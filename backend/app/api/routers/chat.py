import json
import logging
from datetime import datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, get_db_session
from app.core.errors import raise_resource_forbidden
from app.models import ChatMessageRecord, MatchDimensionScore, MatchResult, PathRecommendation, Student, StudentProfile, UploadedFile, User
from app.schemas.chat import ChatRequest, ChatResponse, GreetingResponse
from app.services.bootstrap import get_user_llm_provider

logger = logging.getLogger(__name__)

router = APIRouter()


def _format_profile_score(value: float | int | None) -> str:
    if value is None:
        return ""
    score = float(value)
    if 0 <= score <= 1:
        return f"{score * 100:.0f}%"
    return f"{score:.0f}分"


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
        .limit(2)
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
            if text:
                entry_lines.append(text[:600])
            if structured:
                entry_lines.append(json.dumps(structured, ensure_ascii=False)[:600])
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
    db: Session = Depends(get_db_session),
) -> ChatResponse:
    user_ctx = _build_user_context(db, current_user.id)

    if user_ctx:
        system_prompt = (
            "你是 CareerPilot 的职业规划助手。请用中文回答。\n\n"
            "## 核心原则：证据优先\n"
            "- 必须优先引用下方用户真实数据（简历、画像、匹配结果、路径建议）来回答问题\n"
            "- 不要凭空编造或使用通用模板输出完整的职业规划报告\n"
            "- 如果用户询问的数据尚未生成（如匹配分析、路径规划），如实告知用户需要先完成对应分析\n\n"
            "## 回答格式\n"
            "- 使用 Markdown 标题和要点列表，保持简洁\n"
            "- 除非用户明确要求完整报告，否则控制在 800 字以内\n"
            "- 不要输出无关铺垫\n\n"
            f"{user_ctx}"
        )
    else:
        system_prompt = (
            "你是 CareerPilot 的职业规划助手。请用中文回答。\n\n"
            "当前用户尚未上传简历或完成分析，请引导用户先上传简历并完成职业分析流程。\n"
            "不要输出完整的通用职业规划模板。使用 Markdown 列表格式简洁回复。"
        )

    provider = get_user_llm_provider(None, current_user.id)
    try:
        reply = provider._chat(system_prompt, payload.message)

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

        return ChatResponse(reply=reply)
    except ValueError as exc:
        return ChatResponse(reply=f"API 认证失败：{exc}。请联系管理员检查系统 API 配置。")
    except ConnectionError:
        return ChatResponse(reply="网络连接失败，无法连接到 AI 服务，请检查网络后重试。")
    except TimeoutError:
        return ChatResponse(reply="请求超时，AI 服务响应较慢，请稍后再试。")
    except Exception as exc:
        logger.warning("Chat failed for user %s: %s", current_user.id, exc)
        return ChatResponse(reply=f"AI 模型调用失败：{exc}。请稍后再试。")


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
