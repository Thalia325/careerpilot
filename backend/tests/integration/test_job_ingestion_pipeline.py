def test_job_import_profile_graph_pipeline(client):
    payload = {
        "rows": [
            {
                "title": "前端开发工程师",
                "location": "西安",
                "salary_range": "10-15K",
                "company_name": "集成测试企业",
                "industry": "教育科技",
                "company_size": "500-999人",
                "ownership_type": "民营",
                "job_code": "J-FE-TEST-001",
                "description": "负责前端开发与交互实现，需要 React 和 TypeScript",
                "company_intro": "集成测试企业简介"
            }
        ]
    }
    import_response = client.post("/api/v1/jobs/import", json=payload)
    assert import_response.status_code == 200
    graph_response = client.get("/api/v1/graph/jobs/J-FE-TEST-001")
    assert graph_response.status_code == 200
    graph_data = graph_response.json()
    assert graph_data["job_code"] == "J-FE-TEST-001"
    assert graph_data["required_skills"]

