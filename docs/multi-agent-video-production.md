# 多智能体批量视频生产方案

> 状态：架构建议，待实现
>
> 适用范围：批量生产多个视频，以及同一内容的多个文案、视觉和节奏变体。

## 1. 核心判断

当项目目标是批量生产很多视频和风格变体时，多智能体不是为了增加“智能体数量”，而是为了把生产流程拆成可并行、可验证、可重试的任务单元。

推荐的基本原则是：

1. 父智能体负责理解用户意图、锁定约束、分派任务、选择候选和最终裁决。
2. 子智能体只处理边界清晰的提案、审查或执行任务。
3. 最终的 `video-spec.md`、HyperFrames 组装结果和交付结论只能由父智能体或受控组装器写入。
4. 确定性问题交给程序检查，不用 LLM 代替 `ffprobe`、Schema 校验或 HyperFrames `lint/check`。
5. 每个子任务必须有明确输入、输出格式、文件归属、完成条件和失败处理方式。

多智能体的价值来自四件事：

- 上下文隔离：worker 只读取完成任务所需的事实和约束。
- 并行搜索：多个风格候选、独立素材分析和独立场景可以同时处理。
- 专门审查：由不同任务角色寻找生成者容易忽略的问题。
- 可追溯重试：失败时只重跑对应候选或场景，而不是整批重做。

## 2. 当前仓库基线

当前仓库已经有部分场景级子智能体设计，但还没有完整的批量编排层：

- [`console/server/codexRunner.js`](../console/server/codexRunner.js) 每次运行只启动一个 `codex exec --json` 进程。
- 控制台的 run 记录、进程 ID 和项目锁以单一父运行为中心，没有子任务 ID、子任务状态或并发合并协议。
- HyperFrames 技能已经定义了 frame worker、DISPATCH、WAIT、重派和无委托时的串行回退。
- `video-spec-builder-personal` 强调用户需求确认、事实分层和 spec 一致性，但没有独立的文案 worker 或 spec QA worker。
- 项目级锁意味着多个 worker 不能直接同时修改同一份权威 `video-spec.md`。

因此，下一步不是重写现有 HyperFrames worker，而是在其上游增加批量任务模型和受控合并层。

## 2.5 当前主要链路

结论：`video-spec-builder-personal` 是“上游规格编排” skill，负责把想法整理成逐镜头的 `video-spec.md`；HyperFrames 是下游渲染器。README 也明确描述为两个 skill 接力。[README.zh.md:35](E:/pyproject/video_spec_gen/.agents/skills/video-spec-builder-personal/README.zh.md:35)

主要链路：

1. **锁定影片与工作模式**  
   根据片名、`film-slug` 或路径确定目标，只读取对应的 `assets/<slug>/` 和 `projects/<slug>/`。[SKILL.md:28](E:/pyproject/video_spec_gen/.agents/skills/video-spec-builder-personal/SKILL.md:28)

2. **新影片先做资料补全**  
   新片必须先本地盘点，再做可追溯的联网检索；把来源状态和影片资料写入 `assets/<slug>/references/`，至少生成 `film-metadata.json`、`film-profile.md`、`story-context.md`。[SKILL.md:6](E:/pyproject/video_spec_gen/.agents/skills/video-spec-builder-personal/SKILL.md:6)

3. **分支处理**
   - 没有现有 spec：走 **0-1 模式**
   - 已有 `video-spec.md` 且要修改：走 **迭代模式**[SKILL.md:23](E:/pyproject/video_spec_gen/.agents/skills/video-spec-builder-personal/SKILL.md:23)

4. **0-1 模式五段流程**  
   视频基本盘 → 素材盘点 → 表达方式与节奏 → 视觉主题 → 参考与反例。每段都有硬指标，未满足就继续追问，不允许直接生成半成品。[workflow-0-1.md:12](E:/pyproject/video_spec_gen/.agents/skills/video-spec-builder-personal/references/workflow-0-1.md:12)

5. **拆分镜并校验**  
   按 `scene-breakdown` 拆到单镜头，每个 Scene 必须使用组件目录中的真实组件 ID，然后自检。[workflow-0-1.md:207](E:/pyproject/video_spec_gen/.agents/skills/video-spec-builder-personal/references/workflow-0-1.md:207)

6. **生成或更新 spec**  
   按模板和 `spec-rules` 写入或更新  
   `projects/<film-slug>/video-spec.md`，时长精确到 0.1 秒，缺失内容标 `[待补充]`。[workflow-0-1.md:220](E:/pyproject/video_spec_gen/.agents/skills/video-spec-builder-personal/references/workflow-0-1.md:220)

7. **交给 HyperFrames**  
   spec 完成后只提示用户是否执行 `/hyperframes`；新渲染版本写入 `outputs/<slug>/render-vNNN.mp4`，不会自动判断最终版。[SKILL.md:339](E:/pyproject/video_spec_gen/.agents/skills/video-spec-builder-personal/SKILL.md:339)

关于“是否有启动 agent”：

- **Skill 本身没有启动 agent。** 文档中没有 `spawn_agent`、`subagent`、启动脚本或 agent 编排配置。
- 它运行在当前的 Codex/Claude 等宿主 agent 中；`project-layout.md` 中“agent 可以写入 reference”只是权限说明，不是创建子 agent。[project-layout.md:19](E:/pyproject/video_spec_gen/.agents/skills/video-spec-builder-personal/references/project-layout.md:19)
- 联网搜索、HyperFrames 渲染是工具/下游流程，不等于启动子 agent。
- 本次回答过程中我额外启动了一个只读审阅 agent 来交叉核对文档；这是本次检查的临时行为，不属于该 skill 的内置链路。

## 3. 推荐架构

```text
用户目标 / 批次配置
          |
          v
父智能体（Director / Orchestrator）
  锁定事实、受众、平台、时长、批次矩阵和验收标准
          |
          +--> 共享素材与事实分析 Worker（一次，结果缓存）
          |
          +--> 文案 Worker x 风格数量（并行，输出候选）
          |
          +--> 文案评审 Worker（并行，排序和指出风险）
          |
          v
受控 Spec 组装器（唯一权威 spec 写入者）
          |
          +--> 确定性检查：Schema / 时间码 / 素材 / 路径 / lint / check
          |
          +--> Spec QA Worker（只读，输出问题报告）
          |
          +--> 场景规划与拆解 Worker（需要时）
          |
          +--> Frame Worker x 场景（并行，输出独立 composition）
          |
          v
渲染与版本管理
          |
          v
视觉 QA Worker + 交付检查
```

### 3.1 父智能体

父智能体是唯一的生产负责人，不负责亲自完成所有细节。它负责：

- 解析用户目标和批次要求。
- 确认受众、平台、时长、核心信息、事实边界和禁用项。
- 生成不可变的输入快照，供所有 worker 使用。
- 决定需要哪些风格、哪些候选进入渲染，以及哪些任务可以并行。
- 合并候选结果并解决冲突。
- 决定是否通过 QA、是否渲染和是否交付。

父智能体不能把未确认的用户偏好偷偷补进 spec。无法确认的创意假设应标为待确认，而不是让 worker 自行决定。

### 3.2 共享素材与事实分析 Worker

此 worker 只做一次，并将结果缓存到批次共享目录。适合处理：

- 本地视频、音频、字幕和分析 JSON 的盘点。
- 镜头时间码、角色和故事节点的证据整理。
- 外部资料的来源记录和事实分层。
- 可用素材、缺失素材和不可验证主张的清单。

输出只能写入 `references/` 或 `analysis/`，不能直接生成或覆盖权威 `video-spec.md`。

### 3.3 文案 Worker

每个 worker 绑定一个 `style_id`，接收相同的事实包和用户目标，只改变表达策略。输出候选文件，不直接修改最终 spec。

建议输出：

```json
{
  "style_id": "sharp-commentary",
  "variant_id": "sharp-commentary-01",
  "voiceover": [{
    "text": "...",
    "estimated_duration_s": 2.4,
    "fact_refs": ["story-context.node-03"],
    "inference": false
  }],
  "on_screen_copy": ["..."],
  "scene_intent": ["..."],
  "risks": ["..."],
  "word_count": 86
}
```

文案 worker 的职责是提出可剪辑的表达方案，而不是重新定义影片事实、受众或核心卖点。

### 3.4 风格配置

风格不应依赖“某个 agent 的人格”。应该使用可版本化的风格包：

```json
{
  "style_id": "sharp-commentary",
  "tone": "冷静、犀利、克制",
  "sentence_length": "short",
  "allowed_devices": ["contrast", "irony"],
  "forbidden": ["空泛鸡汤", "未经证实的断言"],
  "reference_examples": ["..."],
  "scoring": ["hook", "clarity", "editability", "factuality"]
}
```

这样可以稳定地复现风格、比较不同版本，并在后续修改风格时批量重跑，而不必更换 agent 身份。

### 3.5 文案评审 Worker

文案评审 worker 读取候选和统一评分标准，输出排序及问题，不改候选原文。建议评分维度：

- 是否准确表达核心信息。
- 是否适合目标平台和时长。
- 是否能被现有素材和 HyperFrames 表达。
- 句子长度、字幕密度和旁白节奏是否可剪辑。
- 是否存在事实越界、过度承诺或风格漂移。

父智能体根据评审报告选择一个或多个候选进入 spec 组装。

### 3.6 Spec 组装器

Spec 组装器是唯一的权威写入者。它把已选择的文案、用户已确认的约束、事实引用、镜头结构和设计决策写入：

```text
projects/<film-slug>/video-spec.md
```

候选文件和评审报告应保留在对应的批次或 run 目录中，便于追踪“哪个变体生成了哪个 spec”。

### 3.7 Spec QA Worker

Spec QA worker 只读检查，不直接修复文件。输出结构化报告，例如：

```json
{
  "status": "needs_revision",
  "findings": [{
    "severity": "high",
    "location": "scene-04.voiceover",
    "problem": "把编辑推断写成了影片事实",
    "evidence": "...",
    "suggestion": "改为明确标注为解读"
  }]
}
```

至少检查：

- 用户明确要求是否全部保留。
- 事实、推断和待核验内容是否分层。
- 每个镜头是否有素材或明确的视觉表达方式。
- 旁白、字幕和镜头时长是否相容。
- 是否引用了不存在的文件或不允许的外部素材。
- 是否违反 `spec-rules`、节奏规则或项目目录边界。
- 核心 takeaway 是否被变体内容稀释。

只有 QA 通过，或父智能体明确接受已记录的风险，任务才可进入组装和渲染。

### 3.8 Frame Worker 与视觉 QA

已经确认的多场景 spec 可以交给现有 HyperFrames frame worker。每个 worker 只拥有自己的场景文件和 motion sidecar，不能改邻居场景或根级组装。

渲染后再使用视觉 QA worker 检查截图或 contact sheet：

- 字幕和文字是否溢出或遮挡主体。
- 是否出现空白帧、黑屏或素材未加载。
- 构图、层级、节奏和转场是否稳定。
- 风格变体是否真正体现差异，同时保留品牌和事实一致性。

视觉 QA 也只输出报告。确定性渲染检查仍由 HyperFrames 工具负责。

## 4. 批量生产流程

### 阶段 A：建立批次

批次配置至少应包含：

- 一个共享事实包和素材清单。
- 一个基础用户目标。
- 风格列表和每种风格的变体数量。
- 平台、比例、时长范围和质量档位。
- 每个变体的验收标准。

批次应生成一个稳定的矩阵，例如：

```text
batch-001
  sharp-commentary / variant-01
  documentary      / variant-01
  restrained-brand / variant-01
  sharp-commentary / variant-02
```

### 阶段 B：共享分析

素材和事实分析只运行一次。所有文案 worker 读取同一份版本化快照，避免每个 worker 重复扫描文件、产生不同事实理解。

### 阶段 C：并行生成与评审

并行运行风格候选，再并行运行评审。评审完成后由父智能体选择 Top-K，而不是默认所有候选都渲染。

### 阶段 D：组装、检查和 QA

每个入选候选生成独立 spec。之后按以下顺序处理：

1. 结构化 Schema 和路径检查。
2. 时间码、字数和旁白时长检查。
3. HyperFrames `lint` / `check`。
4. Spec QA worker。
5. 通过后才生成场景和渲染。

### 阶段 E：渲染和选择

渲染输出必须使用递增版本号，不能覆盖已有文件。批次索引应记录：

```text
输入快照 -> 风格包 -> 文案候选 -> spec -> composition -> QA -> render-vNNN.mp4
```

## 5. 任务契约与并发边界

每个子任务都应有以下元数据：

```json
{
  "task_id": "copy-sharp-commentary-01",
  "parent_run_id": "run-...",
  "role": "copywriter",
  "input_snapshot": "...",
  "owned_outputs": ["candidates/sharp-commentary-01.json"],
  "status": "queued",
  "attempt": 1,
  "timeout_s": 600
}
```

必须满足：

- 输入快照不可变。
- worker 输出路径互不重叠。
- 只有一个 owner 可以写某个权威文件。
- 完成以预期 artifact 存在并通过基本校验为准，不只看进程退出码。
- 缺少 artifact 时允许有限次数重派。
- 父任务取消时向子任务传播取消。
- 记录模型、提示版本、风格包版本和来源引用。

当前项目级锁不支持多个 worker 直接并发写同一项目文件，因此第一版应采用“并行候选/报告，单点合并”的方式。

## 6. 何时使用、何时不使用

适合拆子智能体：

- 多个风格候选互相独立。
- 多个场景已经定稿，文件边界清楚。
- 素材分析可以共享和缓存。
- QA 有明确检查清单和结构化报告。
- 单个任务的工作量足以抵消启动上下文的成本。

不适合拆子智能体：

- 用户需求还没有锁定。
- 任务强耦合，后一个决策会不断推翻前一个决策。
- 只是简单的字段校验或媒体元数据读取。
- 短片只有少量场景，调度成本高于直接完成。
- 多个 worker 必须同时编辑同一份权威文件。

## 7. MVP 实现顺序

### MVP 1：批量文案与 Spec QA

先实现最有价值、风险最低的闭环：

```text
一次素材/事实分析
  -> 并行生成 3-5 个风格文案
  -> 文案评审
  -> 父智能体选择候选
  -> 单点生成 video-spec
  -> 确定性检查
  -> Spec QA
```

这一阶段先不让 worker 并发修改 HyperFrames 或权威 spec。

### MVP 2：批次运行与局部重试

为控制台增加：

- batch、task、parent-child 运行记录。
- 子任务状态、artifact、日志和错误。
- 并发上限、超时、取消传播和有限重试。
- 共享分析缓存。
- 候选、spec、QA 和 render 的 provenance 链。

### MVP 3：场景级并行

在 spec 已通过 QA 后，复用现有 frame-worker 协议进行场景并行。只有场景数量较多或单场景明显较重时才启用 fan-out；短片仍可串行构建。

### MVP 4：渲染后视觉 QA

把 contact sheet、关键帧和渲染元数据交给视觉 QA worker，生成可读的回归报告，并将问题关联到具体 scene 或 variant。

## 8. 成功指标

不要只统计“启动了多少 agent”。建议衡量：

- 从批次输入到首个可渲染候选的时间。
- 每个合格变体的平均 token、时间和渲染成本。
- QA 拦截的问题数量及严重级别。
- 候选到最终采用的通过率。
- 单个失败任务的局部重试比例。
- 不同变体之间的事实一致性。
- 渲染后发现的缺陷率。
- 结果是否能够追溯到输入快照、风格包和具体 worker。

最终目标不是让系统看起来“有很多 agent”，而是让批量生产具备更高的吞吐量、更低的返工率，以及可以解释和复现的决策链。
