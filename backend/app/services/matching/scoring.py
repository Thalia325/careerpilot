from __future__ import annotations


def clamp_score(value: float) -> float:
    return max(0.0, min(100.0, round(value, 2)))


def score_basic_requirements(student_profile: dict, job_profile: dict) -> tuple[float, dict]:
    student_certificates = set(student_profile["certificates"])
    job_certificates = set(job_profile["certificate_requirements"])
    cert_ratio = len(student_certificates.intersection(job_certificates)) / max(1, len(job_certificates))
    internship_score = student_profile["capability_scores"].get("internship", 0)
    completeness = student_profile["completeness_score"]
    score = cert_ratio * 55 + internship_score * 0.25 + completeness * 0.2
    evidence = {
        "matched_certificates": sorted(student_certificates.intersection(job_certificates)),
        "missing_certificates": sorted(job_certificates.difference(student_certificates)),
    }
    return clamp_score(score), evidence


def score_professional_skills(student_profile: dict, job_profile: dict) -> tuple[float, dict]:
    student_skills = set(student_profile["skills"])
    required = set(job_profile["skill_requirements"])
    overlap = student_skills.intersection(required)
    coverage = len(overlap) / max(1, len(required))
    score = coverage * 100
    evidence = {"matched_skills": sorted(overlap), "missing_skills": sorted(required.difference(student_skills))}
    return clamp_score(score), evidence


def score_professional_literacy(student_profile: dict, job_profile: dict) -> tuple[float, dict]:
    student_caps = student_profile["capability_scores"]
    job_caps = job_profile["capability_scores"]
    communication_gap = 100 - abs(student_caps.get("communication", 0) - job_caps.get("communication", 0))
    resilience_gap = 100 - abs(student_caps.get("resilience", 0) - job_caps.get("resilience", 0))
    internship_gap = 100 - abs(student_caps.get("internship", 0) - job_caps.get("internship", 0))
    score = (communication_gap + resilience_gap + internship_gap) / 3
    evidence = {
        "communication": student_caps.get("communication", 0),
        "resilience": student_caps.get("resilience", 0),
        "internship": student_caps.get("internship", 0),
    }
    return clamp_score(score), evidence


def score_development_potential(student_profile: dict, job_profile: dict) -> tuple[float, dict]:
    student_caps = student_profile["capability_scores"]
    job_caps = job_profile["capability_scores"]
    learning_gap = 100 - abs(student_caps.get("learning", 0) - job_caps.get("learning", 0))
    innovation_gap = 100 - abs(student_caps.get("innovation", 0) - job_caps.get("innovation", 0))
    completeness = student_profile["completeness_score"]
    score = learning_gap * 0.4 + innovation_gap * 0.4 + completeness * 0.2
    evidence = {
        "learning": student_caps.get("learning", 0),
        "innovation": student_caps.get("innovation", 0),
        "completeness": completeness,
    }
    return clamp_score(score), evidence

