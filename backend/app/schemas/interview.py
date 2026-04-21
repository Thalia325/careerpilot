from pydantic import BaseModel, Field


class MockInterviewRequest(BaseModel):
    student_id: int = Field(..., gt=0)
    job_code: str = Field(default="", max_length=100)
    profile_version_id: int | None = None
    analysis_run_id: int | None = None


class MockInterviewQuestion(BaseModel):
    question_id: str
    category: str
    question: str
    focus_points: list[str]
    answer_tips: list[str]


class MockInterviewGenerateResponse(BaseModel):
    student_id: int
    job_code: str
    job_title: str
    readiness_score: float
    readiness_level: str
    focus_summary: list[str]
    questions: list[MockInterviewQuestion]


class MockInterviewAnswer(BaseModel):
    question_id: str = Field(..., min_length=1, max_length=40)
    answer: str = Field(..., min_length=1, max_length=4000)


class MockInterviewEvaluateRequest(MockInterviewRequest):
    answers: list[MockInterviewAnswer] = Field(..., min_length=1)


class MockInterviewFeedbackItem(BaseModel):
    question_id: str
    question: str
    score: float
    matched_points: list[str]
    missing_points: list[str]
    suggestion: str


class MockInterviewEvaluateResponse(BaseModel):
    student_id: int
    job_code: str
    job_title: str
    overall_score: float
    readiness_level: str
    recommendation: str
    focus_summary: list[str]
    feedback: list[MockInterviewFeedbackItem]
    next_actions: list[str]
