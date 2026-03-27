from app.services.reference import load_job_profile_templates


def test_job_profile_template_coverage():
    templates = load_job_profile_templates()
    assert len(templates) >= 10
    for template in templates:
        assert template["skills"]
        assert template["certificates"]
        assert "创新能力" in template["explanations"]

