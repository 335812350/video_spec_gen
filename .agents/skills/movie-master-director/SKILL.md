---
name: movie-master-director
description: Use when a user wants to create, resume, revise, or review a film commentary project based on a feature film or long-form screen work.
---

# 影视解说总导演

这是 `film-commentary` 工作流的唯一入口。当前 Agent 持续承担影片理解、创意取舍和用户沟通；其他 movie skill 是同一主脑在不同阶段加载的专业规则，不是固定岗位或并行任务。

## 类型契约

```text
workflow_id: film-commentary
workflow_version: "1"
video_type: commentary
production_mode: script-led
```

适用于基于完整电影或长片素材的第一人称解说、第三人称剧情解说和影评式解说。高能混剪、单段简单裁切、没有旁白的素材集锦，以及产品、科普、访谈内容应转入各自工作流。

## 接管或新建项目

1. 读取仓库 `AGENTS.md`，确认 `film-slug`、`project-slug`、目标平台和交付目标。
2. 读取 `projects/<project-slug>/project.json`、已有 `edit-plan.md`、`video-spec.md` 和 `production/state.json`；没有项目时先与用户确认项目身份，再在 `projects/<project-slug>/` 建立工作文件。
3. 新影片先执行 `../video-spec-builder-personal/references/film-research-enrichment.md`，并保留资料来源于 `assets/<film-slug>/references/`。
4. 只复用已验证的本地分析和可用字幕。`assets/<film-slug>/analysis/` 只用于定位候选，关键剧情、动作、道具、身份变化和结局必须回看带声音的连续原片。
5. 使用本 skill 的 `templates/state.json` 建立轻量阶段记录。该文件只登记当前阶段、下一动作、已确认选择和采用文件路径；它不是全局状态框架，也不包含哈希或锁。

## 阶段顺序

```text
PROJECT_CONFIRMED
-> INDEX_READY
-> DRAFT_READY
-> SCRIPT_CONFIRMED
-> VOICE_CONFIRMED
-> NARRATION_READY
-> DIRECTING
-> SPEC_READY
-> SPEC_CHECKED
-> PREVIEW_RENDERED
-> USER_REVIEWED
-> FINAL_RENDERED
-> SECOND_REVIEWED
```

前六个阶段是探索与决策阶段，由总导演负责影片研究、素材盘点、故事地图、叙述视角、旁白草稿、音色试听和用户确认。它们可以保留候选片段、范围和待确认项，但不能把粗略计划当作正式渲染依据。

NARRATION_READY 只表示旁白和字幕已准备好，下一步必须加载 movie-direct 完成正式编导；不得直接运行 HyperFrames render。

- DIRECTING：按已确认的旁白和创意方向完成 Scene 级选镜。
- SPEC_READY：完整 edit-plan.md 和正式 video-spec.md 已生成。
- SPEC_CHECKED：movie-render-qa 的渲染前规格预检通过。
- PREVIEW_RENDERED：基于完整正式 spec 的 standard 预览已生成。
- USER_REVIEWED：用户完成预览判断并给出是否进入正式渲染的决定。
- FINAL_RENDERED：high 质量正式版本完成渲染和技术检查。
- SECOND_REVIEWED：movie-second-review 完成正式成片独立复看。

按当前阶段加载对应 skill：

- 索引与检索：`movie-index`
- 全片理解与文稿：`movie-first-person-writer`
- 试音、旁白和字幕时间：`movie-voice-tts`
- 文稿预审、选镜和剪辑计划：`movie-direct`
- 样片、渲染和技术检查：`movie-render-qa`
- 最终成片独立复看：`movie-second-review`

## 用户确认与阶段记录

- 叙述视角、核心观点、锁定文稿、入选音色、样片方向和最终成片都由用户确认。
- 文稿、音色或样片变更后，在 `production/state.json` 更新对应确认项和下一动作；不假定文件存在就等于被采用。
- NARRATION_READY 之后，只有 SPEC_CHECKED 才允许预览或正式渲染；预览必须使用完整 Scene 级方案。
- SPEC_CHECKED 之前发现创意、时间轴或素材映射问题，退回 movie-direct；渲染执行问题由 movie-render-qa 处理。
- 当前项目恢复时，不自动把旧的粗略 video-spec.md、剧情阶段表或少量长 clip 视为正式方案。
- 当前项目只允许总导演更新正式 `state.json`。复检 skill 只写审片记录。
- 不创建批量副导演、并行候选、后台运行或 console 任务。

## 交付边界

影视解说的正式交付仍然是：

```text
projects/<project-slug>/edit-plan.md
projects/<project-slug>/video-spec.md
projects/<project-slug>/hyperframes/
outputs/<project-slug>/render-vNNN.mp4
```

不得把 spec、旁白、预览或渲染结果写入 `assets/`，不得覆盖旧版本。


## 影片画面保护规范

影片原画面始终是影视解说的主视觉。标题、章节名、说明文字和必要字幕都可以直接叠加在影片上，但覆盖层必须服务于信息表达，不得把影片处理成背景板。

- 禁止用 box-shadow、text-shadow、filter: drop-shadow()、filter: blur()、backdrop-filter、发光、暗角或全屏/大面积渐变遮罩压暗、染色、模糊影片。
- 允许标题或字幕使用透明背景；为可读性可使用 1--2px 细描边，或贴合文字范围的局部半透明底板。
- 局部底板不得扩展为整屏、宽幅底带或持续性场景调色层；不得遮住人物脸部、关键动作、关键道具和叙事证据。
- 覆盖层默认 pointer-events: none，影片主体和原片声音保持可见、可听、未被 UI 阻断。
- 纯镜头转场可以直接作用于相邻影片素材；不得用额外黑幕、渐变、阴影或磨砂层伪装转场。
