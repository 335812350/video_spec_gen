<h1 align="center">Agent 驱动的视频生产平台</h1>

<p align="center">
  把模糊的视频想法，整理成可审阅、可渲染、可迭代的生产规格。
</p>

<p align="center">
  <img src="https://img.shields.io/badge/Agent--driven-workflow-2563EB?style=flat-square" alt="Agent-driven workflow">
  <img src="https://img.shields.io/badge/Python-3-3776AB?style=flat-square&logo=python&logoColor=white" alt="Python 3">
  <img src="https://img.shields.io/badge/Node.js-22%2B-339933?style=flat-square&logo=nodedotjs&logoColor=white" alt="Node.js 22 or newer">
  <img src="https://img.shields.io/badge/HyperFrames-render-111827?style=flat-square" alt="HyperFrames render">
</p>

<p align="center">
  <a href="#快速开始">快速开始</a> ·
  <a href="#当前支持范围">当前支持范围</a> ·
  <a href="#常用命令">常用命令</a> ·
  <a href="#项目目录">项目目录</a> ·
  <a href="#共享能力">共享能力</a> ·
  <a href="#文档">文档</a>
</p>

> [!NOTE]
> 本项目负责把需求编排成可执行规格，HyperFrames 负责把准备好的素材组装并渲染成视频。它不是拍摄工具，也不会替用户决定核心观点。

这是一个把“我想做一个视频”的模糊想法，逐步整理成可审阅、可渲染、可迭代视频规格的项目。

它的核心产物是 `video-spec.md`：其中明确视频目标、受众、平台、时长、叙事结构、文案、素材、声音、字幕、镜头时间轴和验收要求。HyperFrames 再读取这份规格，把已准备好的素材组装成视频。

## 核心能力

- 从零梳理视频目标、受众、平台和交付约束；
- 根据目标、素材和视频类型选择生产工作流；
- 盘点素材，补充研究资料，识别素材缺口；
- 生成或迭代 `edit-plan.md` 和 `video-spec.md`；
- 调用阿里云 TTS、媒体检索、转录、字幕、音频混音和 HyperFrames；
- 对规格、时间轴、素材路径和渲染产物执行检查。

## 当前支持范围

当前已注册的主生产工作流：

| workflow_id | 适用场景 |
|---|---|
| generic-video | 只提出主题、素材或目标，还没有确定视频类型 |
| film-material | 基于影视正片、字幕或已有片段进行项目化编排 |
| film-commentary | 基于完整电影或长片素材的影视解说、电影解说和影评式解说 |
| high-energy-clip | 高能混剪、爆点剪辑、节奏强化和动作集锦 |

知识科普、产品测评、访谈切片、音乐视频和互动视频等目前尚未注册为独立工作流。使用这些方向时，系统会说明边界，并在确认后采用最接近的通用工作流回退，不会宣称它们已经原生实现。

> [!WARNING]
> 未注册的视频类型不会被自动包装成“已支持”能力。需要使用这些方向时，请先确认兼容回退方案和交付边界。

## 工作流程

平台的默认链路是：

用户描述目标和素材 → 调度层选择工作流 → 工作流追问、研究和拆分镜 → 生成 `edit-plan.md` 与 `video-spec.md` → 规格检查 → HyperFrames 预览和渲染 → 用户审片与迭代。

推荐从 Agent 中直接描述需求，而不是先填写表格。例如：

```text
我想用一部电影的素材做 60 秒竖屏高能混剪，发布到抖音，保留原片对白，不要旁白。
```

调度层会识别目标并选择已注册工作流。用户仍需确认核心观点、素材授权、平台、重要取舍和最终审片结果。

## 环境准备

- Codex、Claude Code 或其他兼容本项目 Skill 的 Agent 环境；
- Python 3；
- Node.js 22 或更高版本；
- HyperFrames CLI；
- FFmpeg 和 FFprobe；
- 阿里云 TTS（可选）需要百炼 Workspace 的 API Key。

HyperFrames 的安装和运行要求以 [HyperFrames CLI Skill](.agents/skills/hyperframes-cli/SKILL.md) 为准。项目内的 Skill 位于 `.agents/skills/`，无需重复实现已经存在的能力。

## 快速开始

### 1. 从零规划视频

在 Agent 中描述：

```text
我想做一个三分钟的产品演示视频，发在 B 站，素材包括产品录屏和一段配音。
```

按对话完成目标、类型、结构、视角、文案、素材和节奏确认。完成后，项目中应有：

- `edit-plan.md`：可审阅的内容拆解和剪辑计划；
- `video-spec.md`：交给执行和渲染层的统一规格。

### 2. 做高能混剪

明确说明高能混剪、动作集锦或爆点剪辑，系统会进入 `high-energy-clip` 工作流，并分析候选片段、节奏和声音策略。

也可以查看分析工具的参数：

```powershell
python tools/high_energy_analyzer.py analyze --help
python tools/high_energy_analyzer.py validate --help
```

### 3. 做影视解说

明确说明要制作影视解说、电影解说或影评式解说时，系统会进入 film-commentary 工作流：先理解完整影片和用户的叙述视角，再生成可审阅的文稿、旁白、剪辑计划、规格和样片。配音统一使用阿里云 TTS，正式渲染前仍由用户确认文稿、音色和样片方向。

### 4. 迭代已有规格

如果项目中已经有 `video-spec.md`，直接描述修改目标：

```text
第三个镜头节奏太快，放慢一点；背景音乐换成更安静的版本。
```

工作流会先判断影响范围，再更新受影响的规格和分镜。

### 5. 预览和渲染

规格确认后，在 HyperFrames 项目目录执行：

```powershell
npx hyperframes check
npx hyperframes preview --no-open
npx hyperframes render --quality high --output outputs/<project-slug>/render-v001.mp4
```

预览服务器遵守仓库约定：启动前先检查现有服务，默认复用 3002 端口；审阅结束后停止预览服务。渲染完成后还要检查文件、时长、音视频完整性、画幅、帧率和字幕。

## 阿里云 TTS（可选）

复制示例配置到仓库根目录，并只在本地填写密钥：

```powershell
Copy-Item .env.example .env.local
```

然后在 `.env.local` 中填写 `DASHSCOPE_API_KEY`。`.env.local` 不得提交到 Git，也不要把密钥写入 Markdown、日志、manifest、spec 或聊天记录。

常用入口：

```powershell
python .agents/skills/aliyun-tts/scripts/aliyun_tts.py models
python .agents/skills/aliyun-tts/scripts/aliyun_tts.py voices --model voice-enrollment --target-model <model>
python .agents/skills/aliyun-tts/scripts/aliyun_tts.py synthesize --model <model> --voice <voice> --text "你好，欢迎使用。" --out projects/<project-slug>/voice.mp3
python .agents/skills/aliyun-tts/scripts/aliyun_tts.py clone --target-model <model> --prefix <name> --audio-url <url>
```

模型、voice ID、权限和配额必须运行时查询。`qwen-audio-*`、`cosyvoice-*` 和 `qwen3-tts-*` 的协议与音色规则不同，复刻音色必须与后续合成的目标模型完全匹配。详见 [阿里云 TTS CLI](docs/aliyun/tts-cli.md) 和 [阿里云 TTS Skill](.agents/skills/aliyun-tts/SKILL.md)。

## 项目目录

```text
assets/<film-slug>/              用户提供的源视频、音频、字幕、图形和参考资料
assets/<film-slug>/references/  研究资料、来源 URL 和摘录
projects/<project-slug>/        一个独立交付项目的 spec、分镜、工程和运行记录
outputs/<project-slug>/         递增版本的 render-vNNN.mp4
```

不同视频类型、平台、时长或音频策略应使用不同的 `project-slug`。`project.json` 用 `source_film_slug` 关联共享影片素材。

不要把 `video-spec.md`、`edit-plan.md`、预览、渲染视频或生成音频写入 `assets/`；不要覆盖原始素材、历史规格、manifest 或渲染版本。

## 共享能力

TTS、字幕、转录、BGM、SFX、媒体处理、动画、关键帧、转场、音频混音和渲染检查都属于可复用能力，不是额外的顶层工作流。

新增工作流时：

1. 先查 [共享能力与资源目录](docs/共享能力与资源目录.md)；
2. 读取对应 Skill 和工具文档；
3. 复用现有入口并保留来源、版本和 metadata；
4. 现有能力确实不足时，再新增工具或 Skill；
5. 最终仍映射到统一 `video-spec` 契约。

## 限制与用户责任

- Agent 可以自主编排流程，但不会替用户决定核心观点、事实立场和最终取舍；
- 用户负责确认受众、平台、素材授权、品牌边界和最终成片；
- HyperFrames 负责把准备好的素材、文字、音频和动效组装并渲染，不会凭空生成实拍镜头；
- 没有合适素材时，系统只能标记缺口或提出生成/检索建议；
- 未注册的视频类型不能仅因为底层工具存在，就被视为已实现的原生工作流；
- 当前账号可用模型、音色、provider 和本机依赖可能变化，以运行时检查为准。

## 文档

- [平台总设计](docs/Agent驱动的自主视频生产平台总设计.md)
- [当前架构图](docs/自主视频生产平台当前架构图.md)
- [共享能力与资源目录](docs/共享能力与资源目录.md)
- [工作流注册表](.agents/skills/video-production-dispatcher/references/workflow-registry.md)
- [影视解说工作流](docs/film-commentary-workflow.md)
- [video-spec-director-dev 中文 README](.agents/skills/video-spec-director-dev/README.zh.md)
- [阿里云 TTS CLI](docs/aliyun/tts-cli.md)

## 许可证

仓库内各 Skill 的许可证和使用条件以对应目录中的 LICENSE 或 NOTICE 文件为准。
