# 仓库 Agent 说明

本文档约束本项目中的 AI / 自动化开发行为。用户当前消息可以覆盖本文件，系统规则优先级最高。

## 基本原则

- 先读现有代码、文档和目录约束，再开始修改。
- 优先沿用现有结构，保持改动最小。
- 通用能力优先使用成熟库和现有工具，不重复实现底层能力。
- 不改无关文件，不顺手重构。
- 保留用户已有改动，不使用重置或覆盖操作清理工作区。
- 修改代码后运行相关测试或检查；不强制执行无关的完整构建。

## Git 与 GitHub

- `origin` 指向个人 GitHub 仓库，未经用户要求不向其他远程仓库推送。
- `main` 保持可用，功能开发优先使用 `codex/<功能名>` 分支。
- 推送前确认没有提交 `.env.local`、本地素材、生成产物、依赖目录或媒体文件。
- 不使用无保护的 `git push --force`；必要时使用 `--force-with-lease`。
- 不覆盖用户未提交的改动或远程已有提交。

## HyperFrames 预览

- 每个项目只保留一个预览服务器，启动前先运行 `npx hyperframes preview --status`。
- 默认复用端口 `3002`，启动预览优先使用 `--no-open`。
- 不为同一项目重复启动 `preview`、`play` 或 `present`。
- 审阅完成后运行 `npx hyperframes preview --stop`。
- 渲染期间和完成后不要保留预览服务器。

## 素材与影片目录

- `assets/<film-slug>/` 是影片输入边界，存放用户提供的源视频、音频、字幕、图形和参考资料。
- `assets/<film-slug>/references/` 可存放联网检索得到的公开资料、摘录和来源记录；这些属于研究输入，不是渲染产物。
- 研究资料保留来源 URL；大型媒体除非用户明确要求，否则只记录来源，不默认下载。
- 不要把 `video-spec.md`、`edit-plan.md`、预览、渲染视频或生成音频写入 `assets/`。
- `projects/<film-slug>/` 存放 spec、分镜和可编辑项目文件。
- `outputs/<film-slug>/` 存放递增版本的 `render-vNNN.mp4`。
- `videos/` 仅作为旧版工作目录，除非用户明确指定，否则不作为新产物位置。
- 不覆盖已有渲染版本，不重写历史 spec、manifest、音频或视频。
- 用户提供的素材默认可用于当前本地制作，不反复提出无关版权警告。

## 阿里云 TTS 与密钥

- 视频配音统一使用 `tools/aliyun_tts.py`，不再使用 Edge TTS。
- 涉及模型、音色或声音复刻时读取 `.agents/skills/aliyun-tts/SKILL.md`。
- `model` 与 `voice` 必须匹配当前 Workspace 授权。
- API Key 只放 `.env.local` 或环境变量，不得出现在代码、日志、manifest、spec、命令示例或聊天内容中。
- 不将本地音频、生成音频或 API Key 上传到 GitHub。

## 文档与控制台

- README 保持简洁；详细说明放入现有 `docs/` 或对应影片的 `projects/<film-slug>/`。
- 重大用户可感知改动同步更新相关文档。
- `console` 的运行事件保持追加式，状态文件使用原子写入，不静默删除或裁剪历史记录。
- 本地验收时不要关闭用户已有的浏览器窗口或标签页。
- 反复出现的问题沉淀为本文件中的明确规则。