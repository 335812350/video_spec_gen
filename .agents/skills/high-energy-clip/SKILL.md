---
name: high-energy-clip
description: Use when 用户明确要求高能片段、高能混剪、动作集锦或从正片提炼高潮片段。
---

# 高能混剪生产工作流

## 类型契约

```text
workflow_id: high-energy-clip
workflow_version: "2"
video_type: high-energy-clip
production_mode: asset-led
```

高能片段是以正片视频为主要内容的短片，不是影视解说，也不是把音量最大的镜头简单拼起来。成片应当让观众经历一条可辨认的能量曲线：引子、升级、爆点、回收。

首期默认：不生成旁白，保留原片声音；BGM、原片对白、环境声、字幕和是否静音由用户确认。源视频已内嵌字幕且用户确认满足要求时，字幕策略写为沿用源视频字幕，不重新生成 SRT；只有需要提取、重排或重新设计字幕时才转录。默认保持影片时间顺序，任何重排或重复使用都必须写入选择记录并由用户确认。

## 适用与不适用

适用：动作段、追逐、对峙、反转、情绪爆发、单角色高光、连续冲突和需要从长片中提炼观看入口的片段。

不适用：需要完整剧情解释的影视解说、以观点论证为主的影评、没有可用正片素材的概念宣传片、只想截取一个连续镜头且不需要重新编排的简单裁切。

## 进入条件

1. 由调度层传入 `workflow_id: high-energy-clip`；直接调用本 Skill 时也按该工作流记录。
2. 完成通用影片素材工作流的影片锁定；新影片先执行
   `../video-spec-director-dev/references/film-research-enrichment.md`。
3. 确认正片源文件位于 `assets/<film-slug>/`，保留用户原始路径。
4. 前期不把时长当作硬输入。用户给出的“约 xx 秒”只记录为 `duration_hint` 或软范围；如果用户没有时长偏好，记录为 `content-driven`。
5. 先读取已有 `assets/<film-slug>/analysis/`；没有候选分析时，先做不绑定目标时长的内容分析：

```bash
python tools/high_energy_analyzer.py analyze \
  --input assets/<film-slug>/<source>.mp4 \
  --out assets/<film-slug>/analysis/high-energy-candidates.json
```

分析器只提供源片 metadata、镜头、音频/切换等客观信号，不在内容未复核前承诺最终时长。先由 Agent 完成语义复核，识别可成立的叙事弧线、最小完整片段和可舍弃内容，再提出一个推荐时长或 2-3 个时长方案。只有用户确认方案后，才写入带 `target_duration_s` 的 selection，并生成正式 `edit-plan.md` 和 `video-spec.md`。

如果需要对白信号或片源对白字幕，先用 HyperFrames 生成词级 transcript JSON，再把它作为可选参数传入：

```bash
npx hyperframes transcribe assets/<film-slug>/<source>.mp4 --dir assets/<film-slug>/analysis
python tools/high_energy_analyzer.py analyze \
  --input assets/<film-slug>/<source>.mp4 \
  --target-duration <seconds> \
  --transcript assets/<film-slug>/analysis/transcript.json \
  --out assets/<film-slug>/analysis/high-energy-candidates.json
```
其中 `--target-duration` 是用户已确认时长后的可选筛选参数；探索阶段可以省略。

没有 transcript 不阻断纯画面/原声候选分析，但输出必须保留明确的缺失 warning；不要把缺失对白信号当成“没有对白”。

## 专属追问

只问公共流程还没有覆盖的维度：

- 高能重点是动作、冲突、反转、情绪爆发，还是某个角色。
- 需要单个完整事件，还是多个事件组成连续高潮。
- 是否保持时间顺序；如果重排，重排理由是什么。
- 原片对白、环境声和现场反应分别保留、压低还是移除。
- 是否加入 BGM；加入时是跟拍节奏还是只做氛围底。
- 是否需要片源对白字幕；字幕是整句、关键词还是关闭。
- hook 在开头使用哪一个源片段，高潮在哪个源片段，结尾是释放、悬停还是硬收。

以下问题在纯素材模式下默认跳过：TTS、旁白字数、真人出镜、3D 模型、数据图表和与正片无关的待搜索 B-roll。用户主动要求时才重新打开对应能力。

## 候选分析事实层

`high-energy-candidates.json` 至少包含 `source`、`shots[]`、`features`、`candidates[]`、`warnings` 和 `tool_versions`。候选中的时间码只能来自本地分析；影片剧情资料只能帮助语义判断，不能替代正片时间码。

候选排序综合镜头切换密度、音频峰值、视觉变化和可用的对白信号。缺少任一信号时必须在 `warnings` 中标明，并要求人工复核。候选字段：

```text
candidate_id
source_segments[]
estimated_duration_s
energy_score
signals[]
arc
selection_reason
warnings[]
```

用户确认时长和片段后写入 `assets/<film-slug>/analysis/high-energy-selection.json`，至少记录：源文件、候选 ID、最终片段顺序、每段 `source_in` / `source_out`、成片时间轴、最终 `target_duration_s`、`duration_decision`（`content_driven` / `user_fixed`）、`order_policy`、声音策略、字幕策略和确认时间。

在时长确认前，只允许输出分析结果、候选时长建议或临时审阅记录；不得把探索记录伪装成正式 `video-spec.md`。

选择文件生成后运行：

```bash
python tools/high_energy_analyzer.py validate \
  --selection assets/<film-slug>/analysis/high-energy-selection.json \
  --source-duration <seconds>
```

## edit-plan 约定

高能工作流的 `projects/<project-slug>/edit-plan.md` 必须可独立审阅，并包含：

- 源文件和分析文件引用。
- 候选列表、能量信号、语义判断和用户选择。
- 每个片段的源入点、源出点、成片入点、成片出点和能量等级。
- 原声、对白、环境声、BGM、字幕和静音策略。
- 引子、升级、爆点、回收的对应片段。
- 被舍弃候选及原因。

JSON 是机器事实和选择记录，`edit-plan.md` 是人工审阅层，最终 `video-spec.md` 是渲染执行层。三者不能互相替代。

## 分镜与 HyperFrames 映射

每个高能片段 Scene 必须写清：

```text
素材：assets/<film-slug>/<source>.mp4
源区间：125.4–127.1s
成片区间：0.0–1.7s
播放速率：1.0x
原声：保留
```

普通片段使用 `broll-footage.source-cut`，连续快剪段使用 `broll-footage.impact-montage`；文字片头/片尾使用现有 `broll-hero.big-type`。不使用 A-roll 旁白占位。

HyperFrames 组装时，画面使用带 `data-media-start` 的静音 `<video>`，原声使用时间和速率完全一致的独立 `<audio>`。源片段的时间裁切、分段和重排遵循 `hyperframes-core/references/creator-editing-recipes.md`，不在分析阶段提前重新编码正片。

## 专属验收

- 影片源文件、分析文件和选择文件路径真实存在。
- 每个源区间合法且没有越过影片总时长。
- 成片时间轴没有未说明的间隙、重叠或重复片段。
- 画面与原声的源起点、时长和播放速率一致。
- 前 3 秒内有明确 hook；高潮片段可在 `edit-plan.md` 中定位。
- 成片包含引子、升级、爆点、回收，或明确记录缺失的能量段及用户接受原因。
- 最终 selection 和 `video-spec.md` 的时间轴必须有明确总时长，且误差不超过 `±0.5s`；该校验针对分析后的最终决定，不针对用户最初的软时长偏好。
- `video-spec.md` 通过通用 spec 自检，再交给 HyperFrames `check`、snapshot 和 preview。

## 公共契约

- 使用 `../video-spec-director-dev/references/project-layout.md` 解析
  `assets/<film-slug>/`、`projects/<project-slug>/` 和 `outputs/<project-slug>/` 边界。
- 使用 `../video-spec-director-dev/templates/video-spec-template.md` 输出统一规格，至少记录
  `workflow_id`、`workflow_version`、`video_type`、`production_mode`、`project_slug` 和
  `source_film_slug`。
- 使用 `../video-spec-director-dev/references/spec-rules.md` 执行公共规格自检；本 Skill 的高能规则优先补充，不能被通用规则覆盖。
- 本 Skill 是独立主生产工作流，不作为 `video-spec-director-dev` 的内部类型模块展示。
