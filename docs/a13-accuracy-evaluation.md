# A13 准确率评估说明

本文件用于把项目里的准确率评估链路，整理成可直接给评委展示的口径。

## 1. 对齐企业答疑的评测口径

企业当前口径可归纳为两项：

1. 人岗匹配关键技能准确率不低于 80%
   - 随机抽取学生样本
   - 将岗位关键技能拆分为技能知识点
   - 对比学生真实掌握情况和系统匹配结果
   - 正确匹配率达到 80% 及以上
2. 岗位画像与学生画像关键信息准确率超过 90%
   - 关键信息重点看学历、专业、证书
   - 抽取匹配成功学生样本
   - 三项中只要有一项不符合，该样本即视为不合格

## 2. 当前项目提供的评估材料

项目里已经补齐了以下材料：

1. 评估脚本
   - [evaluate_accuracy.py](D:/OneDrive/Desktop/careerpilot%20(2)/careerpilot/backend/scripts/evaluate_accuracy.py)
2. 示例样本
   - [evaluation_cases.sample.json](D:/OneDrive/Desktop/careerpilot%20(2)/careerpilot/data/evaluation_cases.sample.json)
3. 团队真实样本模板
   - [evaluation_cases.template.json](D:/OneDrive/Desktop/careerpilot%20(2)/careerpilot/data/evaluation_cases.template.json)
4. 评估结果输出
   - [accuracy_report.json](D:/OneDrive/Desktop/careerpilot%20(2)/careerpilot/exports/accuracy_report.json)

## 3. 团队正式参赛时怎么用

建议直接复制模板文件，替换成你们自己的真实标注样本：

```bash
copy data\\evaluation_cases.template.json data\\evaluation_cases.team.json
```

然后把 `data/evaluation_cases.team.json` 中的每条样本替换为你们真实抽测数据。

建议至少准备：

1. `10` 条匹配成功学生样本
2. 其中至少 `3` 条用于重点展示关键技能匹配过程
3. 每条样本都写清楚：
   - 学生真实学历、专业、证书、技能
   - 岗位画像里的学历、专业、证书、关键技能
   - 系统实际输出的匹配技能
   - 人工核对后的 `expected_matched_skills`

## 4. 运行命令

```bash
cd backend
python scripts/evaluate_accuracy.py --cases ../data/evaluation_cases.team.json --report ../exports/accuracy_report.team.json
```

运行后会输出两层结果：

1. 指标结果
   - 关键技能匹配准确率
   - 关键信息合规率
   - 是否达到企业门槛
2. 参赛就绪提示
   - 是否仍在使用 sample 文件
   - 是否仍在使用 template 文件
   - 是否已标记为 `team_labeled`
   - 是否满足不少于 `10` 条样本

## 5. JSON 格式说明

每条样本的核心字段如下：

```json
{
  "student": {
    "name": "样本01",
    "education": "本科",
    "major": "软件工程",
    "skills": ["Java", "Spring Boot", "MySQL"],
    "certificates": ["英语四级"]
  },
  "job": {
    "title": "Java开发工程师",
    "education": "本科",
    "majors": ["软件工程", "计算机科学与技术"],
    "required_skills": ["Java", "Spring Boot", "MySQL"],
    "certificates": ["英语四级"]
  },
  "system_result": {
    "matched_skills": ["Java", "Spring Boot", "MySQL"]
  },
  "expected_matched_skills": ["Java", "Spring Boot", "MySQL"]
}
```

## 6. 答辩时建议怎么展示

建议在 PPT 或详细方案文档中放 3 部分：

1. 评测口径
   - 明确说明按企业答疑的 80% / 90% 标准执行
2. 样本来源
   - 说明样本来自团队真实抽测与人工标注
3. 评测结果
   - 贴出 `accuracy_report.team.json` 的核心结论
   - 再选 2 到 3 条样本做人工核验说明

## 7. 当前仍需团队补的最后一步

这条链路现在已经不是“没有评测能力”，而是“还差真实标注数据”。

也就是说：

1. 代码链路已补齐
2. 模板已补齐
3. 输出报告已补齐
4. 剩下的只是把你们团队真实抽测样本填进去
