---
name: video-workspace
description: 在当前空文件夹初始化可复用的本地视频创作工作区，复制目录模板、环境检查脚本和配置模板；当业务用户说“初始化视频工作区”“搭建视频项目”“开始用 Codex 做视频”时使用。
---

# Video Workspace

用于把一个普通文件夹初始化成 Codex 视频创作工作区。

## 触发场景

- 用户已创建一个空文件夹，并用 Codex 打开。
- 用户希望开始制作视频，但还没有目录结构、配置模板或检查脚本。
- 用户说“初始化视频工作区”“搭建视频创作环境”“把这里变成视频项目”。

## 必须遵守
- `.codex-tmp/` 只存放当前任务的临时文件，例如转写输出、音频分析、字幕缓存和下载缓存。
- `.codex-tmp/` 不放用户原始素材、video-spec、HyperFrames 工程或最终视频。
- 临时文件建议按 `project-slug` 建子目录；任务结束后清理，或保留到下次任务开始前统一清理。

- 只在用户当前打开的工作目录中操作。
- 不要求用户 clone 开发仓库。
- 不覆盖已有的 `.env.local`、素材、项目文件、历史输出。
- 不确定当前目录是否正确时，先向用户确认。
- 模板中的脚本只检查和准备环境；安装系统软件前必须获得用户确认。

## 初始化步骤

1. 确认当前目录就是用户要使用的视频工作区。
2. 将 `references/` 下的模板复制到当前目录：
   - `setup.ps1` / `setup.sh`
   - `doctor.ps1` / `doctor.sh`
   - `.env.example`
   - `assets/README.md`
- `projects/README.md`
- `outputs/README.md`
3. 如果目标文件已存在，跳过并明确告知；不得覆盖。
4. 根据当前系统运行对应检查：
   - Windows: `.\doctor.ps1`
   - macOS/Linux: `./doctor.sh`
5. 用简明语言报告：
   - 哪些环境已就绪
   - 缺少哪些依赖
- 素材按 `assets/<film-slug>/` 放置，研究资料放入其 `references/`
- 项目文件按 `projects/<project-slug>/` 放置
- 最终视频按 `outputs/<project-slug>/` 递增版本保存
6. 环境缺失时，先告诉用户将执行什么安装命令，等待确认后再执行。


## 后续工作流

初始化完成后，进入 `video-spec-director`：

- 用户提供素材、主题、平台、时长、风格和文案。
- Codex 生成或更新 `video-spec.md`。
- 用户在 `projects/<project-slug>/` 中创建具体视频项目。
- 渲染输出保存到 `outputs/<project-slug>/`，不覆盖历史版本。

## 典型用户指令

```text
把当前文件夹初始化成视频创作工作区。
```

```text
检查这个视频工作区是否可以在本机运行。
```

```text
我已经把素材放进 assets，帮我开始制作视频。
```
