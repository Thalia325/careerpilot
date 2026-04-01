# 数据库设计

## PostgreSQL 关键表

| 表名 | 说明 | 核心字段 |
|---|---|---|
| `users` | 统一用户表 | `username` `password_hash` `role` |
| `students` | 学生主体信息 | `user_id` `major` `grade` `career_goal` |
| `teachers` | 教师主体信息 | `user_id` `department` `title` |
| `resumes` | 简历记录 | `student_id` `file_id` `parsed_json` |
| `certificates` | 证书记录 | `student_id` `file_id` `name` `issuer` |
| `transcripts` | 成绩单记录 | `student_id` `file_id` `gpa` `parsed_json` |
| `uploaded_files` | 上传文件元数据 | `owner_id` `file_type` `storage_key` `url` |
| `companies` | 企业信息 | `name` `industry` `size` `ownership_type` |
| `job_postings` | 原始岗位数据 | `job_code` `title` `location` `salary_range` `description` |
| `job_profiles` | 岗位画像 | `job_posting_id` `skill_requirements` `capability_scores` `dimension_weights` |
| `skills` | 技能词典 | `name` `category` |
| `certificates_required` | 岗位证书要求 | `job_profile_id` `certificate_name` `reason` |
| `student_profiles` | 学生就业能力画像 | `student_id` `skills_json` `certificates_json` `completeness_score` `competitiveness_score` |
| `student_profile_evidence` | 学生画像证据链 | `student_profile_id` `evidence_type` `source` `excerpt` |
| `match_results` | 人岗匹配总结果 | `student_profile_id` `job_profile_id` `total_score` `summary` |
| `match_dimension_scores` | 四维评分明细 | `match_result_id` `dimension` `score` `weight` `reasoning` |
| `career_paths` | 路径模板/图谱结果快照 | `target_job_code` `primary_path_json` `alternate_paths_json` |
| `path_recommendations` | 个体化路径推荐 | `student_id` `target_job_code` `gaps_json` `recommendations_json` |
| `growth_tasks` | 成长任务 | `student_id` `title` `phase` `deadline` `metric` |
| `followup_records` | 跟踪记录 | `student_id` `task_id` `record_type` `content` |
| `career_reports` | 报告主表 | `student_id` `target_job_code` `content_json` `status` |
| `report_versions` | 报告版本 | `report_id` `version_no` `content_json` `editor_notes` |
| `system_configs` | 系统配置 | `config_key` `config_value` |
| `knowledge_documents` | 知识库文档索引 | `doc_type` `title` `content` `source_ref` |
| `scheduler_jobs` | 定时任务 | `job_name` `cron_expr` `status` `payload_json` |

## 设计要点

- 所有核心输出均持久化，支持报告回溯、路径复算、跟踪闭环。
- 画像、匹配、报告均保留 `evidence/reasoning` 字段，保证可解释性。
- 通过 `job_postings -> job_profiles -> match_results` 串联岗位知识与用户决策。

