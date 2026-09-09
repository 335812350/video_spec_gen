# Coocaa Video Skills

面向业务用户的视频创作 Skill Pack。安装后，用户可以新建一个空文件夹，让 Codex 自动初始化视频工作区，并根据素材生成或迭代 `video-spec.md`。

## 两个 Skill 分别做什么

这个 Skill Pack 里有两个能力，分别负责视频制作的“搭工作台”和“写分镜脚本”。

### `video-workspace`：初始化工作区

负责把一个空文件夹变成规范的视频创作工作区。它不关心你要做什么视频，只负责创建固定目录、复制模板和检查本机环境：

- 创建 `assets/`、`projects/`、`outputs/`、`.codex-tmp/`
- 复制 `setup` / `doctor` 脚本和 `.env.example`
- 检查 Node.js、npm、FFmpeg 等基础工具
- 告诉用户素材、项目文件和最终视频分别放在哪里

一句话：**它是“搭工作台”的 Skill，只在你第一次使用一个文件夹时需要。**

### `video-spec-director`：编排视频分镜

负责从想法、素材和目标出发，通过编导式追问生成可执行的 `video-spec.md`：

- 0-1 模式：从模糊想法开始，追问目标、受众、平台、时长、旁白、字幕、风格
- 迭代模式：修改已有 spec，如换镜头、调节奏、改字幕、换配音
- 盘点素材，必要时补全影片研究资料
- 输出精确到镜头和秒的分镜脚本，供后续渲染使用

一句话：**它是“编导/导演”的 Skill，负责把想法变成 `video-spec.md`，但不负责最终渲染。**

两者关系：

```text
video-workspace      搭好工作区
        ↓
video-spec-director  生成 / 迭代 video-spec.md
        ↓
HyperFrames          渲染成视频
```

## 前置要求

### 必需

- **Node.js 22+**：HyperFrames 需要
- **FFmpeg**：视频处理

## 安装

### 安装两个业务 Skill

第一个是视频工作区初始化（用一次就行）
第二个是视频剪辑导演的skill

```powershell
npx skills add https://github.com/335812350/video_spec_gen --skill video-workspace --agent codex --copy --yes
npx skills add https://github.com/335812350/video_spec_gen --skill video-spec-director --agent codex --copy --yes
```

### 安装 HyperFrames（渲染必需）

```powershell
npx skills add heygen-com/hyperframes
```
HyperFrames 是渲染必需。安装后 Codex 可以调用它进行预览和渲染。

## 配置

### API Key（可选）

`.env.local` 中配置：

```bash
# 阿里云 DashScope / Model Studio，用于 AI 配音
# 不填写时使用免费的 Edge TTS（机器味较重）
DASHSCOPE_API_KEY=
```

获取方式：阿里云百炼平台 → API-KEY 管理

## 使用方法

以下是一次完整制作的操作流。每一步都会写清楚：你对 Codex 说什么、Codex 会做什么、生成什么文件、这些文件有什么用。

> 触发方式有两种：让 Codex 根据描述自动匹配 Skill，或在消息里直接引用技能。以下每一步都给出两种写法；更确定时优先用 `$技能名` 直接引用。

### 第 1 步：初始化工作区

新建一个空文件夹并用 Codex 打开后，对 Codex 说：

```text
把当前文件夹初始化成视频创作工作区
```

更直接的方式是引用技能：

```text
$video-workspace 把当前文件夹初始化成视频创作工作区
```

两种方式效果相同。

Codex 会触发 `video-workspace`，创建这些目录：

```text
assets/<film-slug>/          输入素材目录，按源影片或主题命名
projects/<project-slug>/     视频项目目录，存放 spec、edit-plan、project.json、HyperFrames 工程
outputs/<project-slug>/      最终视频输出目录，保存 render-v001.mp4、render-v002.mp4 等
.codex-tmp/                   临时文件目录，任务结束后清理
```

同时复制这些脚本和模板：

```text
setup.ps1 / setup.sh          初始化工作区环境
doctor.ps1 / doctor.sh        检查 Node.js、FFmpeg 等依赖
.env.example                   配置模板，复制为 .env.local 后填写 API Key
```

Codex 会自动运行 `doctor`，告诉你缺什么环境，并询问是否安装。

### 第 2 步：放入素材

把源素材放到 `assets/<film-slug>/`。`film-slug` 是你为这批素材起的英文目录名，例如：

```text
assets/
└─ product-launch/
   ├─ source.mp4
   ├─ voice.wav
   ├─ logo.png
   └─ references/
```

素材不需要一开始就齐全，可以先放核心素材。`video-spec-director` 会在追问时帮你盘点。

### 第 3 步：生成 edit-plan.md 和 video-spec.md

Codex 会先生成可审阅的编辑计划：

```text
projects/<project-slug>/edit-plan.md
```

`edit-plan.md` 记录：

```markdown
项目定位：成片规格、目标、语气、视觉主题
叙事结构：区段划分、各段职责、总时长
叙事弧线：钩子、主线、视角、收束
素材现状：已有素材、必须补齐项、授权状态
版本选择：如同一项目有多个可选版本
开放问题：尚未确认、需要人工审阅的事项
```

它是“创意与剪辑决策记录”，用于让你先审叙事结构和素材取舍；确认后才生成正式 `video-spec.md`。


对 Codex 说：

```text
我想用 assets/product-launch 里的素材做一条 60 秒、16:9 的产品宣传视频
```

更直接的方式是引用技能：

```text
$video-spec-director 我想用 assets/product-launch 里的素材做一条 60 秒、16:9 的产品宣传视频
```

两种方式都会触发 `video-spec-director`，开始编导式追问。


```text
视频目的：营销 / 科普 / 教学 / 产品演示 / 品牌
目标受众：年龄、职业、观看场景
平台：视频号 / 抖音 / B站 / YouTube
时长：固定值或范围，如 60 秒 / 45-60 秒
核心信息：一句话 takeaway，不超过 12 字
旁白：AI 配音 / 真人录音 / 无旁白
字幕：整句 / 关键词高亮 / 逐词出现
视觉主题：HyperFrames 预设或自定义 design.md
```

Codex 会根据你的回答生成：

```text
projects/<project-slug>/video-spec.md
```

这个文件包含：

```markdown
## 1. 视频基本盘
   项目身份、目标、受众、平台、规格
## 2. 叙事结构
   节拍、情绪曲线、音画关系
## 3. 表达手段
   字幕、关键词强调、动效、3D、转场
## 4. 视觉规范
   主题、accent 色、装饰密度
## 5. 素材清单
   已有素材、待生成素材、待搜索素材
## 6. 分镜表
   Scene 01 到 Scene N，每个镜头的时间、画面、旁白、组件
## 7. 音频
   旁白、BGM、音效
## 8. 交互/呈现
   如有
## 9. 自检清单
   渲染前的完整性检查
```

`video-spec.md` 是整条流水线的核心：它描述“这条视频要怎么做”，后续 HyperFrames 根据它生成可渲染的工程。

### 第 4 步：确认和修改 edit-plan.md 与 video-spec.md

生成后，Codex 会提示你：

```text
projects/<project-slug>/video-spec.md 已生成。
接下来是否启动 HyperFrames 生成视频？
```

先不要急着渲染，先看并确认 `edit-plan.md` 和 `video-spec.md`。如果需要修改，你可以说：

```text
把第 2 个镜头节奏改快一点
```

```text
字幕改成逐词出现，不要整句弹出
```

```text
把开头 3 秒改得更有冲击力，先给结论
```

Codex 会进入迭代模式，只改对应段落，不会整段覆盖 `video-spec.md`。

### 第 5 步：生成 HyperFrames 工程

spec 确认后，对 Codex 说：

```text
根据 projects/<project-slug>/video-spec.md 生成 HyperFrames 工程
```

Codex 会读取 `video-spec.md`，在项目目录下生成：

```text
projects/<project-slug>/hyperframes/
├─ hyperframes.json          HyperFrames 项目配置
├─ index.html                主时间线 / 场景编排
├─ meta.json                 项目元信息
├─ package.json              依赖和脚本
└─ assets/                   工程内使用的素材引用
```

这个工程是把 `video-spec.md` 转成可渲染的 HTML 动画项目。

### 第 6 步：预览视频

对 Codex 说：

```text
预览 projects/<project-slug>/hyperframes
```

Codex 会运行：

```powershell
npx hyperframes preview --background
```

然后给你一个本地预览 URL。你在浏览器里检查画面、节奏、字幕和素材是否正确。

看完后可以让 Codex 停止预览：

```text
停止预览
```

### 第 7 步：渲染最终视频

确认预览没问题后，对 Codex 说：

```text
渲染 projects/<project-slug>/hyperframes 到 outputs/<project-slug>/render-v001.mp4
```

Codex 会运行类似：

```powershell
npx hyperframes render ./projects/<project-slug>/hyperframes --output ./outputs/<project-slug>/render-v001.mp4
```

最终文件：

```text
outputs/<project-slug>/render-v001.mp4
```

每次重新渲染递增版本号：

```text
outputs/<project-slug>/
├─ render-v001.mp4
├─ render-v002.mp4
└─ render-v003.mp4
```

不会覆盖历史版本。你可以自己选择哪个版本是“最终版”。

## 常用指令

引用技能写法：

```text
$video-workspace 把当前文件夹初始化成视频创作工作区
```

```text
$video-spec-director 根据 assets 里的素材生成 video-spec.md
```


```text
把当前文件夹初始化成视频创作工作区
```

```text
检查这个视频工作区是否可以正常制作视频
```

```text
根据 assets 里的素材生成 video-spec.md
```

```text
根据现有 video-spec.md 继续追问并完善分镜
```

```text
把现有 spec 改成更适合抖音的 30 秒版本
```

## 完整流程

```text
安装 Skill
→ 新建文件夹并用 Codex 打开
→ 初始化工作区
→ 放入素材到 assets/<film-slug>/
→ 生成 projects/<project-slug>/edit-plan.md
→ 确认 edit-plan 后生成 projects/<project-slug>/video-spec.md
→ 确认 / 修改 video-spec.md
→ 生成 projects/<project-slug>/hyperframes 工程
→ 预览
→ 渲染到 outputs/<project-slug>/render-vNNN.mp4
```
## 使用边界

## 常见问题

**Q: 安装失败怎么办？**

确认已安装 Node.js 22+，然后重试：

```powershell
node --version
npx skills add https://github.com/335812350/video_spec_gen --skill video-workspace --agent codex --copy --yes
```

**Q: 没有 FFmpeg 怎么办？**

Windows：

```powershell
winget install ffmpeg
```

macOS：

```bash
brew install ffmpeg
```

**Q: 渲染失败怎么办？**

1. 确认已安装 HyperFrames：`npx skills add heygen-com/hyperframes`
2. 检查 `video-spec.md` 是否完整
3. 运行 `npx hyperframes doctor` 检查环境

**Q: AI 配音生成失败？**

- 检查 `.env.local` 中的 `DASHSCOPE_API_KEY` 是否填写正确
- 不填则使用免费的 Edge TTS（机器味较重）

