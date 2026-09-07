---
name: movie-render-qa
description: Use when a film commentary project needs a HyperFrames sample or final render plus technical validation of an approved specification.
---

# 影视解说渲染与技术检查

只忠实执行已确认的 video-spec.md、edit-plan.md 和 HyperFrames 工程。这个 Skill 同时负责渲染前规格预检和渲染后的媒体技术检查；不负责重新设计镜头、文稿或叙事。

## 渲染前规格预检

1. 读取项目状态、采用文稿、旁白、字幕、`edit-plan.md` 和 `video-spec.md`。
2. 检查每个 Scene 的素材路径、源时间、成片时间、声音策略和所需组件是否可执行。
3. 确认输出目录使用 `outputs/<project-slug>/render-vNNN.mp4` 递增命名，不覆盖已有版本。
4. 若需要预览，先执行 `npx hyperframes preview --status`；只在没有可复用服务时使用 `npx hyperframes preview --no-open`，审阅结束后停止服务。
5. 确认 video-spec.md 使用当前模板的 9 个章节，并包含完整 Scene 级分镜和全部工作流身份字段。
6. 检查 edit-plan.md 与 video-spec.md 的总时长、Scene 编号、素材范围和声音策略是否一致。
7. 检查 Scene 时间轴连续、无空档、无重叠；源片路径存在，source_in / source_out 合法，旁白和声音事件有对应画面。
8. 检查是否仍有关键 [待确认]、粗略时间、缺失画面职责、被排除的旧项目或未授权素材引用。
9. 确认目标 HyperFrames 工程位于 projects/<project-slug>/hyperframes/，并基本对应正式 spec 的画面结构；输出编号不覆盖已有 outputs/<project-slug>/render-vNNN.mp4。
10. 将结果写入 projects/<project-slug>/RENDER_QA.md：使用 Pre-render: PASS 或 Pre-render: BLOCKED，并列出问题、Scene、责任归属和修复前提。

BLOCKED 时不得运行 HyperFrames render。创意、信息顺序、选镜或分镜缺口退回 movie-direct；路径、时间码、工程结构等执行问题由本 Skill 修复或报告。

预检通过后，先执行 npx hyperframes check。首次预览必须基于完整正式 spec，使用 standard 质量；启动预览前先执行 npx hyperframes preview --status，只有没有可复用服务时才启动 npx hyperframes preview --no-open。

## 渲染后技术检查

- 用户完成完整 standard 预览判断后，正式版使用 high，写入下一个递增 render 版本。
- 每次渲染前执行 `npx hyperframes check`；渲染后检查文件存在、时长、音视频流、画幅、帧率、字幕和明显黑帧或损坏。
- 渲染完成后不保留 preview 服务。

## 交付

在项目工作目录维护 RENDER_QA.md，同时记录 Pre-render checks、Post-render checks、采用的 spec、输出版本、执行的检查和阻断问题。技术通过不代表创意已获用户确认。


## 影片覆盖层静态与视觉检查

影视解说允许标题、章节名、说明文字和必要字幕叠加在影片上，但影片主体不得被样式处理成背景板。

- 静态检查阻断 box-shadow、text-shadow、drop-shadow、blur、backdrop-filter、发光、暗角、全屏/大面积渐变遮罩、磨砂层和填充型全屏 ::before/::after。
- 允许透明文字、1--2px 细描边，以及仅贴合当前文字范围的局部 rgba(...) 底板；底板不得形成固定底带或持续性场景调色层。
- 视觉检查至少覆盖一个桌面和一个移动视口：除文字、描边和局部文字底板外，影片不得整体压暗、染色、模糊或出现阴影遮挡感。
- 检查标题/字幕没有遮住人物脸部、关键动作、关键道具、原片字幕或其他叙事证据；覆盖层默认 pointer-events: none。
- 纯镜头之间的直接淡化/擦拭可保留，但不得叠加黑幕、渐变、阴影或磨砂层。
