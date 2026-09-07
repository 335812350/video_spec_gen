# RENDER_QA

## Pre-render: PASS

检查日期：2026-09-03

本次执行 movie-render-qa 的渲染前规格预检与 HyperFrames check；没有启动 preview 或 render。

## 规格核验

- 项目身份一致：workflow_id 为 film-commentary，project_slug 为 nianhui-bunengting-commentary，source_film_slug 为 annual-meeting。
- 正式 video-spec.md 使用 9 个章节，包含 57 个 Scene；Scene 01–57 连续覆盖 0.0–670.0s，无空档、无重叠。
- 每个 Scene 均含类型、组件、完整旁白、屏显文案、画面职责、预期效果、画面描述、动效、音效、转场、源时间映射、声音策略与素材依赖。
- 正片、v003 旁白、v003 SRT、正式 edit-plan.md 和 HyperFrames 工程均存在。
- 旁白为 generated/voiceover/v003/narration.mp3，时长 655.968s，MP3/24kHz/单声道；56 条字幕 cue 对应 0.0–656.0s；Scene 57 另有 656.0–670.0s 片尾余韵。
- 输出目录没有已有 render-vNNN.mp4，后续首次预览输出可使用 render-v001.mp4 的预览命名，不覆盖历史版本。

## HyperFrames 核验

- 旧的 8 段粗时间轴已废弃。
- 现工程使用 61 个静态源片窗口实现正式 57 Scene；Scene 41、45、51 的多段源片按正式 spec 拆分为独立窗口。
- 现工程挂载 1 条主旁白、13 条关键原片声音窗口和 56 条 SRT 驱动的字幕 cue。
- npx hyperframes check 在 0、39、122、215、330、435、486、550、656 秒采样通过：lint 0 error / 0 warning，runtime 0 error，layout 0 issue，contrast 10/10 通过。
- 已生成关键快照：hyperframes/snapshots/frame-00-at-0.0s.png、frame-01-at-122.0s.png、frame-02-at-330.0s.png、frame-03-at-486.0s.png、frame-04-at-656.0s.png。
- Studio 审阅服务已启动并返回 HTTP 200：http://localhost:3002/#project/hyperframes。该服务仅用于审阅，不代表已生成 MP4。

## 观察项

- v003 narration.srt 是根据旁白段落长度生成的估算时间轴。工程已使用该字幕；standard 预览时优先抽查人名、错调、广进计划、检举视频、Rap、董事长承诺等 cue 首尾。该项不阻断生成 standard 预览。
- 正片源含稀疏关键帧。正式 render 前如出现 seek 冻帧，应预处理为短 GOP 的 H.264 派生片，不修改权威源文件。

## 结论

项目达到 SPEC_CHECKED。允许下一步生成基于完整正式 spec 的 standard 预览，之后由用户决定是否进入 high 正式渲染。


## Post-render: PASS (2026-09-03)

- Output: outputs/nianhui-bunengting-commentary/render-v001.mp4
- Duration: 670.000s (11m10s), exactly 20,100 frames at 30fps.
- Video: H.264, 1920x1080, 30fps, 16:9.
- Audio: AAC-LC, 48kHz stereo, 670.000s.
- File size: 426,859,524 bytes.
- Full FFmpeg decode pass completed with no errors.
- HyperFrames capture completed all 20,100 frames with browser GPU enabled (NVIDIA RTX 4060 detected).
- HyperFrames final packaging stalled after capture; the completed frames and mixed audio were directly muxed with FFmpeg into the same approved output. No source film or legacy project was modified.
- Preview service is stopped after rendering.

## Final state

- production/state.json is FINAL_RENDERED.
- Latest render: render-v001.mp4.
- Optional next step: independent timecoded second review.


## Post-render v002: PASS (2026-09-03)

- Output: outputs/nianhui-bunengting-commentary/render-v002.mp4
- Update: chapters 01-05 now use transparent backgrounds instead of the full-screen rgba(11,13,15,.88) overlay.
- Duration: 670.000s (11m10s), 20,100 frames at 30fps.
- Video: H.264, 1920x1080, 30fps, 16:9.
- Audio: AAC-LC, 48kHz stereo, 670.000s.
- File size: 430,375,919 bytes.
- Full FFmpeg decode pass completed with no errors.
- Pre-render HyperFrames check: 0 lint errors, 0 runtime errors, 0 layout issues, 0 motion errors, contrast 10/10.
- Preview service is stopped after rendering.

- production/state.json latest_render is render-v002.mp4.


## Source overlay audit (2026-09-04)

- Audited all project HTML/CSS fragments; only hyperframes/index.html contains visual overlay CSS.
- Removed the global wash footage darkening layer.
- Removed the full-screen chapter-card background for all title/chapter cards, including chapter 06 and the opening title card.
- Removed the heavy caption text-shadow layer.
- Retained root and film stage black solely for the source film 2.40:1 letterbox area; it is not an overlay.
- Static source audit complete; E:\\Temp was verified writable and the updated HyperFrames check/render completed.
- Latest rendered artifact is render-v003.mp4.


## Post-render v003: PASS (2026-09-04)

Output: outputs/nianhui-bunengting-commentary/render-v003.mp4
Update: removed the global footage wash, all full-screen chapter-card masks, and the heavy caption text shadow across the HyperFrames composition.
HyperFrames pre-render check: 0 lint errors, 0 runtime errors, 0 layout issues, 0 motion errors, contrast 10/10.
Duration: 670.000s (11m10s), 20,100 frames at 30fps.
Video: H.264, 1920x1080, 30fps, 16:9.
Audio: AAC-LC, 48kHz stereo, 670.000s.
File size: 478,927,503 bytes.
Full FFmpeg decode pass completed with no errors.
Browser GPU: NVIDIA RTX 4060 detected; HyperFrames temporary files used E:\\Temp.
HyperFrames capture completed all 20,100 frames; final MP4 was directly packaged from the completed capture and mixed audio after the known HyperFrames packaging stall.
Preview service and render workers are stopped after delivery.
