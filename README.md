# CareerPilot

CareerPilot 是一个面向大学生职业规划场景的 AI 智能体系统，严格对齐 A13 赛题与 `PaddleOCR + ERNIE × OpenClaw` 架构要求，实现岗位知识构建、学生画像、人岗匹配、职业路径规划、报告生成与闭环跟踪。

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

