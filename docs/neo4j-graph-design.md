# Neo4j 图谱设计

## 节点类型

- `Job`
- `Skill`
- `Certificate`
- `Industry`
- `Company`
- `Capability`

## 关系类型

- `REQUIRES`
- `RELATED_TO`
- `PROMOTES_TO`
- `TRANSITIONS_TO`
- `BELONGS_TO`
- `SIMILAR_TO`

## 图谱建模规则

1. `Job -[:REQUIRES]-> Skill`
2. `Job -[:REQUIRES]-> Certificate`
3. `Job -[:BELONGS_TO]-> Industry`
4. `Job -[:PROMOTES_TO]-> Job`
5. `Job -[:TRANSITIONS_TO]-> Job`
6. `Job -[:REQUIRES]-> Capability`
7. `Job -[:SIMILAR_TO]-> Job`

## 查询支持

- 查询某岗位的上游/下游岗位
- 查询岗位晋升路径
- 查询岗位转岗路径
- 查询岗位核心技能
- 查询岗位之间技能差异

## 演示图谱样例

- `前端开发工程师 -> 高级前端工程师 -> 前端架构师`
- `前端开发工程师 -> 全栈工程师`
- `测试工程师 -> 测试开发工程师 -> QA 负责人`
- `数据分析师 -> 数据产品经理`

