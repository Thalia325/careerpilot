# API 设计

## 认证

- `POST /api/v1/auth/login`
- `GET /api/v1/auth/me`

## 数据接入与知识构建

- `POST /api/v1/jobs/import`
- `GET /api/v1/jobs`
- `POST /api/v1/job-profiles/generate`
- `GET /api/v1/job-profiles/templates`

## OCR 与材料解析

- `POST /api/v1/files/upload`
- `POST /api/v1/ocr/parse`

## 学生画像

- `POST /api/v1/student-profiles/generate`
- `GET /api/v1/student-profiles/{student_id}`

## 岗位图谱与职业路径

- `GET /api/v1/graph/jobs/{job_code}`
- `POST /api/v1/career-paths/plan`

## 人岗匹配

- `POST /api/v1/matching/analyze`

## 报告

- `POST /api/v1/reports/generate`
- `POST /api/v1/reports/polish`
- `POST /api/v1/reports/check`
- `POST /api/v1/reports/export`

## 定时任务与闭环跟踪

- `GET /api/v1/scheduler/jobs`
- `POST /api/v1/scheduler/jobs`
- `POST /api/v1/scheduler/run-due`

## 智能体入口

- `POST /api/v1/agents/execute`

