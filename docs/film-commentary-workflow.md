# 影视解说工作流

> 状态：active
> 工作流 ID：`film-commentary`
> 版本：`1`
> 最后更新：2026-09-02

## 定位

`film-commentary` 用于基于完整电影或长片素材制作有旁白的影视解说、电影解说和影评式解说。它不是高能混剪，也不是通用影片素材编排的别名。

工作流由 `movie-master-director` 统一接管，并按需要加载索引、执笔、配音、编导、渲染和二次审片阶段 Skill。阶段 Skill 是同一主脑的工作模式，不创建固定岗位或并行任务。

## 产物与边界

```text
assets/<film-slug>/                 源片、字幕、分析和带来源的研究资料
projects/<project-slug>/            INDEX_REPORT、文稿、edit-plan、video-spec、HyperFrames 工程和审片记录
outputs/<project-slug>/             递增的 render-vNNN.mp4
```

正式交付继续使用统一 `video-spec.md`；`edit-plan.md` 是人工可审阅的剪辑计划。影视解说项目可使用 `projects/<project-slug>/production/state.json` 记录当前阶段、下一动作、已确认选择和采用路径，但它不包含 SHA-256、不建立全局 schema，也不要求其他工作流使用。

本工作流不生成 `visual_edit.json`、`audio_mix_plan.json` 或 `review_issues.json`。如未来出现自动消费者或确定性校验需求，再单独设计。

## 阶段与确认

```text
项目确认
-> 索引或复用分析
-> 全片理解与文稿
-> 编导预审
-> 用户确认文稿
-> 阿里云试音与旁白
-> movie-direct 完整分镜
-> movie-render-qa 渲染前预检
-> standard 全片预览
-> 用户审片
-> high 正式渲染
-> 独立复检
```

探索阶段由 movie-master-director 管理，可保留故事地图、候选片段、试听结果和待确认项；movie-direct 不包含探索/正式模式分支，只负责把已确认方向写成完整 Scene 级正式方案。
正式预览前必须完成 video-spec.md。movie-render-qa 先做规格可执行性预检，再执行 HyperFrames；技术检查和二次审片只发现问题，不能替代创意决定。
当前项目恢复时，若状态为 NARRATION_READY，下一步是 movie-direct，不是直接渲染。旧的剧情阶段表、少量长 clip 或粗略 spec 不自动视为正式分镜。

## 复用能力

- 配音：只使用 `tools/aliyun_tts.py` 和 `.agents/skills/aliyun-tts/`。
- 旁白时间戳：缺少可用时间信息时使用 `npx hyperframes transcribe`，并抽查中文专名与关键句。
- 渲染：HyperFrames `check`、受控 preview、render 和渲染后媒体检查。
- 影片研究：复用 `video-spec-builder-personal` 的研究资料流程，研究记录写入 `assets/<film-slug>/references/`。

## 上游来源与适配说明

本工作流的方法论改编自 [straighttttt/movie-commentary-workflow](https://github.com/straighttttt/movie-commentary-workflow)，采用的上游提交为 `3d50c1745ef2bc37a86919c5492603cdc22e49bb`，上游许可证为 Apache License 2.0。

本仓库保留其“单一总导演、原片证据优先、用户样片确认和独立复检”的原则，但已重写为当前项目的目录、`video-spec`、阿里云 TTS 和 HyperFrames 约定。未引入上游的 Fish Audio、MiniMax、火山 ASR、批量副导演、SHA-256 锁合同或专属 JSON 数据合同。
