# CareerPilot 测试数据生成指南

> **核心原则：数据仅用于模型训练和测试验证，绝不改动任何业务代码逻辑。**

## 概述

项目根目录下 `50+份非计算机简历（dyxhs）.pdf.zip` 包含一份 64 页扫描 PDF，每页为一份简历。本指南描述如何利用这些简历，通过 API 注册账号、上传简历、填充数据库，生成完整的测试数据链路，用于模型训练和系统演示。

## 约束

- **禁止修改** `backend/app/` 下任何 `.py` 源码
- **禁止修改** `frontend/` 下任何源码
- **禁止修改** `.env` 中的业务配置
- 所有操作仅通过 **HTTP API** 或 **直接数据库写入** 完成
- 生成的测试账号统一使用前缀 `test_`，与 demo 账号区分

## 数据源

```
简历压缩包: 50+份非计算机简历（dyxhs）.pdf.zip
内容: 1 个合并 PDF，共 64 页扫描简历（无可提取文字层）
```

## 环境要求

| 服务 | 地址 | 说明 |
|------|------|------|
| Backend API | `http://127.0.0.1:8001/api/v1` | 当前运行在 8001 端口（8000 被占用） |
| Frontend | `http://localhost:3000` | Next.js 开发服务器 |
| SQLite 数据库 | `backend/careerpilot-8001.db` | 本地开发数据库 |

> 注意：curl 在本机环境会走 proxy 导致 503，测试脚本须使用 `httpx` 或 `requests` 直连 `127.0.0.1`。

## 执行步骤

### 第一步：拆分 PDF

将 64 页合并 PDF 拆分为单页 PDF，每份简历对应一页。

```python
from pypdf import PdfReader, PdfWriter

reader = PdfReader("resumes_raw/<合并PDF文件名>")
for i in range(len(reader.pages)):
    writer = PdfWriter()
    writer.add_page(reader.pages[i])
    writer.write(f"resumes_split/resume_{i+1:03d}.pdf")
```

输出目录：`resumes_split/resume_001.pdf` ~ `resume_064.pdf`

### 第二步：注册教师账号

注册 3 个教师账号，用于不同院系。

| 用户名 | 姓名 | 院系 |
|--------|------|------|
| test_teacher_01 | 王建国老师 | 计算机学院 |
| test_teacher_02 | 李芳老师 | 商学院 |
| test_teacher_03 | 张伟老师 | 工学院 |

```python
POST /api/v1/auth/register
{
    "username": "test_teacher_01",
    "password": "Test1234",
    "full_name": "王建国老师",
    "role": "teacher",
    "email": "test_teacher_01@careerpilot.local"
}
```

注册后通过 `PUT /api/v1/students/me` 补充教师信息（department, title），需先登录获取 token。

### 第三步：注册学生账号

为每份简历注册一个学生账号（约 50-64 个）。

```python
POST /api/v1/auth/register
{
    "username": "test_student_001",
    "password": "Test1234",
    "full_name": "测试学生001",
    "role": "student",
    "email": "test_student_001@careerpilot.local"
}
```

注册后通过 `PUT /api/v1/students/me` 补充学生信息：

```python
PUT /api/v1/students/me
{
    "major": "金融学",
    "grade": "大三",
    "career_goal": "金融分析师",
    "teacher_code": "test_teacher_02"
}
```

`teacher_code` 填教师用户名即可自动绑定师生关系。

### 第四步：上传简历

为每个学生上传对应的拆分简历 PDF。

```python
POST /api/v1/files/upload
Content-Type: multipart/form-data

owner_id: <学生user_id>
file_type: resume
upload: <resume_XXX.pdf>
```

> 单文件限制 10MB，支持的格式：`.pdf .doc .docx .png .jpg .jpeg`

### 第五步：创建分析流程

为每个学生启动分析流程，建立完整数据链路。

```python
POST /api/v1/analysis/start
{
    "student_id": <student_id>,
    "job_code": "J-FIN-001",
    "file_ids": [<uploaded_file_id>],
    "resume_file_id": <uploaded_file_id>
}
```

### 第六步：直接数据库写入 — 填充画像/匹配/报告

由于简历是扫描件且 OCR 为 mock 模式，API 无法自动解析。需要直接操作 SQLite 数据库写入训练数据。

**数据库路径**: `backend/careerpilot-8001.db`

#### 写入流程

按以下顺序写入，保证外键完整：

```
student_profiles → match_results → match_dimension_scores → career_reports → growth_tasks → followup_records
```

#### 关键表结构

| 表名 | 用途 | 关键字段 |
|------|------|----------|
| `users` | 用户 | id, username, role |
| `students` | 学生 | id, user_id, major, grade, target_job_code |
| `teachers` | 教师 | id, user_id, department |
| `teacher_student_links` | 师生绑定 | teacher_id, student_id |
| `uploaded_files` | 文件 | id, owner_id, file_type |
| `student_profiles` | 能力画像 | student_id, skills_json, capability_scores, completeness_score |
| `match_results` | 匹配结果 | student_profile_id, job_profile_id, total_score |
| `match_dimension_scores` | 维度分数 | match_result_id, dimension, score, weight |
| `career_reports` | 职业报告 | student_id, target_job_code, status, content_json, markdown_content |
| `growth_tasks` | 成长任务 | student_id, title, phase, status, deadline |
| `followup_records` | 教师跟进 | student_id, record_type, content |

#### 专业与目标岗位映射

根据简历内容（非计算机专业），合理分配目标岗位：

```python
MAJOR_JOB_MAP = {
    "金融学": ("J-FIN-001", "金融分析师"),
    "会计学": ("J-ACC-001", "财务会计"),
    "法学": ("J-LAW-001", "法务专员"),
    "教育学": ("J-EDU-001", "培训讲师"),
    "市场营销": ("J-MKT-001", "市场营销专员"),
    "工商管理": ("J-HR-001", "人力资源专员"),
    "机械工程": ("J-MECH-001", "机械工程师"),
    "土木工程": ("J-CIV-001", "土木工程师"),
    "建筑学": ("J-ARC-001", "建筑设计师"),
    "电气工程": ("J-ELE-001", "电气工程师"),
    "药学": ("J-PHA-001", "医药代表"),
    "新闻学": ("J-JOU-001", "记者/编辑"),
    "英语": ("J-TRL-001", "翻译/本地化"),
    "国际经济与贸易": ("J-TRD-001", "外贸专员"),
    "社会工作": ("J-PSY-001", "心理咨询师"),
    "体育教育": ("J-FIT-001", "健身教练"),
    "农学": ("J-AGR-001", "农业技术员"),
    "食品科学与工程": ("J-FDQ-001", "食品安全/质量管理"),
}
```

#### 能力画像数据模板

```python
profile = {
    "source_summary": "张三，金融学专业大三学生，目标岗位：金融分析师",
    "skills_json": ["财务建模", "行业研究", "Excel", "Python", "估值分析"],
    "certificates_json": ["CET-4", "CET-6", "CFA一级（在考）"],
    "projects_json": ["上市公司财务报表分析与估值建模", "行业研究报告撰写实践"],
    "internships_json": ["中国银行 - 金融分析师实习生"],
    "capability_scores": {
        "innovation": 78.5,
        "learning": 82.3,
        "resilience": 75.0,
        "communication": 80.2,
        "internship": 72.1,
    },
    "completeness_score": 75.0,
    "competitiveness_score": 78.0,
}
```

#### 匹配结果数据模板

匹配分数应在 40-95 之间随机分布，保证训练数据的多样性：

```python
match_result = {
    "total_score": 78.5,
    "strengths_json": ["具备财务建模技能基础", "行业研究能力突出"],
    "gaps_json": [{"item": "Python数据分析", "detail": "建议系统学习Python数据分析相关知识"}],
    "suggestions_json": ["补强核心技能短板", "争取相关实习机会"],
}
```

维度分数需与总分保持一致：

```python
dimensions = {
    "basic_requirements": {"name": "基础要求", "weight": 0.15},
    "professional_skills": {"name": "职业技能", "weight": 0.45},
    "professional_literacy": {"name": "职业素养", "weight": 0.20},
    "development_potential": {"name": "发展潜力", "weight": 0.20},
}
```

#### 报告数据模板

```python
report = {
    "status": "completed",  # draft / edited / completed
    "content_json": {
        "student_summary": "...",
        "capability_profile": {"skills": [...], "completeness": 75},
        "matching_analysis": {"total_score": 78.5, "target_job": "金融分析师"},
    },
    "markdown_content": "# 张三的职业规划报告\n\n## 基本信息\n...",
}
```

#### 成长任务模板

```python
growth_task = {
    "title": "完成财务建模课程",
    "phase": "短期",
    "status": "in_progress",  # pending / in_progress / completed / overdue
    "deadline": "2026-06-01T00:00:00Z",
    "metric": "完成度100%",
}
```

## 数据分布策略

为保证训练数据质量，数据应覆盖以下维度：

### 匹配分数分布
| 区间 | 比例 | 说明 |
|------|------|------|
| 85-95 | 20% | 高匹配度学生 |
| 70-84 | 35% | 中高匹配度 |
| 55-69 | 30% | 中等匹配度 |
| 40-54 | 15% | 低匹配度 |

### 报告状态分布
| 状态 | 比例 |
|------|------|
| completed | 40% |
| edited | 30% |
| draft | 20% |
| 无报告 | 10% |

### 成长任务状态分布
| 状态 | 比例 |
|------|------|
| completed | 25% |
| in_progress | 30% |
| pending | 30% |
| overdue | 15% |

### 画像完整度分布
| 区间 | 比例 |
|------|------|
| 80-100 | 20% |
| 60-79 | 35% |
| 40-59 | 30% |
| 0-39 | 15% |

## 验证方法

数据写入后，通过以下方式验证：

```bash
# 1. API 验证 — 登录学生账号查看画像
python -c "
import httpx
r = httpx.post('http://127.0.0.1:8001/api/v1/auth/login',
    json={'username': 'test_student_001', 'password': 'Test1234'})
token = r.json()['access_token']
print(httpx.get('http://127.0.0.1:8001/api/v1/students/me',
    headers={'Authorization': f'Bearer {token}'}).json())
"

# 2. 数据库验证 — 统计记录数
python -c "
import sqlite3
conn = sqlite3.connect('backend/careerpilot-8001.db')
for table in ['users','students','teachers','student_profiles',
              'match_results','match_dimension_scores','career_reports','growth_tasks']:
    count = conn.execute(f'SELECT COUNT(*) FROM {table}').fetchone()[0]
    print(f'{table}: {count}')
conn.close()
"

# 3. 教师端验证 — 查看班级概览
python -c "
import httpx
r = httpx.post('http://127.0.0.1:8001/api/v1/auth/login',
    json={'username': 'test_teacher_01', 'password': 'Test1234'})
token = r.json()['access_token']
print(httpx.get('http://127.0.0.1:8001/api/v1/teacher/stats/overview',
    headers={'Authorization': f'Bearer {token}'}).json())
"
```

## 清理方法

如需清除测试数据（不影响 demo 数据）：

```sql
-- 按用户名前缀 test_ 清理
DELETE FROM growth_tasks WHERE student_id IN (
    SELECT s.id FROM students s JOIN users u ON s.user_id = u.id WHERE u.username LIKE 'test_%');
DELETE FROM career_reports WHERE student_id IN (
    SELECT s.id FROM students s JOIN users u ON s.user_id = u.id WHERE u.username LIKE 'test_%');
DELETE FROM match_dimension_scores WHERE match_result_id IN (
    SELECT mr.id FROM match_results mr WHERE mr.student_id IN (
        SELECT s.id FROM students s JOIN users u ON s.user_id = u.id WHERE u.username LIKE 'test_%'));
DELETE FROM match_results WHERE student_id IN (
    SELECT s.id FROM students s JOIN users u ON s.user_id = u.id WHERE u.username LIKE 'test_%');
DELETE FROM student_profiles WHERE student_id IN (
    SELECT s.id FROM students s JOIN users u ON s.user_id = u.id WHERE u.username LIKE 'test_%');
DELETE FROM analysis_runs WHERE student_id IN (
    SELECT s.id FROM students s JOIN users u ON s.user_id = u.id WHERE u.username LIKE 'test_%');
DELETE FROM uploaded_files WHERE owner_id IN (
    SELECT id FROM users WHERE username LIKE 'test_%');
DELETE FROM teacher_student_links WHERE student_id IN (
    SELECT s.id FROM students s JOIN users u ON s.user_id = u.id WHERE u.username LIKE 'test_%');
DELETE FROM followup_records WHERE student_id IN (
    SELECT s.id FROM students s JOIN users u ON s.user_id = u.id WHERE u.username LIKE 'test_%');
DELETE FROM students WHERE user_id IN (SELECT id FROM users WHERE username LIKE 'test_%');
DELETE FROM teachers WHERE user_id IN (SELECT id FROM users WHERE username LIKE 'test_%');
DELETE FROM users WHERE username LIKE 'test_%';
```

## API 速查

| 操作 | 方法 | 路径 | 备注 |
|------|------|------|------|
| 注册 | POST | `/api/v1/auth/register` | 返回 token |
| 登录 | POST | `/api/v1/auth/login` | 返回 token |
| 当前用户 | GET | `/api/v1/auth/me` | 需 Bearer token |
| 上传文件 | POST | `/api/v1/files/upload` | multipart/form-data |
| 文件列表 | GET | `/api/v1/files/` | 需 Bearer token |
| 更新学生信息 | PUT | `/api/v1/students/me` | major, grade, career_goal, teacher_code |
| 设置目标岗位 | PUT | `/api/v1/students/me/target-job` | job_code, job_title |
| 推荐岗位 | GET | `/api/v1/students/me/recommended-jobs` | 需有画像数据 |
| 启动分析 | POST | `/api/v1/analysis/start` | student_id, file_ids |
| 更新教师信息 | PUT | `/api/v1/teacher/me` | department, title |
| 班级概览 | GET | `/api/v1/teacher/stats/overview` | 教师端统计 |
| 学生报告列表 | GET | `/api/v1/teacher/students/reports` | 教师端查看 |
