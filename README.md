# CareerPilot

CareerPilot 是一个面向大学生职业规划场景的 AI 智能体系统，对齐 `PaddleOCR + ERNIE × OpenClaw` 架构要求，实现岗位知识构建、学生画像、人岗匹配、职业路径规划、报告生成与闭环跟踪。

## 核心特性

- `OpenClaw` 风格主控智能体 + 子智能体协同编排
- `PaddleOCR` / Mock OCR 适配器，支持简历、证书、成绩单、招聘材料解析
- `ERNIE` / Mock LLM 适配器，支撑岗位画像、学生画像、匹配分析、报告生成
- `RAGFlow` / Mock 检索适配器 + `Neo4j` / Mock 图谱适配器
- `PostgreSQL + MinIO + Neo4j` 生产接口边界，开发阶段可本地回退
- 学生端、教师端、管理后台三套界面
- PDF 导出、DOCX 导出、完整性检查、报告润色、定时跟踪

## 快速开始

### 1. 后端

```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp ../.env.example ../.env
python -m app.main
```

后端启动后访问：

- API: [http://localhost:8000/api/v1](http://localhost:8000/api/v1)
- OpenAPI: [http://localhost:8000/docs](http://localhost:8000/docs)

### 2. 前端

```bash
cd frontend
npm install
npm run dev
```

前端访问：

- Web: [http://localhost:3000](http://localhost:3000)

### 3. 初始化演示数据

```bash
cd backend
python scripts/generate_sample_jobs.py --output ../data/sample_jobs.csv --rows 10000
python scripts/seed_demo.py
```

## 演示账号

- 学生端：`student_demo / demo123`
- 教师端：`teacher_demo / demo123`
- 管理端：`admin_demo / demo123`

## 交付内容

- [需求覆盖与合规矩阵](docs/compliance-matrix.md)
- [系统架构设计](docs/architecture.md)
- [数据库设计](docs/database-design.md)
- [Neo4j 图谱设计](docs/neo4j-graph-design.md)
- [API 设计](docs/api-design.md)

## 本地开发说明

- 默认使用 Mock Provider 保证本地可运行。
- 切换生产能力时，只需在 `.env` 中调整 `LLM_PROVIDER / OCR_PROVIDER / RAGFLOW_PROVIDER / GRAPH_PROVIDER / STORAGE_PROVIDER`。
- 代码里保留正式适配器接口和开发替代实现，不以本地调试为由删除生产边界。

## 评估与测试

```bash
cd backend
pytest
python scripts/evaluate_accuracy.py
```

## 目录概览

```text
CareerPilot/
├── backend/
├── frontend/
├── data/
├── docs/
├── exports/
├── docker-compose.yml
└── README.md
```

## 官方岗位库导入

项目现在支持直接读取 A13 官方岗位数据。默认通过根目录 `.env` 中的 `JOB_DATASET_PATH` 指向数据文件，例如：

```bash
JOB_DATASET_PATH=C:/Users/Lenovo/Downloads/20260226105856_457.xls
JOB_DATASET_FILTERING_ENABLED=true
```

首次启动后端时，如果库里还没有岗位画像，系统会优先导入这份官方数据；只有未配置 `JOB_DATASET_PATH` 时，才会退回示例模板数据。导入前会按 A13 答疑口径优先筛掉非计算机/信息类岗位。

如需手动重导入官方岗位库，可执行：

```bash
cd backend
python scripts/reimport_job_dataset.py
```

如果想临时指定别的数据文件：

```bash
cd backend
python scripts/reimport_job_dataset.py --dataset C:/path/to/jobs.xls
```

## 本地知识库导出

企业要求提交筛选并向量化后的本地知识库 JSON，可执行：

```bash
cd backend
python scripts/export_local_knowledge_base.py
```

默认导出到 `exports/knowledge_base/a13_local_knowledge_base.json`，内容包含筛选后的岗位数据、聚合岗位画像和知识库文档。

## A13 准确率评估

项目提供了贴近企业抽测口径的评估脚本，可直接基于标注样本输出 JSON 报告：

```bash
cd backend
python scripts/evaluate_accuracy.py --cases ../data/evaluation_cases.sample.json
```

默认报告输出到 `exports/accuracy_report.json`。

## A13 2026-04-20 更新

当前项目已经按更严格的 A13 口径重新清洗岗位库：

- 官方原始表：`9958` 条
- 严格清洗后官方可用岗位：`3906` 条
- 严格清洗后官方唯一岗位：`3430` 条
- 增量补抓后合并可用岗位：`6860` 条
- 当前数据库落库岗位：`6860` 条
- 当前数据库聚合岗位画像：`123` 个

### 批量导库

批量导库阶段允许临时使用 `mock` 生成岗位画像，用于离线初始化和大规模重建数据：

```bash
cd backend
python scripts/reimport_job_dataset.py --dataset ../data/a13_jobs_augmented.csv --profile-provider mock
```

这个参数只影响当前命令，不会改写根目录 `.env`。

### 真模型刷新画像

如果需要在答辩或正式演示前切回真实模型，可直接基于当前数据库里的聚合岗位重刷画像：

```bash
cd backend
python scripts/refresh_job_profiles.py --profile-provider ernie
```

如果只想先刷新一部分代表性岗位：

```bash
cd backend
python scripts/refresh_job_profiles.py --profile-provider ernie --titles Java 前端开发 软件测试 实施工程师 技术支持工程师
```

### 增量补抓

项目现在提供了按官方字段结构补抓并合并岗位库的脚本，输出文件：

- `data/a13_jobs_supplement.csv`
- `data/a13_jobs_augmented.csv`

执行命令：

```bash
cd backend
python scripts/supplement_job_dataset.py --target-multiplier 2.0
```

## A13 真实标注评估

除了示例样本，项目现在还提供了团队真实标注模板与使用说明：

- `data/evaluation_cases.template.json`
- `docs/a13-accuracy-evaluation.md`

建议先复制模板，再替换成你们自己的真实抽测样本：

```bash
copy data\\evaluation_cases.template.json data\\evaluation_cases.team.json
cd backend
python scripts/evaluate_accuracy.py --cases ../data/evaluation_cases.team.json --report ../exports/accuracy_report.team.json
```

脚本会在报告里额外标记：

- 当前是否仍在使用 `sample`
- 当前是否仍在使用 `template`
- 当前样本是否已标记为 `team_labeled`
- 当前是否达到参赛就绪状态
