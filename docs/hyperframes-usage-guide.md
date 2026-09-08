# HyperFrames 使用教程

> 面向：安装了 `coocaa_video` Skill Pack 的业务用户，以及想在本地手动使用 HyperFrames CLI 的团队成员
> 前置依赖：Node.js 22+、FFmpeg
> 最后更新：2026-09-08

## HyperFrames 是什么

HyperFrames 把 HTML 渲染成视频。一个"composition"就是一个 HTML 文件：DOM 上的 `data-*` 属性声明时间轴，动画由可 seek 的时间线驱动，媒体播放由框架托管。最终输出是标准 MP4（或透明 WebM）。

在本仓库的视频生产链路里，它是最下游的渲染层：

```text
video-workspace      搭好工作区
        ↓
video-spec-director  生成 / 迭代 video-spec.md
        ↓
HyperFrames          渲染成视频
```

日常使用中你几乎不需要直接写 HTML —— 那是 Codex 借助 `.agents/skills/hyperframes-core` 等 Skill 做的事。你手动操作的主要是 CLI：init（建工程）、check（检查）、preview（预览）、render（渲染）。

## 环境准备

### 必备依赖

| 依赖    | 要求               | 说明                                                  |
|---------|--------------------|-------------------------------------------------------|
| Node.js | 22 或更高          | `npx` 由 npm 提供；hyperframes CLI 强制要求 Node 22+ |
| npm     | 随 Node.js 一起安装 | 所有命令通过 `npx hyperframes ...` 运行              |
| FFmpeg  | 可执行文件在 PATH | 渲染、媒体处理和转写需要                              |
| Chrome  | 可选               | HyperFrames 自带固定版本 Chrome，缺失时见下文         |

### 安装前后各检查一次

```bash
# 初始化工作区后，用 Skill Pack 自带的 doctor 检查基础工具
.\doctor.ps1        # Windows
./doctor.sh         # macOS / Linux

# 检查 HyperFrames 自身的运行环境（Node 版本、FFmpeg、Chrome、内存等）
npx hyperframes doctor
```

`doctor` 会逐项报告 ok / warn / fail。常见问题：

- **缺 FFmpeg**：macOS 用 `brew install ffmpeg`；Windows 建议 winget 或官方构建。
- **缺 Chrome**：运行 `npx hyperframes browser ensure` 下载 HyperFrames 固定版本的 Chrome（渲染像素跨版本可复现）。
- **内存不足**：关闭其他 Chrome 实例，或渲染时降低 `--workers` / 用 `--quality draft`。

## 快速上手：第一条视频

### 1. 创建工程

```powershell
npx hyperframes init my-video
```

终端下会进入交互向导选模板。常用模板：`blank`（空白）、`warm-grain`、`kinetic-type`（动力学文字）、`product-promo`（产品宣传）。

常用参数：

```powershell
# 非交互 + 指定模板（CI / agent 场景必须带 --example）
npx hyperframes init my-video --non-interactive --example blank

# 竖屏（抖音 / 视频号 9:16）
npx hyperframes init my-video --example blank --resolution portrait

# 带源视频 / 音频创建（会自动用 Whisper 转写）
npx hyperframes init my-video --video clip.mp4
npx hyperframes init my-video --audio track.mp3
```

分辨率预设：`landscape`（1920×1080）、`portrait`（1080×1920）、`square`（1080×1080），以及各自的 `-4k` 版本。

### 2. 认识工程结构

```text
my-video/
├─ index.html          # composition 主文件：根节点 + 场景 + 时间轴
├─ hyperframes.json    # 工程配置（含所属工作流记录）
├─ package.json        # 固定 hyperframes 版本，保证渲染可复现
└─ compositions/       # 子 composition（多场景工程）
```

一个最小 composition 长这样（节选）：

```html
<div id="root"
  data-composition-id="main"
  data-width="1920" data-height="1080"
  data-duration="5">
  <section id="title-card" class="clip" data-start="0" data-duration="5">
    <h1 id="title">Hello HyperFrames</h1>
  </section>
</div>
<script>
  const tl = gsap.timeline({ paused: true });
  tl.from("#title", { y: 48, opacity: 0, duration: 0.6, ease: "power3.out" }, 0.2);
  window.__timelines["main"] = tl;
</script>
```

要点：

- 根节点必须带 `data-composition-id`、`data-width`、`data-height`，总时长由 `data-duration` 决定（也可以省略，从时间线或媒体推断）。
- 元素带上 `data-start` / `data-duration` 就成为一个"clip"（时间片段）；`class="clip"` 只是排版约定。
- 动画时间线必须 `paused: true` 创建，并注册到 `window.__timelines["<composition-id>"]`，渲染器按帧 seek 它，而不是实时播放。
- 媒体（`<video>` / `<audio>`）由框架托管播放和 seek，不要自己控制播放。

日常让 Codex 写这些即可；手动改 HTML 时注意上面几条硬规则，`lint` 会拦截大多数违规。

### 3. 检查

```powershell
npx hyperframes lint     # 快速静态检查，迭代时用
npx hyperframes check    # 最终门禁：lint + 运行时 + 布局 + 动效 + 对比度
```

`check` 用一次浏览器会话扫时间轴采样点，检查 JS 错误、失败请求、文字溢出/遮挡、动效断言和 WCAG 对比度。`check` 通过不代表可以渲染，只代表工程健康。

常用选项：

```powershell
npx hyperframes check --snapshots    # 输出带标注的总览帧和问题截图
npx hyperframes check --samples 15   # 更密的采样
npx hyperframes check --at 1.5,4,7.25  # 指定关键帧时间
npx hyperframes check --strict       # warning 也阻断（默认只有 error 阻断）
```

### 4. 预览

```powershell
npx hyperframes preview --background
```

启动 Studio（默认端口 3002），自动打开浏览器。交给用户看的 URL 形如：

```text
http://localhost:3002/#project/<project-name>
```

Studio 是完整的时间线编辑器：可以播放、看每一层、手动微调。审阅结束后停掉服务器：

```powershell
npx hyperframes preview --stop
```

注意：同个项目只保留一个 preview 服务器；需要轻量播放器（不要编辑器）时用 `npx hyperframes play`（默认端口 3003）。

### 5. 渲染

```powershell
# 草稿：迭代快，用于内部确认
npx hyperframes render --quality draft

# 正式：高质量交付
npx hyperframes render --quality high --output outputs/my-video/render-v001.mp4
```

默认输出 `renders/<project>_<时间戳>.mp4`；按仓库约定，正式版本写入 `outputs/<project-slug>/render-vNNN.mp4`，不覆盖历史版本。

常用渲染选项：

| 参数                    | 作用                                        |
|-------------------------|---------------------------------------------|
| `--quality draft/high`  | 草稿 / 高质量                                |
| `--fps 60`              | 帧率（正式交付可用 60）                      |
| `--format webm`         | 透明背景 WebM（叠加层用）                    |
| `--output <file>`       | 指定输出路径，覆盖默认时间戳命名             |
| `--docker`              | 容器内渲染，跨机器字节级可复现               |
| `--batch rows.json`     | 变量驱动批量渲染                             |

渲染后验证：

```powershell
ffprobe -v error -show_format outputs/my-video/render-v001.mp4
```

确认文件非空、时长、分辨率、编码符合预期。

### 6. 完整循环（cheat sheet）

```powershell
npx hyperframes init my-video --example blank --resolution portrait
npx hyperframes lint
npx hyperframes check --snapshots
npx hyperframes preview --background
# 人工审阅 + 确认
npx hyperframes preview --stop
npx hyperframes render --quality high --output outputs/my-video/render-v001.mp4
ffprobe -v error -show_format outputs/my-video/render-v001.mp4
```

## 在 Codex 里用（推荐日常路径）

装了 Skill Pack 后，你平时只需要说人话：

1. **初始化**："把当前文件夹初始化成视频创作工作区"
2. **放素材**：素材进 `assets/<film-slug>/`
3. **生成规格**："根据 assets 里的素材生成 video-spec.md" —— `video-spec-director` 会追问目标、受众、平台、时长、旁白、字幕、风格
4. **渲染**："渲染这个项目" —— Codex 会走 `hyperframes` 入口 Skill：先 `check`，再受控 `preview`，你确认后 `render`

判断该用哪条工作流由 HyperFrames 路由表决定（产品宣传 → `product-launch-video`、主题讲解 → `faceless-explainer`、字幕叠加 → `embedded-captions` 等），不需要你记。

## 常用命令速查

| 场景                 | 命令                                          |
|----------------------|-----------------------------------------------|
| 环境体检             | `npx hyperframes doctor`                      |
| 新建工程             | `npx hyperframes init <name>`                 |
| 从网站创建           | `npx hyperframes capture <url>`               |
| 快速静态检查         | `npx hyperframes lint`                        |
| 最终门禁             | `npx hyperframes check`                       |
| 总览帧快照           | `npx hyperframes snapshot`                    |
| Studio 预览          | `npx hyperframes preview --background`        |
| 轻量播放器           | `npx hyperframes play`                        |
| 渲染草稿             | `npx hyperframes render --quality draft`      |
| 渲染成品             | `npx hyperframes render --quality high --output <file>` |
| 变量批量渲染         | `npx hyperframes render --batch rows.json`    |
| 变体视觉对比         | `npx hyperframes compare a b --at 3 --out c.png` |
| 安装 HyperFrames 技能 | `npx hyperframes skills`                     |

`validate` / `inspect` / `layout` 是旧别名，功能已并入 `check`，新脚本不要再使用。

## 常见坑

1. **`init` 在非交互环境报错**：管道 / CI 里必须带 `--example`，加 `--non-interactive` 强制非交互。
2. **lint 报 `gsap_css_transform_conflict`**：不要在 CSS 里写初始 `transform` 又在 GSAP 里 tween 同一属性；用 `gsap.fromTo(el, { x: -40 }, { x: 0 })` 设置初始态。
3. **渲染出来没有声音**：`<audio>` 忘了 `id` —— mixer 找不到它，lint 会报 `media_missing_id`。
4. **视频画面在预览里是黑的**：给 `<video data-start>` 套了一个同样带 `data-start` 的父元素，lint 会报 `video_nested_in_timed_element`；计时属性只放一边。
5. **check 报 0 samples 却像"全绿"**：lint 有 error 时布局和对比度审计会整个跳过。先修 lint error，再看 check 结果。
6. **渲染失败报 Chrome/FFmpeg 错误**：先跑 `npx hyperframes doctor`；缺 Chrome 用 `npx hyperframes browser ensure`。
7. **在 agent 沙盒里渲染失败（macOS）**：沙盒可能拦截 Chromium 启动，这是宿主级限制；用 `--docker` 或云渲染兜底，不要自建替代渲染管线。
8. **check 报 `sweep_static`**：整个时间轴零几何变化会被判定为冻结；把入场动画分散到时间轴上，或保留一个持续动画元素。

## 与本仓库的衔接

- 工程位置：`projects/<project-slug>/hyperframes/`
- 渲染输出：`outputs/<project-slug>/render-vNNN.mp4`（递增，不覆盖）
- 深入规则：`.agents/skills/hyperframes-core/SKILL.md`（composition 契约）、`.agents/skills/hyperframes-cli/SKILL.md`（命令循环）
- 平台级说明：`docs/共享能力与资源目录.md` 中渲染相关能力条目
