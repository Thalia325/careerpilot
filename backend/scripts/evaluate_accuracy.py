from __future__ import annotations

import argparse
import json
import statistics
import sys
from pathlib import Path
from typing import Any

CURRENT_DIR = Path(__file__).resolve().parent
BACKEND_DIR = CURRENT_DIR.parent
PROJECT_DIR = BACKEND_DIR.parent

if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Evaluate A13 accuracy metrics with labeled cases.")
    parser.add_argument(
        "--cases",
        default=str(PROJECT_DIR / "data" / "evaluation_cases.sample.json"),
        help="Path to labeled evaluation cases JSON.",
    )
    parser.add_argument(
        "--report",
        default=str(PROJECT_DIR / "exports" / "accuracy_report.json"),
        help="Path to output JSON report.",
    )
    return parser.parse_args()


def _normalize_items(items: list[str] | None) -> list[str]:
    if not items:
        return []
    ordered: list[str] = []
    seen: set[str] = set()
    for item in items:
        text = str(item or "").strip()
        key = text.lower()
        if not text or key in seen:
            continue
        ordered.append(text)
        seen.add(key)
    return ordered


def _contains_any(candidates: list[str], targets: list[str]) -> bool:
    candidate_keys = {item.lower() for item in _normalize_items(candidates)}
    return any(target.lower() in candidate_keys for target in _normalize_items(targets))


def _evaluate_skill_case(case: dict[str, Any]) -> dict[str, Any]:
    student = case.get("student", {})
    job = case.get("job", {})
    system = case.get("system_result", {})

    required_skills = _normalize_items(job.get("required_skills"))
    student_skills = _normalize_items(student.get("skills"))
    expected_matched = _normalize_items(case.get("expected_matched_skills"))
    if not expected_matched:
        expected_matched = [skill for skill in required_skills if _contains_any(student_skills, [skill])]
    system_matched = _normalize_items(system.get("matched_skills")) or expected_matched

    expected_keys = {item.lower() for item in expected_matched}
    predicted_keys = {item.lower() for item in system_matched}
    required_keys = [item.lower() for item in required_skills]

    total = max(len(required_keys), 1)
    correct = sum((skill in expected_keys) == (skill in predicted_keys) for skill in required_keys)
    accuracy = round(correct / total * 100, 2)

    return {
        "student_name": student.get("name") or "未命名学生",
        "job_title": job.get("title") or "未命名岗位",
        "required_skills": required_skills,
        "expected_matched_skills": expected_matched,
        "system_matched_skills": system_matched,
        "skill_accuracy": accuracy,
        "passed": accuracy >= 80,
    }


def _evaluate_key_info_case(case: dict[str, Any]) -> dict[str, Any]:
    student = case.get("student", {})
    job = case.get("job", {})

    required_education = str(job.get("education") or "").strip()
    allowed_majors = _normalize_items(job.get("majors"))
    required_certificates = _normalize_items(job.get("certificates"))

    student_education = str(student.get("education") or "").strip()
    student_major = str(student.get("major") or "").strip()
    student_certificates = _normalize_items(student.get("certificates"))

    education_ok = not required_education or student_education == required_education
    major_ok = not allowed_majors or _contains_any([student_major], allowed_majors)
    certificate_ok = not required_certificates or all(
        _contains_any(student_certificates, [certificate]) for certificate in required_certificates
    )
    passed = education_ok and major_ok and certificate_ok

    return {
        "student_name": student.get("name") or "未命名学生",
        "job_title": job.get("title") or "未命名岗位",
        "education_ok": education_ok,
        "major_ok": major_ok,
        "certificate_ok": certificate_ok,
        "passed": passed,
    }


def _load_cases_payload(cases_path: Path) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    payload = json.loads(cases_path.read_text(encoding="utf-8"))
    cases = payload.get("cases", payload if isinstance(payload, list) else [])
    if not isinstance(cases, list) or not cases:
        raise ValueError("Evaluation cases JSON must contain a non-empty 'cases' list.")
    meta = payload.get("meta", {}) if isinstance(payload, dict) else {}
    return cases, meta if isinstance(meta, dict) else {}


def _build_readiness(meta: dict[str, Any], cases_path: Path, case_count: int) -> dict[str, Any]:
    is_sample = "sample" in cases_path.name.lower()
    is_template = "template" in cases_path.name.lower()
    claimed_source = str(meta.get("dataset_type") or "").strip().lower()
    uses_real_team_cases = claimed_source in {"team_labeled", "real_labeled", "competition_ready"}
    minimum_ready = case_count >= 10

    blockers: list[str] = []
    if is_sample:
        blockers.append("当前仍在使用示例样本文件，正式提交前应替换为团队真实标注样本。")
    if is_template:
        blockers.append("当前使用的是模板文件，需先补齐学生、岗位、系统输出和人工标注内容。")
    if not uses_real_team_cases:
        blockers.append("cases 文件的 meta.dataset_type 尚未标记为 team_labeled。")
    if not minimum_ready:
        blockers.append("样本数量不足 10 条，不满足关键字段准确率抽测口径。")

    return {
        "dataset_type": meta.get("dataset_type") or "unspecified",
        "is_sample_file": is_sample,
        "is_template_file": is_template,
        "case_count_ready": minimum_ready,
        "competition_ready": not blockers,
        "blockers": blockers,
    }


def main() -> None:
    args = parse_args()
    cases_path = Path(args.cases)
    report_path = Path(args.report)

    if not cases_path.exists():
        raise FileNotFoundError(f"Cases file not found: {cases_path}")

    cases, meta = _load_cases_payload(cases_path)

    skill_cases = [_evaluate_skill_case(case) for case in cases]
    key_info_cases = [_evaluate_key_info_case(case) for case in cases]

    skill_accuracy = round(statistics.mean(item["skill_accuracy"] for item in skill_cases), 2)
    key_info_pass_count = sum(1 for item in key_info_cases if item["passed"])
    key_info_accuracy = round(key_info_pass_count / len(key_info_cases) * 100, 2)
    readiness = _build_readiness(meta, cases_path, len(cases))

    report = {
        "meta": {
            "cases_file": str(cases_path),
            "case_count": len(cases),
            "dataset_name": meta.get("dataset_name") or cases_path.stem,
            "dataset_type": readiness["dataset_type"],
            "enterprise_rules": {
                "skill_accuracy_threshold": 80,
                "key_info_accuracy_threshold": 90,
                "skill_sampling_note": "建议至少抽取 3 名学生样本，用于核验关键技能匹配准确率。",
                "key_info_sampling_note": "建议至少抽取 10 名匹配成功学生样本，用于核验学历、专业、证书三项关键信息。",
            },
            "competition_readiness": readiness,
        },
        "summary": {
            "skill_accuracy": skill_accuracy,
            "skill_passed": skill_accuracy >= 80,
            "key_info_accuracy": key_info_accuracy,
            "key_info_passed": key_info_accuracy >= 90,
            "overall_passed": skill_accuracy >= 80 and key_info_accuracy >= 90,
        },
        "skill_cases": skill_cases,
        "key_info_cases": key_info_cases,
    }

    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")

    print("CareerPilot A13 准确率评估")
    print(f"- 样本数: {len(cases)}")
    print(f"- 关键技能匹配准确率: {skill_accuracy}%")
    print(f"- 关键信息合规率: {key_info_accuracy}%")
    print(f"- 指标结论: {'通过' if report['summary']['overall_passed'] else '未通过'}")
    print(f"- 参赛就绪: {'是' if readiness['competition_ready'] else '否'}")
    if readiness["blockers"]:
        print("- 当前阻塞:")
        for blocker in readiness["blockers"]:
            print(f"  - {blocker}")
    print(f"- 报告路径: {report_path}")


if __name__ == "__main__":
    main()
