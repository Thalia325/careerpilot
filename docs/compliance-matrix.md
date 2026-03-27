# 需求覆盖与合规矩阵

| A13/架构要求 | 是否覆盖 | 对应模块 | 对应接口/页面 | 对应测试 |
|---|---|---|---|---|
| 学生端 Web、教师端工作台、管理后台三层交互 | 是 | `frontend/app/student` `frontend/app/teacher` `frontend/app/admin` | `/student/*` `/teacher` `/admin` | `backend/tests/integration/test_demo_flow.py` |
| OpenClaw 主控智能体、工具调用层、子智能体群、任务路由、状态管理 | 是 | `backend/app/services/agents` | `POST /api/v1/agents/execute` | `backend/tests/unit/test_agents.py` |
| 简历解析智能体：PaddleOCR + ERNIE 信息抽取 | 是 | `integrations/ocr` `services/agents/resume_agent.py` | `POST /api/v1/ocr/parse` | `backend/tests/unit/test_ocr.py` |
| 岗位画像智能体：岗位抓取/清洗/知识构建 | 是 | `services/ingestion` `services/agents/job_profile_agent.py` | `POST /api/v1/jobs/import` `POST /api/v1/job-profiles/generate` | `backend/tests/integration/test_job_ingestion_pipeline.py` |
| 动态跟踪智能体：cron/scheduler 提醒、推送、复盘 | 是 | `services/scheduler` `services/agents/tracking_agent.py` | `GET/POST /api/v1/scheduler/jobs` | `backend/tests/integration/test_scheduler_flow.py` |
| 报告生成智能体：生成职业发展报告 | 是 | `services/reports` `services/agents/report_agent.py` | `POST /api/v1/reports/generate` | `backend/tests/integration/test_demo_flow.py` |
| PaddleOCR 感知层：支持简历/证书/成绩单/招聘材料解析 | 是 | `integrations/ocr/providers.py` `services/ingestion/file_ingestion.py` | `POST /api/v1/files/upload` `POST /api/v1/ocr/parse` | `backend/tests/unit/test_ocr.py` |
| OCR 流程包含文字识别、版面分析、结构化 JSON 输出 | 是 | `integrations/ocr` | `POST /api/v1/ocr/parse` | `backend/tests/unit/test_ocr.py` |
| ERNIE 作为核心认知引擎并保留 Provider 抽象 | 是 | `integrations/llm/providers.py` | 所有画像/匹配/报告接口 | `backend/tests/unit/test_student_profile.py` |
| RAGFlow + Neo4j 混合知识架构 | 是 | `integrations/ragflow` `integrations/graph` | `POST /api/v1/jobs/import` `GET /api/v1/graph/jobs/{job_code}` | `backend/tests/integration/test_job_ingestion_pipeline.py` |
| 本地无法直连时使用适配器 + mock/fallback provider | 是 | `integrations/*/providers.py` | 启动配置与所有核心接口 | `backend/tests/unit/test_providers.py` |
| PostgreSQL、MinIO、Neo4j 数据层边界 | 是 | `db/session.py` `integrations/storage` `integrations/graph` | 文件、图谱、业务 API | `backend/tests/integration/test_demo_flow.py` |
| 支持导入约 10000 条岗位数据 | 是 | `scripts/generate_sample_jobs.py` `services/ingestion/job_import_service.py` | `POST /api/v1/jobs/import` | `backend/tests/integration/test_job_ingestion_pipeline.py` |
| 岗位字段包含职位名称、地址、薪资、公司、行业、规模、性质、编码、描述、简介 | 是 | `models/job.py` `schemas/job.py` | `POST /api/v1/jobs/import` | `backend/tests/integration/test_job_ingestion_pipeline.py` |
| 数据导入脚本、清洗标准化、向量化/知识库入库、Neo4j 图谱构建、可复跑初始化 | 是 | `scripts/seed_demo.py` `scripts/generate_sample_jobs.py` `services/ingestion/*` | `POST /api/v1/jobs/import` | `backend/tests/integration/test_job_ingestion_pipeline.py` |
| 不少于 10 个岗位画像模板/实例 | 是 | `data/job_profile_templates.json` `services/ingestion/job_profile_service.py` | `GET /api/v1/job-profiles/templates` | `backend/tests/unit/test_job_profile.py` |
| 每个岗位画像包含技能、证书、创新、学习、抗压、沟通、实习能力且可解释 | 是 | `schemas/job_profile.py` `services/ingestion/job_profile_service.py` | `POST /api/v1/job-profiles/generate` | `backend/tests/unit/test_job_profile.py` |
| 建立垂直岗位图谱、换岗路径图谱 | 是 | `integrations/graph` `services/paths` | `GET /api/v1/graph/jobs/{job_code}` `POST /api/v1/career-paths/plan` | `backend/tests/integration/test_job_ingestion_pipeline.py` |
| 至少 5 个岗位换岗路径且每个不少于 2 条 | 是 | `data/job_graph_seed.json` | `GET /api/v1/graph/jobs/{job_code}` | `backend/tests/unit/test_graph_seed.py` |
| 查询上游/下游岗位、晋升路径、转岗路径、技能差异 | 是 | `services/paths/graph_query_service.py` | `GET /api/v1/graph/jobs/{job_code}` | `backend/tests/unit/test_graph_queries.py` |
| 学生画像双输入方式：上传材料 + 手动录入 | 是 | `services/profiles/student_profile_service.py` | `POST /api/v1/student-profiles/generate` | `backend/tests/unit/test_student_profile.py` |
| 学生画像包含技能、证书、创新、学习、抗压、沟通、实习能力 | 是 | `schemas/student_profile.py` | `GET /api/v1/student-profiles/{student_id}` | `backend/tests/unit/test_student_profile.py` |
| 提供完整度评分、竞争力评分、评分依据 | 是 | `services/profiles/student_profile_service.py` | `POST /api/v1/student-profiles/generate` | `backend/tests/unit/test_student_profile.py` |
| 职业探索与岗位匹配：量化对比契合点与差距项 | 是 | `services/matching/matching_service.py` | `POST /api/v1/matching/analyze` | `backend/tests/unit/test_matching.py` |
| 职业目标设定与职业路径规划 | 是 | `services/paths/career_path_service.py` | `POST /api/v1/career-paths/plan` | `backend/tests/integration/test_demo_flow.py` |
| 行动计划至少包含短期、中期阶段、学习路径、实践安排、评估指标 | 是 | `services/reports/report_service.py` | `POST /api/v1/reports/generate` | `backend/tests/integration/test_demo_flow.py` |
| 报告支持润色、完整性检查、手动编辑、一键导出 PDF，尽量 DOCX | 是 | `services/reports/*` | `POST /api/v1/reports/polish` `POST /api/v1/reports/check` `POST /api/v1/reports/export` | `backend/tests/unit/test_report_completeness.py` |
| 人岗匹配必须按基础要求、职业技能、职业素养、发展潜力四维建模 | 是 | `services/matching/scoring.py` | `POST /api/v1/matching/analyze` | `backend/tests/unit/test_matching.py` |
| 允许不同岗位配置不同维度权重，并综合加权得分 | 是 | `models/job_profile.py` `services/matching/scoring.py` | `POST /api/v1/matching/analyze` | `backend/tests/unit/test_matching.py` |
| 返回匹配总分、分维度解释、差距项、提升建议 | 是 | `schemas/matching.py` | `POST /api/v1/matching/analyze` | `backend/tests/unit/test_matching.py` |
| 闭环跟踪：定时提醒、资源推送、阶段复盘、成长任务追踪 | 是 | `services/scheduler` | `GET/POST /api/v1/scheduler/jobs` | `backend/tests/integration/test_scheduler_flow.py` |
| 形成“规划→执行→反馈→再规划”闭环 | 是 | `services/scheduler/followup_service.py` | `POST /api/v1/scheduler/run-due` | `backend/tests/integration/test_scheduler_flow.py` |
| 准确率指标：匹配关键技能 ≥ 80%，画像关键信息 > 90% | 是 | `scripts/evaluate_accuracy.py` | 命令行评估脚本 | `backend/tests/unit/test_evaluation_script.py` |
| 报告要具备可操作性、明确岗位建议、差距、路径、短中期计划、评估周期 | 是 | `services/reports/report_service.py` | `POST /api/v1/reports/generate` | `backend/tests/unit/test_report_completeness.py` |
| 所有核心输出必须可解释 | 是 | `schemas/*` `services/*` | 画像/匹配/路径/报告接口 | `backend/tests/unit/test_matching.py` |
| 友好界面、符合用户习惯、可完整演示业务闭环 | 是 | `frontend/app/*` | 学生端、教师端、管理端页面 | `backend/tests/integration/test_demo_flow.py` |

