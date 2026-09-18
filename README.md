# play-review-analysis

把几个月的 Google Play 评论熬成一套「可复现的 bug 知识库」——不是简单的评论分类统计，
而是把笼统、零散的用户反馈，聚合成能落地到"哪台机器、哪个版本、哪个文件"的具体复现坐标。

这是一个 [Claude Code Skill](https://claude.com/claude-code)：喂给 Claude 一批 Play Console
导出的评论 CSV，它按固定流水线跑出 6 张表的 Google Sheets 知识库，并能按需生成某个问题的
可执行复现步骤文档。

## 为什么做这个

测试看 Play 评论想找 bug，最常见的挫败是："视频播放卡顿"这种评论，没法复现，就没法定位，
问题就一直挂着。

但实测下来，这个判断不完全成立。在某个视频播放器 App 的 5 个月数据里（35734 条评论），
逐条人工核对后发现：

> 真正"确有问题但完全无从下手"的，只占有效低星评论的 **2.3%**。
> 绝大多数评论其实带着线索，只是**埋在 40 种语言的自然表达里，关键词挖不出来**。

所以这套流水线的核心不是"分类评论"，而是**把线索挖出来并让它们累积**：单条笼统评论是一个
没有坐标的信号点，同症状评论叠加后，元数据（机型/芯片/版本/地区）的交集就是复现坐标。
实测效果：「快进后卡顿」在某芯片平台上集中 **8.7 倍**；「记不住播放进度」7 条证据里 6 条
落在同一芯片族（**3.2 倍**）——按具体机型看毫无规律，按芯片族看立刻收敛。

## 快速开始

```bash
SKILL=~/.claude/skills/play-review-analysis

# 1. 初始化项目
mkdir -p ~/Projects/myapp-reviews && cd ~/Projects/myapp-reviews
python3 $SKILL/scripts/init_project.py --app MyApp --package com.example.myapp

# 2. 把评论 CSV（Play Console 导出，UTF-16）放进 raw/，按该 app 改 taxonomy.py 的分类词表

# 3. 跑完整流水线（首次自动新建 Google Sheets）
python3 $SKILL/scripts/run_all.py

# 4. 首次额外跑两个（写表头 + 格式化）
python3 $SKILL/scripts/init_tabs.py && python3 $SKILL/scripts/format_sheets.py
```

以后每月只需：把新 CSV 丢进 `raw/` → 重跑 `run_all.py`。

依赖：`gspread google-auth`，以及 Google Workspace 凭证。

## 产出的 6 张表

| 表 | 内容 | 谁维护 |
|---|---|---|
| 1_评论库 | 评论原文 + 机型/SoC/形态 + 多标签分类 + 置信度 + 线索标签 | 脚本 |
| 2_问题档案 | 问题实体：状态/主次证据/伴随度/四维集中度（不含复现步骤） | 脚本生成，人改状态 |
| 3_复现尝试记录 | 谁、用什么机型、试了什么、结果、★排除了什么 | 人工 |
| 4_历史BUG | 缺陷系统导出后映射进来 | 导入 |
| 5_分类词典 | 词表在线可读 | 脚本 |
| 6_月度趋势 | 版本×分类的密度，发现回归 | 脚本 |

设计上最反直觉的一点：**表2 故意不存"复现步骤"**。步骤随证据增长会变，存一份旧的反而误导
测试往错方向试；真正存档的是表3 里"这次排除了什么"，让每次新生成的步骤能接着走而不是原地绕圈。

## 目录结构

```
SKILL.md                  给 Claude 的完整操作说明（触发场景、流水线细节、六个关键设计）
scripts/                  流水线脚本（classify → build_issues → export_sheets → build_trends → upload）
references/
  ├─ gotchas.md              改词表前必读：正则陷阱、Sheets API 坑、子串误伤案例
  ├─ taxonomy-guide.md       怎么给新 app 建分类体系
  ├─ sheet-schema.md         6 张表的完整列定义与状态机
  └─ confidence-scoring.md   评分全链路：密度分→置信度→证据强度→状态，每步公式和阈值
assets/
  └─ taxonomy_template.py    分类词表模板，通用 7 类已内置
```

## 使用场景 / 边界

用在：评论分析、差评分类、"用户反馈太笼统复现不了"、从评论里挖 bug、把评论变成复现步骤、
问题档案、评论知识库、给另一个 app 建一套、历史 bug 接进来、"这个问题这期有没有变多"。

⚠️ 这是**月度沉淀**，不是**每日巡检**——如果要的是"今天新增了哪些差评""推送到 Telegram"
"生成差评日报"，那是另外的巡检类工具的活。这个仓库回答的是"这个问题到底怎么复现"，
不是"今天出了什么事"。
