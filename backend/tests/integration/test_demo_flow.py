from pathlib import Path


def test_resume_to_report_export_flow(client):
    upload_response = client.post(
        "/api/v1/files/upload",
        data={"owner_id": "1", "file_type": "resume"},
        files={
            "upload": (
                "resume.txt",
                "姓名：陈同学\n专业：软件工程\n技能：JavaScript React Next.js Python\n项目：CareerPilot\n实习：前端开发实习\n证书：英语四级".encode("utf-8"),
                "text/plain",
            )
        },
    )
    assert upload_response.status_code == 200
    uploaded_file_id = upload_response.json()["data"]["id"]

    ocr_response = client.post("/api/v1/ocr/parse", json={"uploaded_file_id": uploaded_file_id, "document_type": "resume"})
    assert ocr_response.status_code == 200

    profile_response = client.post(
        "/api/v1/student-profiles/generate",
        json={
            "student_id": 1,
            "uploaded_file_ids": [uploaded_file_id],
            "manual_input": {
                "target_job": "前端开发工程师",
                "skills": ["TypeScript", "HTML"],
                "projects": ["职业规划平台"],
                "internships": ["教育科技公司前端实习"]
            }
        },
    )
    assert profile_response.status_code == 200

    matching_response = client.post("/api/v1/matching/analyze", json={"student_id": 1, "job_code": "J-FE-001"})
    assert matching_response.status_code == 200
    assert matching_response.json()["total_score"] > 0

    report_response = client.post("/api/v1/reports/generate", json={"student_id": 1, "job_code": "J-FE-001"})
    assert report_response.status_code == 200
    report_id = report_response.json()["report_id"]

    export_response = client.post("/api/v1/reports/export", json={"report_id": report_id, "format": "pdf"})
    assert export_response.status_code == 200
    exported_path = export_response.json()["exported"]["path"]
    assert Path(exported_path).exists()

