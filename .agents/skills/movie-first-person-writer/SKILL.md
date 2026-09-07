---
name: movie-first-person-writer
description: Use when a film commentary project needs full-story understanding, narration perspective selection, or a production-ready commentary draft.
---

# 影视解说执笔

根据整部影片的因果链写可制作的解说文稿。支持第一人称、第三人称和影评式叙述；不把剧情摘要、视觉模型猜测或导演意图推断当作文稿事实。

## 前置条件

1. 读取 `AGENTS.md`、`INDEX_REPORT.md`、已有研究资料、项目状态和用户目标。
2. 只有索引已足以定位关键段落时才开始写作；关键事实不足时退回 `movie-index`。
3. 从头到尾理解剧情与结局，并反查会改变早期含义的反转。

## 叙述策略

- 第一人称：用户先确认叙述角色；只能写该角色当时已知或可合理推断的信息。
- 第三人称：明确剧透边界、信息释放顺序和观众预设。
- 影评式：区分影片事实、可回看的视听观察和作者观点；不把观点包装成导演唯一意图。

## 输出与修订

在 `projects/<project-slug>/` 输出：

```text
STORY_MAP.md
POV_BRIEF.md                 # 第一人称时必需；其他视角写叙述策略
script/NARRATION_DRAFT_01.md
script/NARRATION_DRAFT_02.md # 每次整体修订递增
```

- `STORY_MAP.md` 记录时间线、人物关系、身份变化、关键道具、信息揭露和待核实项。
- 草稿按叙事节拍组织，不按标点机械换镜。
- `movie-direct` 只提出事实、视角、剧透顺序和可实现性问题，不直接改写正文。
- 用户确认采用稿后，总导演在状态文件记录 `SCRIPT_CONFIRMED` 和文稿路径。之后任何改稿都新建编号稿，并重新确认。
