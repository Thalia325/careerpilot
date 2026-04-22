from app.api.deps import create_access_token
from app.models import KnowledgeDocument, Student, User
from app.services.auth_service import hash_password


def _make_student(db, username: str, full_name: str = "知识库学生"):
    user = User(
        username=username,
        password_hash=hash_password("test123"),
        role="student",
        full_name=full_name,
        email=f"{username}@test.local",
    )
    db.add(user)
    db.flush()
    student = Student(user_id=user.id, major="软件工程", grade="大三")
    db.add(student)
    db.commit()
    token = create_access_token({"sub": str(user.id)})
    return user, student, {"Authorization": f"Bearer {token}"}


def test_knowledge_search_endpoint_returns_hits(client, db_session):
    _, _, headers = _make_student(db_session, "kb_search_student")
    db_session.add(
        KnowledgeDocument(
            doc_type="job_profile",
            title="数据分析",
            content="数据分析岗位通常要求 SQL、Python、统计学基础和数据清洗能力。",
            source_ref="CC550543720J40931577815",
            embedding_status="indexed",
        )
    )
    db_session.commit()

    resp = client.get("/api/v1/chat/knowledge/search?query=数据分析", headers=headers)
    assert resp.status_code == 200
    payload = resp.json()
    assert payload["query"] == "数据分析"
    assert payload["items"]
    matched = next((item for item in payload["items"] if item["source_ref"] == "CC550543720J40931577815"), None)
    assert matched is not None
    assert "SQL" in matched["snippet"]


def test_chat_response_includes_knowledge_hits_and_source_block(client, db_session):
    _, _, headers = _make_student(db_session, "kb_chat_student")
    db_session.add(
        KnowledgeDocument(
            doc_type="job_profile",
            title="前端开发工程师",
            content="前端开发工程师通常需要 HTML、CSS、JavaScript、React、XState 状态机和工程化能力。",
            source_ref="CC120776610J40817210808",
            embedding_status="indexed",
        )
    )
    db_session.commit()

    resp = client.post("/api/v1/chat", json={"message": "前端开发工程师"}, headers=headers)
    assert resp.status_code == 200
    payload = resp.json()
    assert payload["knowledge_hits"]
    assert "参考知识库" in payload["reply"]
    assert payload["knowledge_hits"][0]["source_ref"]
