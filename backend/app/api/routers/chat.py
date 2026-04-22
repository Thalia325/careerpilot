import asyncio
import json
import logging
import re
from concurrent.futures import ThreadPoolExecutor, TimeoutError as FuturesTimeoutError
from datetime import datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import get_container, get_current_user, get_db_session
from app.core.errors import raise_resource_forbidden
from app.models import ChatMessageRecord, KnowledgeDocument, MatchDimensionScore, MatchResult, PathRecommendation, Student, StudentProfile, UploadedFile, User
from app.schemas.chat import ChatRequest, ChatResponse, GreetingResponse, KnowledgeHit, KnowledgeSearchResponse
from app.services.bootstrap import ServiceContainer, get_user_llm_provider

logger = logging.getLogger(__name__)

router = APIRouter()


def _snippet(text: str, query: str, max_len: int = 180) -> str:
    clean = " ".join((text or "").split())
    if len(clean) <= max_len:
        return clean
    index = clean.lower().find(query.lower())
    if index < 0:
        return clean[: max_len - 1] + "…"
    start = max(0, index - max_len // 3)
    end = min(len(clean), start + max_len)
    snippet = clean[start:end]
    if start > 0:
        snippet = "…" + snippet
    if end < len(clean):
        snippet = snippet + "…"
    return snippet


def _query_terms(query: str) -> list[str]:
    raw = query.strip().lower()
    parts = re.split(r"[\s,，。！？；、/]+", raw)
    unique: list[str] = []

    def add(term: str) -> None:
        normalized = term.strip()
        if len(normalized) < 2:
            return
        if normalized not in unique:
            unique.append(normalized)

    add(raw)
    for item in parts:
        add(item)

    han_chunks = re.findall(r"[\u4e00-\u9fff]{2,}", raw)
    for chunk in han_chunks:
        for size in (2, 3, 4):
            if len(chunk) < size:
                continue
            for index in range(0, min(len(chunk) - size + 1, 8)):
                add(chunk[index:index + size])

    return unique[:20]


def _document_score(title: str, content: str, query: str) -> float:
    haystack_title = (title or "").lower()
    haystack_content = (content or "").lower()
    terms = _query_terms(query)
    score = 0.0
    for term in terms:
        score += haystack_title.count(term) * 3
        score += haystack_content.count(term)
    if query.lower() in haystack_title:
        score += 5
    if query.lower() in haystack_content:
        score += 2
    return score


async def _search_knowledge(
    db: Session,
    container: ServiceContainer,
    query: str,
    top_k: int = 5,
) -> list[KnowledgeHit]:
    seen: set[tuple[str, str]] = set()
    hits: list[KnowledgeHit] = []

    try:
        rag_items = await container.job_import_service.rag_provider.search(query, top_k=top_k)
    except Exception:
        logger.warning("Knowledge provider search failed for query=%s", query, exc_info=True)
        rag_items = []

    for item in rag_items:
        title = str(item.get("title") or "").strip()
        content = str(item.get("content") or "").strip()
        metadata = item.get("metadata") or {}
        source_ref = str(metadata.get("job_code") or item.get("source_ref") or "").strip()
        doc_type = str(metadata.get("doc_type") or item.get("doc_type") or "job_profile").strip()
        key = (title, source_ref)
        if not title or key in seen:
            continue
        seen.add(key)
        hits.append(
            KnowledgeHit(
                title=title,
                snippet=_snippet(content, query),
                doc_type=doc_type,
                source_ref=source_ref,
                score=float(item.get("score")) if item.get("score") is not None else None,
            )
        )

    documents = list(db.scalars(select(KnowledgeDocument)).all())
    ranked_docs = sorted(
        documents,
        key=lambda doc: _document_score(doc.title, doc.content, query),
        reverse=True,
    )
    for doc in ranked_docs:
        if len(hits) >= top_k:
            break
        score = _document_score(doc.title, doc.content, query)
        if score <= 0:
            continue
        key = (doc.title, doc.source_ref or "")
        if key in seen:
            continue
        seen.add(key)
        hits.append(
            KnowledgeHit(
                title=doc.title,
                snippet=_snippet(doc.content, query),
                doc_type=doc.doc_type,
                source_ref=doc.source_ref or "",
                score=score,
            )
        )

    return hits[:top_k]


def _build_chat_fallback_reply(
    message: str,
    knowledge_hits: list[KnowledgeHit],
    has_user_context: bool,
) -> str:
    lines = ["### 当前为快速兜底回答"]
    if knowledge_hits:
        lines.append("以下内容来自知识库检索，可先作为参考：")
        for hit in knowledge_hits[:3]:
            source = f"（{hit.source_ref}）" if hit.source_ref else ""
            lines.append(f"- **{hit.title}**{source}：{hit.snippet}")
        lines.append("你也可以换一种更具体的问法继续追问，比如“这个岗位需要哪些项目经验”。")
        return "\n".join(lines)
    if has_user_context:
        lines.append("我已经拿到你的简历/画像上下文，但这次模型响应超时。")
        lines.append(f"- 你刚刚的问题是：{message}")
        lines.append("- 建议稍后重试，或把问题缩小到某个岗位、技能或项目经历，我会更快给出回答。")
        return "\n".join(lines)
    lines.append("当前没有检索到可直接引用的知识库内容，且模型响应超时。")
    lines.append("- 建议先上传简历，或把问题改成具体岗位名称、技能名、行业方向再试。")
    return "\n".join(lines)


def _format_profile_score(value: float | int | None) -> str:
    if value is None:
        return ""
    score = float(value)
    if 0 <= score <= 1:
        return f"{score * 100:.0f}%"
    return f"{score:.0f}分"


def _compact_ocr_structured(structured: dict) -> dict[str, object]:
    if not isinstance(structured, dict):
        return {}
    compact: dict[str, object] = {}
    for key in ("name", "school", "major", "grade", "graduation_year", "target_job", "gpa"):
        value = structured.get(key)
        if value:
            compact[key] = value
    for key, limit in (
        ("skills", 12),
        ("certificates", 8),
        ("projects", 5),
        ("internships", 5),
        ("competitions", 5),
    ):
        value = structured.get(key)
        if isinstance(value, list) and value:
            compact[key] = value[:limit]
    if structured.get("self_evaluation"):
        compact["self_evaluation"] = str(structured["self_evaluation"])[:180]
    return compact


def _chat_options_for_message(message: str, has_user_context: bool) -> dict[str, object]:
    text = (message or "").strip()
    resume_keywords = ("简历", "项目", "经历", "实习", "技能", "证书", "画像", "匹配", "报告")
    is_resume_question = any(keyword in text for keyword in resume_keywords)
    if has_user_context or is_resume_question:
        return {
            "enable_web_search": False,
            "max_completion_tokens": 2048,
            "timeout_seconds": 90.0,
            "executor_timeout_seconds": 95,
        }
    return {
        "enable_web_search": True,
        "max_completion_tokens": 2048,
        "timeout_seconds": 45.0,
        "executor_timeout_seconds": 50,
    }


def _build_user_context(db: Session, user_id: int) -> str:
    parts: list[str] = []

    user = db.scalar(select(User).where(User.id == user_id))
    student = db.scalar(select(Student).where(Student.user_id == user_id))
    if student:
        info_lines: list[str] = []
        if user and user.full_name:
            info_lines.append(f"姓名/昵称：{user.full_name}")
        if student.major:
            info_lines.append(f"专业：{student.major}")
        if student.grade:
            info_lines.append(f"年级：{student.grade}")
        if student.career_goal:
            info_lines.append(f"职业目标：{student.career_goal}")
        if info_lines:
            parts.append("【学生基本信息】\n" + "\n".join(info_lines))

        profile = db.scalar(
            select(StudentProfile).where(StudentProfile.student_id == student.id)
        )
        if profile:
            profile_lines: list[str] = []
            if profile.source_summary:
                profile_lines.append(f"综合评价：{profile.source_summary}")
            if profile.skills_json:
                skills = profile.skills_json if isinstance(profile.skills_json, list) else []
                if skills:
                    profile_lines.append(f"技能标签：{', '.join(str(s) for s in skills[:20])}")
            if profile.certificates_json:
                certs = profile.certificates_json if isinstance(profile.certificates_json, list) else []
                if certs:
                    profile_lines.append(f"证书：{', '.join(str(c) for c in certs[:10])}")
            if profile.capability_scores and isinstance(profile.capability_scores, dict):
                scores_text = ", ".join(
                    f"{k}: {v}" for k, v in list(profile.capability_scores.items())[:8]
                )
                if scores_text:
                    profile_lines.append(f"能力评分：{scores_text}")
            if profile.completeness_score:
                profile_lines.append(f"档案完整度：{_format_profile_score(profile.completeness_score)}")
            if profile.competitiveness_score:
                profile_lines.append(f"竞争力评分：{_format_profile_score(profile.competitiveness_score)}")
            if profile_lines:
                parts.append("【学生能力画像】\n" + "\n".join(profile_lines))

        # --- Latest match result ---
        latest_match = db.scalar(
            select(MatchResult)
            .where(MatchResult.student_profile_id == profile.id)
            .order_by(MatchResult.created_at.desc())
            .limit(1)
        ) if profile else None
        if latest_match:
            match_lines: list[str] = []
            match_lines.append(f"匹配总分：{latest_match.total_score}")
            if latest_match.summary:
                match_lines.append(f"匹配摘要：{latest_match.summary}")
            if latest_match.gaps_json:
                gaps = latest_match.gaps_json if isinstance(latest_match.gaps_json, list) else []
                if gaps:
                    gap_items = []
                    for g in gaps[:10]:
                        name = g.get("name", g.get("skill", ""))
                        desc = g.get("description", g.get("detail", ""))
                        score = g.get("score", "")
                        item = name
                        if desc:
                            item += f"：{desc}"
                        if score:
                            item += f"（评分：{score}）"
                        gap_items.append(f"- {item}")
                    match_lines.append("差距项：\n" + "\n".join(gap_items))
            if latest_match.suggestions_json:
                suggestions = latest_match.suggestions_json if isinstance(latest_match.suggestions_json, list) else []
                if suggestions:
                    match_lines.append("改进建议：\n" + "\n".join(f"- {s}" for s in suggestions[:10]))

            # Dimension scores
            dim_scores = db.scalars(
                select(MatchDimensionScore)
                .where(MatchDimensionScore.match_result_id == latest_match.id)
                .order_by(MatchDimensionScore.dimension)
            ).all()
            if dim_scores:
                dim_lines = [f"- **{ds.dimension}**：{ds.score} 分（权重 {ds.weight}）{f'，{ds.reasoning}' if ds.reasoning else ''}" for ds in dim_scores]
                match_lines.append("各维度评分：\n" + "\n".join(dim_lines))

            parts.append("【最近匹配结果】\n" + "\n".join(match_lines))

        # --- Latest path recommendation ---
        latest_path = db.scalar(
            select(PathRecommendation)
            .where(PathRecommendation.student_id == student.id)
            .order_by(PathRecommendation.created_at.desc())
            .limit(1)
        )
        if latest_path:
            path_lines: list[str] = []
            path_lines.append(f"目标岗位：{latest_path.target_job_code}")
            if latest_path.gaps_json:
                path_gaps = latest_path.gaps_json if isinstance(latest_path.gaps_json, list) else []
                if path_gaps:
                    path_lines.append("路径差距项：\n" + "\n".join(f"- {g}" for g in path_gaps[:10]))
            if latest_path.recommendations_json:
                recs = latest_path.recommendations_json if isinstance(latest_path.recommendations_json, list) else []
                if recs:
                    rec_items = []
                    for r in recs[:10]:
                        title = r.get("title", r.get("name", ""))
                        desc = r.get("description", r.get("detail", ""))
                        item = title
                        if desc:
                            item += f"：{desc}"
                        rec_items.append(f"- {item}")
                    path_lines.append("路径建议：\n" + "\n".join(rec_items))
            parts.append("【最近职业路径建议】\n" + "\n".join(path_lines))

    files = db.scalars(
        select(UploadedFile)
        .where(UploadedFile.owner_id == user_id)
        .order_by(UploadedFile.created_at.desc())
        .limit(1)
    ).all()
    if files:
        ocr_parts: list[str] = []
        for f in files:
            meta = f.meta_json or {}
            ocr_text = meta.get("ocr", {})
            if isinstance(ocr_text, dict):
                text = ocr_text.get("raw_text") or ocr_text.get("text", "")
                structured = ocr_text.get("structured_json", {})
            elif isinstance(ocr_text, str):
                text = ocr_text
                structured = {}
            else:
                continue
            if not text and not structured:
                continue
            entry_lines = [f"--- 文件：{f.file_name}（{f.file_type}）---"]
            compact_structured = _compact_ocr_structured(structured if isinstance(structured, dict) else {})
            if compact_structured:
                entry_lines.append("结构化摘要：")
                entry_lines.append(json.dumps(compact_structured, ensure_ascii=False))
            if text:
                entry_lines.append("OCR 摘要：")
                entry_lines.append(text[:240])
            ocr_parts.append("\n".join(entry_lines))
        if ocr_parts:
            parts.append("【用户上传的简历/文件 OCR 解析内容】\n" + "\n\n".join(ocr_parts))

    if not parts:
        return ""

    return (
        "以下是你正在对话的用户的相关背景信息，请在回答时优先引用这些真实数据给出个性化建议。"
        "如果用户询问你尚未掌握的信息（如匹配结果、路径规划），请如实告知尚未完成该分析：\n\n"
        + "\n\n".join(parts)
    )


def _fallback_greeting(db: Session, user_id: int) -> tuple[str, str]:
    """Return a (greeting, subline) tuple based on basic student info, no LLM call."""
    user = db.scalar(select(User).where(User.id == user_id))
    student = db.scalar(select(Student).where(Student.user_id == user_id))
    display_name = (user.full_name or "").strip() if user else ""
    greeting = "你好，想了解什么职业方向？"
    subline = "输入你感兴趣的岗位方向或上传简历，AI 帮你分析"
    if display_name and student and student.career_goal:
        greeting = f"你好，{display_name}同学！来聊聊{student.career_goal}方向？"
        subline = "上传简历或直接提问，AI 帮你深入分析"
    elif display_name:
        greeting = f"你好，{display_name}同学！想了解什么职业方向？"
        subline = "上传简历或直接提问，AI 帮你规划职业路径"
    elif student and student.career_goal:
        greeting = f"你好！来聊聊{student.career_goal}方向？"
        subline = "上传简历或直接提问，AI 帮你深入分析"
    elif student and student.major:
        greeting = "你好，想了解什么职业方向？"
        subline = "上传简历或直接提问，AI 帮你规划职业路径"
    return greeting, subline


@router.get("/greeting", response_model=GreetingResponse)
def greeting(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db_session),
) -> GreetingResponse:
    fallback_greeting, fallback_subline = _fallback_greeting(db, current_user.id)

    try:
        user_ctx = _build_user_context(db, current_user.id)
    except Exception:
        logger.warning("Failed to build user context for greeting, user_id=%s", current_user.id, exc_info=True)
        return GreetingResponse(greeting=fallback_greeting, subline=fallback_subline)

    try:
        recent = db.scalars(
            select(ChatMessageRecord)
            .where(ChatMessageRecord.user_id == current_user.id, ChatMessageRecord.role == "user")
            .order_by(ChatMessageRecord.created_at.desc())
            .limit(10)
        ).all()
        history_lines = [f"- {m.content[:80]}" for m in reversed(recent)] if recent else []
    except Exception:
        history_lines = []

    if not user_ctx and not history_lines:
        return GreetingResponse(greeting=fallback_greeting, subline=fallback_subline)

    context_block = ""
    if user_ctx:
        context_block = f"\n\n用户背景信息：\n{user_ctx}"
    if history_lines:
        context_block += f"\n\n用户最近的聊天话题：\n" + "\n".join(history_lines)

    system_prompt = (
        "你是职航智策（CareerPilot）的职业规划AI助手。"
        "请根据用户的背景信息和历史聊天记录，生成一句个性化、简短亲切的中文问候语，引导用户开始新的职业规划对话。\n"
        "要求：\n"
        "1. 问候语不超过30个字，自然口语化\n"
        "2. 如果称呼用户为“xx同学”，xx必须使用用户姓名/昵称，不能使用专业名称\n"
        "3. 如果用户有明确的职业目标，围绕目标给出引导\n"
        "4. 如果没有明确目标，根据专业或历史话题引导，但不要把专业当作称呼\n"
        "5. 每次问候尽量不同，有新鲜感\n"
        "6. 再生成一句简短的副标题（不超过25字），提示用户可以做什么\n"
        "7. 严格按以下JSON格式返回，不要返回其他内容：\n"
        '{"greeting": "问候语", "subline": "副标题"}'
    )

    try:
        provider = get_user_llm_provider(None, current_user.id)
        raw = provider._chat(system_prompt, context_block or "新用户，暂无背景信息")
        parsed = json.loads(raw.strip().removeprefix("```json").removeprefix("```").removesuffix("```").strip())
        greeting_text = parsed.get("greeting", fallback_greeting)
        subline_text = parsed.get("subline", fallback_subline)
        student = db.scalar(select(Student).where(Student.user_id == current_user.id))
        display_name = (current_user.full_name or "").strip()
        if display_name and student and student.major:
            greeting_text = str(greeting_text).replace(f"{student.major}同学", f"{display_name}同学")
        return GreetingResponse(greeting=greeting_text[:60], subline=subline_text[:50])
    except Exception as exc:
        logger.warning("Greeting generation failed for user %s: %s", current_user.id, exc)
        return GreetingResponse(greeting=fallback_greeting, subline=fallback_subline)


@router.post("", response_model=ChatResponse)
def chat(
    payload: ChatRequest,
    current_user: User = Depends(get_current_user),
    container: ServiceContainer = Depends(get_container),
    db: Session = Depends(get_db_session),
) -> ChatResponse:
    user_ctx = _build_user_context(db, current_user.id)
    try:
        knowledge_hits = asyncio.run(_search_knowledge(db, container, payload.message, top_k=6))
    except Exception:
        logger.warning("Knowledge search failed for user %s", current_user.id, exc_info=True)
        knowledge_hits = []

    knowledge_context = ""
    if knowledge_hits:
        knowledge_lines = []
        for hit in knowledge_hits:
            source = f"（来源：{hit.source_ref}）" if hit.source_ref else ""
            knowledge_lines.append(f"- {hit.title}{source}\n  {hit.snippet}")
        knowledge_context = "\n\n【知识库检索补充】\n" + "\n".join(knowledge_lines)

    if user_ctx:
        system_prompt = (
            "你是 CareerPilot 的职业规划助手。请用中文回答。\n\n"
            "## 核心原则：证据优先\n"
            "- 必须优先引用下方用户真实数据（简历、画像、匹配结果、路径建议）来回答问题\n"
            "- 如提供了知识库检索补充，可将其作为岗位要求、技能建议、职业认知的补充依据\n"
            "- 不要凭空编造或使用通用模板输出完整的职业规划报告\n"
            "- 如果用户询问的数据尚未生成（如匹配分析、路径规划），如实告知用户需要先完成对应分析\n\n"
            "## 回答格式\n"
            "- 使用 Markdown 标题和要点列表，保持简洁\n"
            "- 除非用户明确要求完整报告，否则控制在 800 字以内\n"
            "- 不要输出无关铺垫\n\n"
            f"{user_ctx}{knowledge_context}"
        )
    else:
        system_prompt = (
            "你是 CareerPilot 的职业规划助手。请用中文回答。\n\n"
            "当前用户尚未上传简历或完成分析，请引导用户先上传简历并完成职业分析流程。\n"
            "不要输出完整的通用职业规划模板。使用 Markdown 列表格式简洁回复。"
            f"{knowledge_context}"
        )

    provider = get_user_llm_provider(None, current_user.id)
    chat_options = _chat_options_for_message(payload.message, bool(user_ctx))
    try:
        executor = ThreadPoolExecutor(max_workers=1)
        if hasattr(provider, "_chat_with_options"):
            future = executor.submit(
                provider._chat_with_options,
                system_prompt,
                payload.message,
                enable_web_search=bool(chat_options["enable_web_search"]),
                max_completion_tokens=int(chat_options["max_completion_tokens"]),
                timeout_seconds=float(chat_options["timeout_seconds"]),
            )
        else:
            future = executor.submit(provider._chat, system_prompt, payload.message)
        try:
            reply = future.result(timeout=int(chat_options["executor_timeout_seconds"]))
            executor.shutdown(wait=False, cancel_futures=False)
        except FuturesTimeoutError:
            logger.warning("Chat LLM timeout for user %s, using fallback reply", current_user.id)
            future.cancel()
            executor.shutdown(wait=False, cancel_futures=True)
            reply = _build_chat_fallback_reply(payload.message, knowledge_hits, bool(user_ctx))
        if knowledge_hits:
            source_lines = []
            for hit in knowledge_hits:
                source = f" ({hit.source_ref})" if hit.source_ref else ""
                source_lines.append(f"- {hit.title}{source}")
            reply = f"{reply.rstrip()}\n\n---\n**参考知识库**\n" + "\n".join(source_lines)

        db.add(ChatMessageRecord(
            user_id=current_user.id,
            role="user",
            content=payload.message,
            has_context=bool(user_ctx),
        ))
        db.add(ChatMessageRecord(
            user_id=current_user.id,
            role="assistant",
            content=reply,
            has_context=bool(user_ctx),
        ))
        db.commit()

        return ChatResponse(reply=reply, knowledge_hits=knowledge_hits)
    except ValueError as exc:
        return ChatResponse(reply=f"API 认证失败：{exc}。请联系管理员检查系统 API 配置。", knowledge_hits=knowledge_hits)
    except ConnectionError:
        return ChatResponse(reply=_build_chat_fallback_reply(payload.message, knowledge_hits, bool(user_ctx)), knowledge_hits=knowledge_hits)
    except TimeoutError:
        return ChatResponse(reply=_build_chat_fallback_reply(payload.message, knowledge_hits, bool(user_ctx)), knowledge_hits=knowledge_hits)
    except Exception as exc:
        logger.warning("Chat failed for user %s: %s", current_user.id, exc)
        return ChatResponse(reply=_build_chat_fallback_reply(payload.message, knowledge_hits, bool(user_ctx)), knowledge_hits=knowledge_hits)


@router.get("/knowledge/search", response_model=KnowledgeSearchResponse)
async def search_knowledge(
    query: str = Query(..., min_length=2, max_length=200),
    current_user: User = Depends(get_current_user),
    container: ServiceContainer = Depends(get_container),
    db: Session = Depends(get_db_session),
) -> KnowledgeSearchResponse:
    if current_user.role not in {"student", "teacher", "admin"}:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="无权访问知识库检索")
    items = await _search_knowledge(db, container, query, top_k=8)
    return KnowledgeSearchResponse(query=query, items=items)


@router.get("/history/{message_id}")
def get_chat_history(
    message_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db_session),
):
    """Fetch a specific chat message and its surrounding conversation for history replay.

    Returns messages within a ±5-minute window of the target message,
    scoped to the authenticated user.
    """
    msg = db.get(ChatMessageRecord, message_id)
    if not msg:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="聊天记录不存在")

    # Ownership check: only the message owner can view
    if msg.user_id != current_user.id:
        raise_resource_forbidden()

    # Fetch messages in a ±5-minute window around the target message
    target_time: datetime = msg.created_at
    window_start = target_time - timedelta(minutes=5)
    window_end = target_time + timedelta(minutes=5)

    messages = list(db.scalars(
        select(ChatMessageRecord)
        .where(
            ChatMessageRecord.user_id == current_user.id,
            ChatMessageRecord.created_at >= window_start,
            ChatMessageRecord.created_at <= window_end,
        )
        .order_by(ChatMessageRecord.created_at.asc())
    ).all())

    return {
        "messages": [
            {
                "id": m.id,
                "role": m.role,
                "content": m.content,
                "created_at": m.created_at.isoformat() if m.created_at else "",
                "has_context": m.has_context,
            }
            for m in messages
        ],
        "target_message_id": message_id,
    }
