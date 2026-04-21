# A13 答疑逐项核对

状态说明：
- `已符合`：代码或页面已有明确实现，和企业答疑口径基本一致。
- `部分符合`：有相关能力，但和答疑口径仍有偏差，评审时可能被追问。
- `未符合`：当前项目没有实现，或实现方向与答疑要求明显不一致。
- `非代码项`：属于提交方式、答疑渠道、字体等赛务事项，不属于项目代码核对范围。

## 总结

当前项目最关键的结论是：

1. 官方岗位库接入已经完成，项目现在可以读取并重导入企业提供的 `.xls` 数据。
2. 官方岗位库现在会先按 A13 答疑口径清洗，仅保留计算机/信息类岗位；当前官方表从 `9958` 行筛到 `5412` 行，落库唯一岗位 `4879` 个。
3. “相同岗位合并后生成岗位画像”已经落地，当前官方数据导入后聚合为 `51` 个岗位画像。
4. 本地知识库 `json` 导出已经补齐，当前可直接导出提交版 JSON。
5. 目前最大的剩余缺口集中在：准确率报告还需要替换成团队真实标注样本，赛事版详细方案文档仍需补齐。

## 逐项核对

| 编号 | 主题 | 结论 | 说明 | 证据 |
|---|---|---|---|---|
| 1, 3, 19, 25, 33, 37, 38, 40, 49 | 官方岗位数据获取与导入 | 已符合 | 项目已支持通过 `JOB_DATASET_PATH` 读取官方 `.xls`，并提供重导入脚本。 | `backend/app/services/reference.py`, `backend/scripts/reimport_job_dataset.py`, `.env` |
| 2, 24, 47 | 岗位晋升图谱 / 换岗路径与岗位相关 | 已符合 | 图谱已改为“官方岗位画像优先、seed 仅兜底”：启动时会把当前数据库中的聚合岗位画像全部同步进图谱，并基于真实岗位标题生成晋升路径、换岗路径、垂直序列和转岗集群；路径规划接口也不再混入大段演示 fallback。 | `backend/app/integrations/graph/providers.py`, `backend/app/services/bootstrap.py`, `backend/app/services/paths/career_path_service.py` |
| 4, 18, 42, 50, 51, 57, 59 | 本地知识库资料需提交，最好为 json | 已符合 | 已补充知识库导出能力，可输出提交版 `json`，内容含筛选后岗位数据、聚合岗位画像和知识库文档；同时提供管理员接口和本地脚本。 | `backend/app/services/ingestion/job_import_service.py`, `backend/app/api/routers/jobs.py`, `backend/scripts/export_local_knowledge_base.py` |
| 5, 30, 32, 43 | 准确率测试标准与证明材料 | 部分符合 | 已补齐评估脚本、团队真实标注模板、使用说明和 JSON 报告链路；当前剩余工作只是把模板替换成团队自己的真实标注样本。 | `backend/scripts/evaluate_accuracy.py`, `data/evaluation_cases.template.json`, `docs/a13-accuracy-evaluation.md`, `exports/accuracy_report.json` |
| 6, 41, 44 | 智能体不要求严格 OpenClaw，AI 平台即可 | 已符合 | 项目具备 OCR、画像、匹配、路径、报告、聊天与多页面 AI 平台形态，满足“AI 平台即可”的口径。 | `backend/app/services/agents/*`, `frontend/app/student/*`, `frontend/app/teacher/*` |
| 7, 28 | 链接失效不影响，不必剔除 | 已符合 | 数据导入逻辑不依赖招聘链接有效性，重点使用表格字段。 | `backend/app/services/reference.py` |
| 8, 12, 16, 21, 23, 45 | 只保留计算机 / 信息类岗位 | 已符合 | 已在官方岗位数据读取链路增加过滤规则，导入与浏览都只走清洗后的数据；当前官方表 `9958` 行中筛出 `5412` 行，去重后落库 `4879` 个岗位。 | `backend/app/services/reference.py`, `backend/scripts/reimport_job_dataset.py`, `backend/app/api/routers/jobs.py` |
| 9 | 缺项数据不必删除，可综合同岗位多条数据形成画像 | 已符合 | 导入过程允许字段缺失；岗位画像已改为按同标题聚合生成。 | `backend/app/services/reference.py`, `backend/app/services/ingestion/job_import_service.py` |
| 10, 17, 22 | API key 可用环境变量，不必上交真实 key | 已符合 | 项目已有 `.env` / `.env.example` 配置模式，支持用环境变量和加密字段配置模型。 | `.env.example`, `backend/app/core/config.py` |
| 11, 52 | 既要做人岗匹配，也要支持目标岗位差距分析与学习规划 | 已符合 | 已有人岗匹配、目标岗位路径规划和职业报告；报告现已明确同时呈现“当前较匹配岗位”和“理想岗位”，并给出差距建议。 | `backend/app/api/routers/matching.py`, `backend/app/api/routers/career_paths.py`, `backend/app/api/routers/reports.py`, `frontend/app/results/[id]/page.tsx` |
| 13 | 最终岗位画像是相同岗位合并结果 | 已符合 | 当前导入后按岗位标题聚合生成画像，不再按每条招聘记录单独生成。 | `backend/app/services/ingestion/job_import_service.py` |
| 14, 34 | 可以自行补充爬取岗位数据 | 非代码项 | 项目没有限制继续扩充数据；是否额外爬取是团队策略，不是代码缺陷。 | 当前实现不构成阻塞 |
| 15, 20, 46, 48, 53 | 是否必须提交代码 / 链接 | 非代码项 | 这是赛务提交策略，不是项目实现问题。项目本身已有本地运行、导出和页面。 | `README.md` |
| 26 | 报告“智能润色 / 手动编辑”粗粒度即可 | 已符合 | 结果页支持整篇手动编辑、保存、智能润色。没有做段落级局部润色，但按答疑“粗粒度即可”是可接受的。 | `frontend/app/results/[id]/page.tsx`, `backend/app/api/routers/reports.py` |
| 27 | 评估周期偏内容设计，交互不必复杂 | 已符合 | 报告强制包含 `evaluation_cycle`，并有完整性检查；前端展示不复杂。 | `backend/app/services/reports/report_service.py`, `frontend/app/results/[id]/page.tsx` |
| 29 | 报告应体现匹配职位和理想职位 | 已符合 | 报告内容与结果页现在都会明确展示“当前较匹配岗位 + 理想岗位”，当两者不一致时，还会补充对照结论和差距建议。 | `backend/app/schemas/report.py`, `backend/app/services/reports/report_service.py`, `frontend/app/results/[id]/page.tsx` |
| 31 | 用户界面要有；后端管理不是硬要求 | 已符合 | 已有学生端、教师端、管理员端、登录与注册页面。 | `frontend/app/student/*`, `frontend/app/teacher/*`, `frontend/app/admin/*`, `frontend/app/login/page.tsx`, `frontend/app/register/page.tsx` |
| 35 | 不要求登录注册 | 已符合 | 项目虽然做了登录注册，但这不违背答疑；只是属于附加功能。 | `frontend/app/login/page.tsx`, `frontend/app/register/page.tsx`, `backend/app/api/routers/auth.py` |
| 36 | 本地演示即可，不一定上云 | 已符合 | 当前项目支持本地运行、导出报告、本地数据库和本地文件存储。 | `README.md`, `backend/app/core/config.py` |
| 39 | 需要详细方案文档 | 已符合 | 已补齐赛事版详细方案文档，按“需求分析 -> 系统设计 -> 核心流程 -> 测评方法 -> 提交材料”组织，可直接用于书面材料或答辩文档扩写。 | `docs/a13-detailed-solution.md`, `docs/architecture.md`, `docs/database-design.md`, `docs/api-design.md` |
| 50 | 本地数据集应是清洗后的岗位知识库，可分文件提交 | 已符合 | 已可导出清洗后的本地知识库 JSON，默认输出到 `exports/knowledge_base/a13_local_knowledge_base.json`，可以单独作为提交材料。 | `backend/scripts/export_local_knowledge_base.py`, `exports/knowledge_base/a13_local_knowledge_base.json` |
| 54 | PPT 里的“业务模式”更偏功能实现方式 | 已符合 | 已补业务模式与功能闭环文档，可直接转成答辩 PPT 页面，重点回答“谁在用、怎么闭环、价值在哪”。 | `docs/a13-business-mode.md`, `docs/a13-detailed-solution.md` |
| 56 | 面向大一到大四都可使用 | 已符合 | 学生档案、推荐、匹配、路径、报告都没有限定年级，只要有画像就能使用。 | `backend/app/models`, `frontend/app/student/*` |
| 58 | 模拟面试算创新功能点 | 已符合 | 已补模拟面试功能，支持按目标岗位生成面试题、学生作答、自动评分和改进建议。 | `backend/app/api/routers/interviews.py`, `backend/app/services/interviews/mock_interview_service.py`, `frontend/app/student/interview/page.tsx` |

## 重复问题不再单独展开

以下问题和上表对应项重复，结论一致：

- 数据下载类：`1, 3, 19, 25, 33, 37, 38, 40, 49`
- 本地知识库类：`4, 18, 42, 50, 51, 57, 59`
- 计算机类岗位清洗类：`8, 12, 16, 21, 23, 45`
- 准确率口径类：`5, 30, 32, 43`
- 智能体定义类：`6, 41, 44`
- 提交形式类：`15, 20, 46, 48, 53`

## 当前最优先整改项

### P0：仍需优先补

1. 把评估脚本中的示例样本替换成团队真实标注样本
   - 脚本已经可用，但最终答辩材料不能停留在示例数据。

### P1：应该改

1. 补一份赛事版详细方案文档
2. 把报告与知识库导出结果纳入提交流程截图/说明
3. 进一步增强教师点评与跟踪闭环展示

### P2：加分项

1. 模拟面试
2. 更多教师点评与跟踪闭环展示

## 2026-04-20 增补

本轮又补了两项和答疑直接相关的落地内容：

1. 岗位库扩充与清洗
   - 新增 `backend/scripts/supplement_job_dataset.py`，按官方字段结构补抓岗位并合并生成 `data/a13_jobs_augmented.csv`
   - 清洗口径已进一步收紧，加入岗位标题标准化和更严格的计算机/信息类过滤
   - 当前口径下：
     - 官方原始表 `9958` 条
     - 严格清洗后官方可用岗位 `3906` 条
     - 严格清洗后官方唯一岗位 `3430` 条
     - 增量补抓并合并后唯一岗位 `6860` 条

2. 批量导库与真模型刷新分离
   - `backend/scripts/reimport_job_dataset.py` 新增 `--profile-provider mock|ernie`
   - 新增 `backend/scripts/refresh_job_profiles.py`
   - 当前建议口径：
     - 批量重导库可临时用 `mock`
     - 正式答辩或演示前，可用 `ERNIE` 对代表性岗位或全量岗位画像进行重刷

## 2026-04-20 二次复核

这次按当前代码、数据库和导出物又核了一遍，后续答辩建议以本节为准。

### 当前已完成且可直接拿去说的状态

1. 严格清洗后的官方岗位库
   - 官方原始表：`9958` 条
   - 严格清洗后官方可用岗位：`3906` 条
   - 严格清洗后官方唯一岗位：`3430` 条
   - 增量补抓并合并后的唯一岗位：`6860` 条
2. 当前导出物状态
   - 本地知识库文件：`exports/knowledge_base/a13_local_knowledge_base.json`
   - `filtered_job_postings`：`6860`
   - `job_profiles`：`123`
   - `knowledge_documents`：`123`
3. 当前数据库状态
   - `job_postings`：`6860`
   - `job_profiles`：`124`
   - `job_profiles` 去重后标题数：`123`

### 仍未完成的答疑项

1. `5, 30, 32, 43` 准确率测试标准与证明材料
   - 当前脚本、模板、使用说明和报告导出链路已经补齐：
     - `backend/scripts/evaluate_accuracy.py`
     - `data/evaluation_cases.template.json`
     - `docs/a13-accuracy-evaluation.md`
   - 现在剩下的不是功能缺失，而是需要把模板替换成团队自己的真实标注样本，并把测试结果整理进 PPT 或单独报告
2. `39` 详细方案文档
   - 已补充比赛版详细方案文档：`docs/a13-detailed-solution.md`
   - 这一项现在已经从“缺文档”变成“可直接拿去整理进最终提交材料”
3. `54` PPT 中的“业务模式”说明
   - 已补充一页式说明文档：`docs/a13-business-mode.md`
   - 这一项现在可以直接转成 PPT 页面，不再是缺材料状态
4. `58` 模拟面试
   - 已补模拟面试模块，当前学生端可直接按目标岗位生成题目并获取评分反馈
   - 这一项现在已经从“未实现”变成“可展示的创新点”

### 本轮复核新发现的小问题

1. 数据库里仍有 `1` 条重复岗位画像
   - 当前 `job_profiles` 总数是 `124`，但按标题去重后是 `123`
   - 重复标题为：`Java开发工程师`
   - 这不会影响当前导出的本地知识库 JSON，因为导出结果已经是 `123` 个聚合画像
   - 但运行库本身最好再做一次去重清理，避免后续评审现场抽查时出现“库内计数和导出计数不一致”

## 2026-04-20 最新结论

按当前代码与文档状态，A13 答疑项里真正还没有闭环完成的，只剩 1 项：

1. `5, 30, 32, 43` 准确率证明材料
   - 功能链路已补齐
   - 模板已补齐
   - 使用说明已补齐
   - 现在只差把团队真实标注样本填进 `data/evaluation_cases.team.json`，再导出正式报告

本轮已新增并补齐的内容：

1. 准确率评估模板与说明
   - `backend/scripts/evaluate_accuracy.py`
   - `data/evaluation_cases.template.json`
   - `docs/a13-accuracy-evaluation.md`
2. 赛事版详细方案文档
   - `docs/a13-detailed-solution.md`
3. 业务模式 / 功能闭环文档
   - `docs/a13-business-mode.md`
4. 模拟面试创新功能
   - `backend/app/api/routers/interviews.py`
   - `backend/app/services/interviews/mock_interview_service.py`
   - `frontend/app/student/interview/page.tsx`

如果后续继续收尾，优先级建议如下：

1. 先补团队真实标注样本并生成正式准确率报告

补充：

1. 运行库里的重复 `Java开发工程师` 岗位画像已经清理完成
2. 当前数据库状态已对齐为：
   - `job_postings = 6860`
   - `job_profiles = 123`
   - `job_profiles` 去重标题数 = `123`

## 2026-04-20 ERNIE 刷新状态

本轮已将岗位画像刷新链路切换为严格 ERNIE 模式：

1. `backend/app/integrations/llm/providers.py`
   - 新增 JSON 修复重试
   - 岗位画像刷新失败时不再静默回退到 `mock`
   - 新增访问频繁场景的退避重试
2. `backend/app/services/ingestion/job_import_service.py`
   - 聚合岗位画像改为逐岗位提交
   - 日志中可直接看到 `[n/123]` 进度
3. `backend/scripts/refresh_job_profiles.py`
   - 新增严格模式环境变量
   - 新增 `--titles-file`
   - 支持断点续刷

实际全量刷新结果：

- 全量岗位画像总数：`123`
- 本轮成功用 ERNIE 刷新：`43`
- 失败：`80`
- 日志内 `fallback` 次数：`0`
- 失败原因：`403 访问过于频繁` 与 `40408 token 已经用完毕，请充值后使用`

已生成断点续刷清单：

- `data/ernie_refresh_pending_titles.txt`

额度补足后，可直接续刷剩余岗位：

```bash
cd backend
python scripts/refresh_job_profiles.py --profile-provider ernie --titles-file ../data/ernie_refresh_pending_titles.txt
```

结论：

- 当前“岗位画像是否由 ERNIE 实际生成”这一点已经从代码层面满足要求
- 当前未完成项不再是实现问题，而是 ERNIE 额度不足导致的批量任务中断

## 2026-04-20 再核对（团队标注样本）

本节用于覆盖前文中关于 `5, 30, 32, 43` 的旧状态判断。后续答辩与材料整理请以本节为准。

### 结论

`5, 30, 32, 43` 对应的“团队真实标注样本 + 正式准确率报告”已完成，不再属于未完成项。

### 已落地文件

1. 团队真实标注样本  
   - `data/evaluation_cases.team.json`
2. 正式准确率报告  
   - `exports/accuracy_report.team.json`
3. 草稿型自动标注样本（不作为最终提交口径）  
   - `data/evaluation_cases.real.json`

### 核对结果

1. `data/evaluation_cases.team.json`
   - `dataset_type = team_labeled`
   - `dataset_name = CareerPilot team labeled cases (anonymized real resumes)`
   - `owner = Team`
   - `cases = 10`
2. `exports/accuracy_report.team.json`
   - `case_count = 10`
   - `skill_accuracy = 91.0`
   - `key_info_accuracy = 100.0`
   - `overall_passed = true`
   - `competition_ready = true`
3. `data/evaluation_cases.real.json`
   - `dataset_type = real_auto_labeled_draft`
   - 该文件仅可作为内部草稿或补充说明，不应替代 `team.json`

### 状态更新

原先文档中“只差补团队真实标注样本并生成正式报告”的表述，现应更新为：

- 已完成团队真实标注样本整理
- 已生成正式准确率报告
- 当前准确率相关材料已具备提交与答辩使用条件

### 当前真正未闭环项

截至本次核对后，A13 项目剩余的主要未闭环项不再是准确率材料，而是：

1. ERNIE 全量岗位画像刷新受额度限制，当前仅完成部分岗位
2. 如需答辩版“全量岗位画像均由 ERNIE 生成”，需在补足额度后继续断点续刷
