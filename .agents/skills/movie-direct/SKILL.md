---
name: movie-direct
description: Use when a film commentary project needs script review, scene selection, audiovisual planning, or a reviewable edit plan and video specification.
---

# 影视解说编导

编导负责把已经确认的解说方向、旁白和影片证据编排成完整、可执行的 Scene 级导演方案。此 Skill 不包含探索模式分支，也不把粗略候选或阶段摘要当作正式分镜。

## 前置条件

1. 读取项目状态、INDEX_REPORT.md、STORY_MAP.md、旁白稿、旁白音频和用户已确认的叙述视角。
2. 确认旁白、基本时长、平台画幅、素材边界和声音方向已明确；未明确时退回总导演继续探索，不生成正式 spec。
3. 读取当前 video-spec-builder-personal 的 video-spec 模板和 spec-rules，沿用现有统一规格契约。

## 文稿预审

1. 读取项目状态、`INDEX_REPORT.md`、`STORY_MAP.md` 和候选文稿。
2. 只将事实错误、人物错认、第一人称越界、反转提前泄露、关键画面无法找到列为阻断项。
3. 把具体段落、原因和可回看的源片区间交回执笔，不直接覆盖文稿。

## 正式规划

- 文稿和音色已经由用户确认后，按约 8--15 秒的叙事节拍组织画面。
- 每段先判断观众需理解或感受的内容，再从字幕、索引和连续原片中挑选画面。
- 关键动作、对白、揭示、交接和身份变化必须回看带声音的连续原片。
- 原片接管只在对白、表演、动作或现场声音明显优于旁白复述时使用；接管期间停止重复旁白，登记准确源时间与替换范围。
- 明确旁白、原片对白、环境声、静默和 BGM 的关系，不让音乐淹没信息。

每个正式 Scene 必须记录：

- 成片起止时间；
- 对应完整旁白和屏显文案；
- 画面职责、构图和观众预期效果；
- 具体素材路径、source_in、source_out 和播放速率；
- 声音策略、动效要点、转场进入与离开；
- 素材依赖和必要的证据说明。

必须覆盖整条正式成片时间轴，Scene 之间无空档、无重叠，旁白、画面和声音策略能够相互对应。

以下内容不能作为正式分镜交付：

- 只有剧情阶段的摘要表；
- 只有源片大区间的证据映射；
- 只有 8 个或少量连续 HyperFrames clip 的粗工程；
- 只有旁白清单、没有画面职责和源时间；
- 关键字段仍保留未解决的 [待确认]。

## 交付

更新现有统一产物：

```text
projects/<project-slug>/edit-plan.md
projects/<project-slug>/video-spec.md
```

edit-plan.md 记录叙事结构、创意取舍、选镜理由和审阅说明；video-spec.md 是执行细节的权威文档，必须按当前模板完成 9 个章节和 Scene 级分镜。

正式交付门槛：

1. edit-plan.md 与 video-spec.md 的项目身份、总时长、Scene 编号和素材范围一致。
2. video-spec.md 包含 workflow_id、workflow_version、project_slug、source_film_slug、video_type 和 production_mode。
3. 所有 Scene 的时间轴、旁白、素材映射、声音策略、转场和素材依赖均已填写。
4. 正式规格完成后交给 movie-render-qa 做渲染前预检；预检未通过不得渲染。

movie-direct 不负责修改 HyperFrames 工程来掩盖规格缺口；工程应按通过检查的正式 video-spec.md 执行。


### 覆盖层与构图约束

- 标题、章节名、说明文字和必要字幕可以压在影片镜头上，不要求单独切出标题镜头。
- 叠加文字应避开人物脸部、关键动作、关键道具和观众必须读取的原片文字；优先选择画面中的真实留白区。
- HTML/CSS 不得加入阴影、暗角、模糊、发光、全屏半透明遮罩、大面积渐变或磨砂层来“托住”文字。
- 文字可用透明背景和 1--2px 细描边；确有可读性需要时，只允许紧贴文字边界的局部 rgba(...) 底板，且应短时出现、快速消失。
- 纯镜头转场只能直接处理相邻影片素材，不得通过额外覆盖层压暗或改变影片观感。
