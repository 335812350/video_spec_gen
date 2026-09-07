---
name: movie-second-review
description: Use when a finished film commentary render needs an independent, timecoded viewing review before the project is marked complete.
---

# 影视解说二次审片

独立复看已经渲染的成片，依据观众实际看到和听到的结果提出可定位的问题。它不修改文稿、剪辑计划、HyperFrames 工程、渲染文件或项目状态。

## 前置条件

1. 读取项目状态、采用的 `video-spec.md`、`RENDER_QA.md`、最终 render 和字幕。
2. 仅在 `FINAL_RENDERED` 后开始；路径或版本不明确时先报告，不猜测哪一版是最终采用版本。
3. 新建 `projects/<project-slug>/review/<render-version>/SECOND_REVIEW.md`，不覆盖历史审片记录。

## 两遍观看

- 第一遍：从头到尾正常速度、带声音完整观看，记录观众感到突兀、难懂或情绪断裂的时间点。
- 第二遍：复查所有切点和第一遍问题，特别检查开头、剧情揭示、原片接管、高潮、结尾、字幕遮挡、音频接缝、闪白、跳画面和小于 1 秒的后期新增镜头。

## 记录与回交

每个阻断问题必须包含时间窗、现象、预期观看结果、相关 Scene 或源区间，以及责任方向：

- 文稿、信息顺序或镜头选择：交回 `movie-direct` 或执笔阶段；
- 渲染偏离已确认方案、音视频故障或字幕错位：交回 `movie-render-qa`；
- 不影响理解的改善建议：标记为建议，不阻止交付。

总导演审阅记录并更新轻量状态；二次审片通过不替代用户的最终创意判断。
