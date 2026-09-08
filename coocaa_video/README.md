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

- **Codex CLI**：已安装并登录
- **Node.js 22+**：HyperFrames 需要
- **FFmpeg**：视频处理

## 安装

### 只安装指定 Skill（推荐）

只安装业务 Skill，不影响其他内部开发版本：

```powershell
npx skills add https://github.com/335812350/video_spec_gen --skill video-workspace --agent codex --copy --yes
npx skills add https://github.com/335812350/video_spec_gen --skill video-spec-director --agent codex --copy --yes
```

### 安装 HyperFrames（渲染必需）

```powershell
npx skills add heygen-com/hyperframes
```

## 配置

### API Key（可选）

`.env.local` 中配置：

```bash
# 阿里云 DashScope / Model Studio，用于 AI 配音
# 不填写时使用免费的 Edge TTS（机器味较重）
DASHSCOPE_API_KEY=
```

获取方式：阿里云百炼平台 → API-KEY 管理

## 第一次使用

### 1. 新建工作文件夹

例如：

```text
my-video-project/
```

不要在这个文件夹里提前放代码或旧项目文件。

### 2. 用 Codex 打开这个文件夹

然后对 Codex 说：

```text
把当前文件夹初始化成视频创作工作区
```

Codex 会触发 `video-workspace`，在当前文件夹创建：

```text
assets/       按源影片或主题划分：assets/<film-slug>/，研究资料在其 references/ 中
projects/     按交付项目划分：projects/<project-slug>/，保存 video-spec.md、edit-plan.md、project.json 和 hyperframes/
outputs/      按交付项目划分：outputs/<project-slug>/，保存 render-v001.mp4、render-v002.mp4 等版本
.codex-tmp/   当前任务临时文件，按 project-slug 分目录，任务结束后清理
setup.*       初始化脚本
doctor.*      环境检查脚本
```

初始化后，Codex 会运行环境检查，并告诉你缺什么依赖。

### 3. 放入素材

把素材放到 `assets/`。建议按主题建立子目录，例如：

```text
assets/
└─ product-launch/
   ├─ source.mp4
   ├─ voice.wav
   ├─ logo.png
   └─ references/
      ├─ film-metadata.json
      ├─ film-profile.md
      └─ story-context.md
```

### 4. 生成视频规格

素材放好后，对 Codex 说：

```text
根据 assets 里的素材，帮我生成 video-spec.md
```

也可以说得更具体：

```text
根据 assets/product-launch 里的素材，帮我做一个 60 秒、16:9、中文旁白、适合视频号发布的产品宣传视频规格
```

Codex 会触发 `video-spec-director`，通过追问补齐目标、受众、平台、时长、旁白、字幕、风格和分镜。

### 5. 修改已有规格

之后可以直接说：

```text
把第 2 个镜头节奏改快一点，字幕改成逐词出现
```

或：

```text
把这条视频改成 9:16，时长控制在 30 秒
```

Codex 会进入迭代模式，更新 `video-spec.md`，不会整段覆盖已有内容。

## 常用指令

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
1. 安装 Skill（video-workspace + video-spec-director + hyperframes）
2. 新建文件夹，用 Codex 打开
3. 初始化工作区：创建 assets/、projects/、outputs/ 等目录
4. 放入素材：assets/<film-slug>/
5. 生成 spec：Codex 追问并生成 video-spec.md
6. 渲染视频：/hyperframes 或 npx hyperframes render
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

