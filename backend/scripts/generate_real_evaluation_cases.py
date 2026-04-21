from __future__ import annotations

import argparse
import json
import re
import sqlite3
from collections import Counter
from pathlib import Path
from typing import Any

CURRENT_DIR = Path(__file__).resolve().parent
BACKEND_DIR = CURRENT_DIR.parent
PROJECT_DIR = BACKEND_DIR.parent


SKILL_PATTERNS: dict[str, tuple[str, ...]] = {
    "Python": ("python",),
    "Java": ("java",),
    "JavaScript": ("javascript", " js "),
    "TypeScript": ("typescript",),
    "React": ("react",),
    "Vue": ("vue", "vue.js"),
    "Next.js": ("next.js", "nextjs"),
    "Node.js": ("node.js", "nodejs"),
    "Spring Boot": ("spring boot", "springboot"),
    "FastAPI": ("fastapi",),
    "SQL": ("sql",),
    "MySQL": ("mysql",),
    "PostgreSQL": ("postgresql", "postgres"),
    "Oracle": ("oracle",),
    "Redis": ("redis",),
    "Linux": ("linux",),
    "Docker": ("docker",),
    "Kubernetes": ("kubernetes", "k8s"),
    "C语言": ("c语言",),
    "C++": ("c++",),
    "Go": ("golang", " go ", "go开发"),
    "HTML": ("html",),
    "CSS": ("css",),
    "Excel": ("excel",),
    "ECharts": ("echarts",),
    "PyTorch": ("pytorch",),
    "TensorFlow": ("tensorflow",),
    "NLP": ("nlp", "自然语言处理"),
    "计算机视觉": ("计算机视觉", "cv视觉"),
    "机器学习": ("机器学习", "machine learning"),
    "深度学习": ("深度学习", "deep learning"),
    "数据分析": ("数据分析", "商业分析", "bi"),
    "数据清洗": ("数据清洗",),
    "数据可视化": ("数据可视化", "可视化"),
    "自动化测试": ("自动化测试",),
    "测试用例设计": ("测试用例设计",),
    "Postman": ("postman",),
    "Selenium": ("selenium",),
    "Shell": ("shell",),
    "TCP/IP": ("tcp/ip", "tcpip"),
    "Wireshark": ("wireshark",),
    "Zabbix": ("zabbix",),
    "Ansible": ("ansible",),
    "Terraform": ("terraform",),
    "网络安全": ("网络安全", "信息安全"),
    "ERP": ("erp", "金蝶", "sap"),
    "CRM": ("crm",),
    "GIS": ("gis", "arcgis", "cass"),
}

MAJOR_KEYWORDS = (
    "计算机科学与技术",
    "软件工程",
    "数据科学与大数据技术",
    "人工智能",
    "网络工程",
    "信息安全",
    "通信工程",
    "电子信息工程",
    "自动化",
    "电气工程",
    "地理信息科学",
    "测绘工程",
    "金融工程",
)

CERTIFICATE_KEYWORDS = (
    "英语四级",
    "英语六级",
    "CET-4",
    "CET-6",
    "计算机二级",
    "PMP",
    "HCIA",
    "HCIP",
    "软考",
    "数据库系统工程师",
    "网络工程师",
)

TRACK_RULES: dict[str, dict[str, tuple[str, ...]]] = {
    "frontend": {
        "resume": ("前端", "javascript", "typescript", "react", "vue", "html", "css", "小程序"),
        "job": ("前端", "web前端", "javascript", "react", "vue", "小程序", "h5"),
    },
    "backend": {
        "resume": ("后端", "java", "spring boot", "go", "mysql", "sql", "fastapi", "接口"),
        "job": ("后端", "java", "服务端", "spring", "golang", "go开发", "fastapi", "开发工程师"),
    },
    "data": {
        "resume": ("数据分析", "数据处理", "excel", "echarts", "sql", "数据清洗"),
        "job": ("数据分析", "数据处理", "bi", "商业分析", "报表"),
    },
    "algorithm": {
        "resume": ("算法", "ai", "人工智能", "机器学习", "深度学习", "pytorch", "tensorflow", "nlp"),
        "job": ("算法", "ai", "人工智能", "机器学习", "aigc", "nlp", "视觉"),
    },
    "testing": {
        "resume": ("测试", "postman", "自动化测试", "测试用例"),
        "job": ("测试", "qa", "软件测试", "测试工程师"),
    },
    "ops": {
        "resume": ("运维", "linux", "docker", "kubernetes", "zabbix", "ansible", "terraform", "网络"),
        "job": ("运维", "noc", "网络管理员", "网络运维", "devops"),
    },
    "implementation": {
        "resume": ("实施", "erp", "crm", "需求", "客户现场"),
        "job": ("实施", "erp", "顾问", "项目交付", "客户培训"),
    },
}

TRACK_PRIORITY = ("frontend", "backend", "data", "algorithm", "testing", "ops", "implementation")

TRACK_SKILLS: dict[str, tuple[str, ...]] = {
    "frontend": ("JavaScript", "TypeScript", "React", "Vue", "Next.js", "Node.js", "HTML", "CSS", "ECharts"),
    "backend": ("Python", "Java", "Go", "Spring Boot", "FastAPI", "SQL", "MySQL", "PostgreSQL", "Redis", "Linux", "Docker"),
    "data": ("Python", "SQL", "MySQL", "PostgreSQL", "Excel", "ECharts", "机器学习", "数据分析", "数据清洗", "数据可视化"),
    "algorithm": ("Python", "SQL", "PyTorch", "TensorFlow", "机器学习", "深度学习", "NLP", "计算机视觉"),
    "testing": ("Python", "Java", "SQL", "Linux", "自动化测试", "测试用例设计", "Postman", "Selenium"),
    "ops": ("Python", "Linux", "Docker", "Kubernetes", "Shell", "TCP/IP", "Wireshark", "Zabbix", "Ansible", "Terraform"),
    "implementation": ("Python", "Java", "SQL", "MySQL", "Oracle", "Excel", "数据分析", "ERP", "CRM"),
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Generate draft evaluation cases from real resumes and real job postings.")
    parser.add_argument(
        "--db",
        default=str(BACKEND_DIR / "careerpilot.db"),
        help="Path to SQLite database.",
    )
    parser.add_argument(
        "--output",
        default=str(PROJECT_DIR / "data" / "evaluation_cases.real.json"),
        help="Path to output JSON file.",
    )
    parser.add_argument(
        "--count",
        type=int,
        default=10,
        help="Number of resume-job pairs to export.",
    )
    parser.add_argument(
        "--max-per-resume",
        type=int,
        default=5,
        help="Maximum pairs generated for the same resume.",
    )
    return parser.parse_args()


def _json_load(value: Any) -> Any:
    if isinstance(value, (list, dict)):
        return value
    if value in (None, "", "{}"):
        return {}
    try:
        return json.loads(value)
    except json.JSONDecodeError:
        return {}


def _clean_text(value: Any) -> str:
    text = str(value or "")
    text = re.sub(r"<br\s*/?>", "\n", text, flags=re.IGNORECASE)
    text = re.sub(r"<[^>]+>", " ", text)
    text = text.replace("&nbsp;", " ")
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def _normalize_text(value: Any) -> str:
    return re.sub(r"\s+", "", _clean_text(value).lower())


def _extract_first(text: str, patterns: tuple[str, ...]) -> bool:
    normalized = _normalize_text(text)
    return any(_normalize_text(pattern) in normalized for pattern in patterns)


def _extract_skills(text: str) -> list[str]:
    normalized = f" {_normalize_text(text)} "
    matched: list[str] = []
    for skill, patterns in SKILL_PATTERNS.items():
        if any(f" {_normalize_text(pattern)} " in normalized or _normalize_text(pattern) in normalized for pattern in patterns):
            matched.append(skill)
    return matched


def _extract_education(text: str, default: str = "") -> str:
    content = _clean_text(text)
    for keyword in ("博士", "硕士", "本科", "大专"):
        if keyword in content:
            return keyword
    return default


def _extract_majors(text: str) -> list[str]:
    content = _clean_text(text)
    return [major for major in MAJOR_KEYWORDS if major in content]


def _extract_certificates(text: str) -> list[str]:
    content = _clean_text(text)
    return [item for item in CERTIFICATE_KEYWORDS if item in content]


def _seniority_years(text: str) -> int:
    content = _clean_text(text)
    values = [int(item) for item in re.findall(r"(\d+)\s*年", content)]
    return max(values) if values else 0


def _infer_tracks(text: str, field: str) -> list[str]:
    matched: list[str] = []
    for track in TRACK_PRIORITY:
        patterns = TRACK_RULES[track][field]
        if _extract_first(text, patterns):
            matched.append(track)
    return matched


def _merge_unique(items: list[str]) -> list[str]:
    result: list[str] = []
    seen: set[str] = set()
    for item in items:
        key = _normalize_text(item)
        if not key or key in seen:
            continue
        result.append(item)
        seen.add(key)
    return result


def _filter_skills_by_track(skills: list[str], tracks: list[str]) -> list[str]:
    if not tracks:
        return []
    allowed: set[str] = set()
    for track in tracks:
        allowed.update(TRACK_SKILLS.get(track, ()))
    filtered = [skill for skill in skills if skill in allowed]
    return _merge_unique(filtered)[:7]


def load_resume_cases(conn: sqlite3.Connection) -> list[dict[str, Any]]:
    query = """
    select
        r.student_id,
        u.full_name,
        uf.file_name,
        r.parsed_json,
        uf.meta_json
    from resumes r
    join students s on s.id = r.student_id
    join users u on u.id = s.user_id
    join uploaded_files uf on uf.id = r.file_id
    where r.parsed_json != '{}'
    order by r.student_id, uf.id
    """
    rows = conn.execute(query).fetchall()
    cases: list[dict[str, Any]] = []
    seen_payloads: set[str] = set()

    for row in rows:
        parsed = _json_load(row["parsed_json"])
        meta = _json_load(row["meta_json"])
        raw_text = _clean_text((meta.get("ocr") or {}).get("raw_text", ""))
        dedupe_key = json.dumps(parsed, ensure_ascii=False, sort_keys=True)
        if dedupe_key in seen_payloads:
            continue
        seen_payloads.add(dedupe_key)

        resume_text = " ".join(
            [
                row["full_name"] or "",
                parsed.get("name") or "",
                parsed.get("school") or "",
                parsed.get("major") or "",
                parsed.get("target_job") or "",
                " ".join(parsed.get("skills") or []),
                " ".join(parsed.get("projects") or []),
                " ".join(parsed.get("internships") or []),
                raw_text,
            ]
        )
        extracted_resume_skills = _merge_unique(_extract_skills(resume_text) + list(parsed.get("skills") or []))
        tracks = _infer_tracks(resume_text, "resume")

        if len(extracted_resume_skills) < 3:
            continue

        cases.append(
            {
                "student_id": row["student_id"],
                "full_name": row["full_name"],
                "file_name": row["file_name"],
                "parsed": parsed,
                "raw_text": raw_text,
                "education": _extract_education(raw_text or parsed.get("major") or "", default=""),
                "skills": extracted_resume_skills,
                "tracks": tracks,
            }
        )
    return cases


def load_job_cases(conn: sqlite3.Connection) -> list[dict[str, Any]]:
    rows = conn.execute(
        """
        select job_code, title, company_name, location, description
        from job_postings
        """
    ).fetchall()
    jobs: list[dict[str, Any]] = []

    for row in rows:
        description = _clean_text(row["description"])
        title = _clean_text(row["title"])
        combined = f"{title} {description}"
        title_tracks = _infer_tracks(title, "job")
        if not title_tracks:
            continue
        tracks = title_tracks
        required_skills = _filter_skills_by_track(_extract_skills(combined), tracks)
        if len(required_skills) < 2:
            continue
        if _seniority_years(description) > 2:
            continue

        jobs.append(
            {
                "job_code": row["job_code"],
                "title": title,
                "company_name": row["company_name"],
                "location": row["location"],
                "description": description,
                "education": _extract_education(description, default=""),
                "majors": _extract_majors(description),
                "certificates": _extract_certificates(description),
                "required_skills": required_skills,
                "title_tracks": title_tracks,
                "tracks": tracks,
            }
        )
    return jobs


def _resume_skill_keys(skills: list[str]) -> set[str]:
    return {_normalize_text(skill) for skill in skills if _normalize_text(skill)}


def _matched_required_skills(required_skills: list[str], resume_skills: list[str], extra_text: str = "") -> list[str]:
    resume_keys = _resume_skill_keys(resume_skills)
    extra_keys = _resume_skill_keys(_extract_skills(extra_text))
    matched: list[str] = []
    for skill in required_skills:
        key = _normalize_text(skill)
        if key in resume_keys or key in extra_keys:
            matched.append(skill)
    return matched


def _target_job_bonus(target_job: str, title: str) -> int:
    target = _clean_text(target_job)
    title_text = _clean_text(title)
    if not target:
        return 0
    for token in re.split(r"[、,/，\s]+", target):
        token = token.strip()
        if token and token in title_text:
            return 20
    return 0


def build_candidate_pairs(resumes: list[dict[str, Any]], jobs: list[dict[str, Any]]) -> list[dict[str, Any]]:
    candidates: list[dict[str, Any]] = []
    for resume in resumes:
        parsed = resume["parsed"]
        resume_text = " ".join(
            [
                parsed.get("target_job") or "",
                " ".join(parsed.get("skills") or []),
                " ".join(parsed.get("projects") or []),
                " ".join(parsed.get("internships") or []),
                resume["raw_text"],
            ]
        )
        for job in jobs:
            expected = _matched_required_skills(job["required_skills"], resume["skills"], resume_text)
            system = _matched_required_skills(job["required_skills"], list(parsed.get("skills") or []))
            if len(expected) < 2:
                continue

            shared_tracks = set(resume["tracks"]).intersection(job["title_tracks"] or job["tracks"])
            if not shared_tracks:
                continue
            score = len(expected) * 25 + len(shared_tracks) * 20 + _target_job_bonus(parsed.get("target_job", ""), job["title"])

            if score < 50:
                continue

            candidates.append(
                {
                    "resume": resume,
                    "job": job,
                    "score": score,
                    "expected_matched_skills": expected,
                    "system_matched_skills": system or expected,
                    "shared_tracks": sorted(shared_tracks),
                }
            )
    candidates.sort(
        key=lambda item: (
            item["score"],
            len(item["expected_matched_skills"]),
            len(item["system_matched_skills"]),
        ),
        reverse=True,
    )
    return candidates


def select_pairs(
    candidates: list[dict[str, Any]],
    count: int,
    max_per_resume: int,
) -> list[dict[str, Any]]:
    selected: list[dict[str, Any]] = []
    resume_counter: Counter[int] = Counter()
    title_counter: Counter[str] = Counter()
    seen_pairs: set[tuple[int, str]] = set()

    for candidate in candidates:
        resume_id = candidate["resume"]["student_id"]
        job_code = candidate["job"]["job_code"]
        title = candidate["job"]["title"]
        pair_key = (resume_id, job_code)
        if pair_key in seen_pairs:
            continue
        if resume_counter[resume_id] >= max_per_resume:
            continue
        if title_counter[title] >= 2:
            continue

        selected.append(candidate)
        seen_pairs.add(pair_key)
        resume_counter[resume_id] += 1
        title_counter[title] += 1
        if len(selected) >= count:
            break
    return selected


def build_case(candidate: dict[str, Any]) -> dict[str, Any]:
    resume = candidate["resume"]
    parsed = resume["parsed"]
    job = candidate["job"]
    projects = [str(item).strip() for item in parsed.get("projects") or [] if str(item).strip()]
    internships = [str(item).strip() for item in parsed.get("internships") or [] if str(item).strip()]

    return {
        "student": {
            "name": parsed.get("name") or resume["full_name"] or "未知学生",
            "education": resume["education"],
            "major": parsed.get("major") or "",
            "skills": resume["skills"],
            "certificates": list(parsed.get("certificates") or []),
        },
        "job": {
            "title": job["title"],
            "education": job["education"],
            "majors": job["majors"],
            "required_skills": job["required_skills"],
            "certificates": job["certificates"],
        },
        "system_result": {
            "matched_skills": candidate["system_matched_skills"],
        },
        "expected_matched_skills": candidate["expected_matched_skills"],
        "evidence": {
            "resume_file": resume["file_name"],
            "student_id": resume["student_id"],
            "job_code": job["job_code"],
            "company_name": job["company_name"],
            "location": job["location"],
            "resume_tracks": resume["tracks"],
            "job_tracks": job["tracks"],
            "shared_tracks": candidate["shared_tracks"],
            "target_job": parsed.get("target_job") or "",
            "project_samples": projects[:2],
            "internship_samples": internships[:2],
            "labeling_note": "expected_matched_skills 基于简历显式技能与 OCR 文本证据抽取；system_result 仅基于结构化技能字段命中，便于后续人工复核。",
        },
    }


def main() -> None:
    args = parse_args()
    db_path = Path(args.db)
    output_path = Path(args.output)

    if not db_path.exists():
        raise FileNotFoundError(f"Database not found: {db_path}")

    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    try:
        resumes = load_resume_cases(conn)
        jobs = load_job_cases(conn)
        candidates = build_candidate_pairs(resumes, jobs)
        selected = select_pairs(candidates, count=args.count, max_per_resume=args.max_per_resume)
    finally:
        conn.close()

    payload = {
        "meta": {
            "dataset_name": "CareerPilot real resume-job draft cases",
            "dataset_type": "real_auto_labeled_draft",
            "owner": "Codex",
            "note": "样本来自库内真实/准真实简历 OCR 与真实岗位 JD 自动配对，expected_matched_skills 为待人工抽查的草稿标签。",
            "resume_case_count": len(resumes),
            "job_case_count": len(jobs),
            "candidate_pair_count": len(candidates),
            "selected_pair_count": len(selected),
        },
        "cases": [build_case(item) for item in selected],
    }

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")

    print(f"Generated draft cases: {len(selected)}")
    print(f"Output: {output_path}")


if __name__ == "__main__":
    main()
