---
name: movie-index
description: Use when a film commentary project needs to inspect, build, refresh, or query reusable evidence from a local feature-film source.
---

# 电影素材索引

为影视解说建立可定位、可复核的素材事实层。镜头分析、字幕、技术切点和视觉识别只帮助召回候选，不替代连续原片的创意与事实判断。

## 输入与复用

1. 读取 `AGENTS.md`、目标项目的 `project.json` 与 `production/state.json`。
2. 检查 `assets/<film-slug>/` 的权威正片、字幕和 `analysis/`。已有分析覆盖当前需求时优先复用，不重跑无关批次。
3. 分析缺口可写入 `assets/<film-slug>/analysis/`；研究资料写入 `assets/<film-slug>/references/`。不要把项目文稿、旁白或成片写入 assets。
4. 使用 `ffprobe`、本地字幕、HyperFrames 转录和既有分析定位候选；缺少工具或字幕时明确标记缺口，不把缺失当成没有内容。

## 索引要求

- 记录正片路径、可用时间范围、字幕来源和分析来源。
- 候选应包含精确源时间、人物、地点、动作、对白线索和不确定项。
- 对关键动作、道具交接、身份变化、反转和结局，导出或观看带合理前后余量的连续原片。
- 不把单帧、视觉模型描述或剧情摘要升级为确定事实。

## 交付

输出 `projects/<project-slug>/INDEX_REPORT.md`，至少说明：

- 可用源文件和字幕；
- 复用或新建的分析文件；
- 覆盖范围、已知缺口和检索方式；
- 关键剧情需要回看的证据范围；
- 能否进入文稿阶段。

总导演确认后将阶段更新为 `INDEX_READY`。
