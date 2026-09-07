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

## 素材、影片与视频项目目录

- `assets/<film-slug>/` 是影片输入边界，存放用户提供的源视频、音频、字幕、图形和参考资料。
- `assets/<film-slug>/references/` 可存放联网检索得到的公开资料、摘录和来源记录；这些属于研究输入，不是渲染产物。
- 研究资料保留来源 URL；大型媒体除非用户明确要求，否则只记录来源，不默认下载。
- 不要把 `video-spec.md`、`edit-plan.md`、预览、渲染视频或生成音频写入 `assets/`。
- `projects/<project-slug>/` 表示一个独立的视频交付项目，存放其 spec、分镜、HyperFrames 工程和运行记录。
- `outputs/<project-slug>/` 存放该视频项目递增版本的 `render-vNNN.mp4`。
- 同一影片的不同视频类型、平台、时长或音频策略必须使用不同的 `project-slug`；不把一个交付项目嵌套到另一个项目目录下。
- 项目的 `project.json` 使用 `source_film_slug` 关联共享的 `assets/<film-slug>/`；`variant_id` 只记录批次候选或实验，不默认创建目录。
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

- README 保持简洁；详细说明放入现有 `docs/` 或对应影片的 `projects/<project-slug>/`。
- 重大用户可感知改动同步更新相关文档。
- `docs/项目进展.md` 是项目状态的唯一汇总入口；新增或完成工作流、Skill、工具、项目、渲染版本、测试或架构能力时，必须在同一轮同步更新，不得等后续再补。
- 更新 `docs/项目进展.md` 的“已完成”时，必须写明完成日期或日期范围，并以 Git 提交日期、项目状态、QA 记录、测试结果或实际产物作为依据；未验证的内容只能放在“进行中”或“待完成”。
- 涉及平台边界、工作流注册、共享能力或执行层的改动，必须联动检查并按需同步：`docs/Agent驱动的自主视频生产平台总设计.md`、`docs/自主视频生产平台当前架构图.md`、`docs/共享能力与资源目录.md`、`.agents/skills/video-production-dispatcher/references/workflow-registry.md`。
- 新增或删除 Skill / 工作流 / 能力时，同时更新其权威文档、注册表、共享能力目录、项目进展和相关测试；不得只创建目录或修改 `SKILL.md` 就宣称能力已完成。
- 重命名、移动或删除文档后，必须使用 `rg` 检查仓库内旧路径和旧文件名引用，并同步修复 Markdown 链接、README、测试和交叉引用。
- 每次任务结束前执行一次文档一致性检查：确认项目进展中的完成状态与实际文件、状态记录、QA、输出版本和测试结果一致；发现过期描述时在同一轮修正。
- 本项目的 HyperFrames / 视频工作流 Skill 以仓库内 `.agents/skills/` 和根目录 `skills-lock.json` 为权威来源；修改或更新项目 Skill 时直接维护该目录并同步锁文件、文档和测试。`C:\Users\chenyinghong\.codex\skills` 只是 Codex 全局 Skill 目录，不得当作本项目 Skill 的依赖路径。
- HyperFrames CLI 的 `skills update` 是全局 Skill 安装/更新机制，不等同于更新本项目 `.agents/skills/`；如需执行全局更新，必须明确目标是 Codex 全局目录，并将其结果与项目本地 Skill 状态分开记录。
- 更新本项目已锁定的上游 HyperFrames Skill 时，必须在仓库根目录运行 `npx --yes skills@latest update --project --yes`；它更新 `skills-lock.json` 管理的项目级 Skill，不得在项目更新时附加 `--global`。更新前保留当前工作区改动，更新后必须检查 `.agents/skills/` 与 `skills-lock.json` 的 diff，保留本项目定制内容，并运行相关测试和文档一致性检查。
- 当前项目暂不使用 `console/` 文件夹；处理其他功能时默认忽略其中的代码、依赖和生成内容，除非用户明确要求修改 `console/` 。
- 本地验收时不要关闭用户已有的浏览器窗口或标签页。
- 反复出现的问题沉淀为本文件中的明确规则。

## HyperFrames 临时目录

- HyperFrames 项目的源码、配置和最终交付物仍放在项目目录或命令的 `--output` 指定位置；本节只约束渲染过程使用的系统临时目录。
- 执行 `npx hyperframes render`、`preview`、`snapshot` 或其他可能产生大量临时文件的命令时，优先将当前命令进程的 `TEMP` 和 `TMP` 设置为 `E:\Temp`，以减少 Chrome、FFmpeg 等子进程把临时文件写入系统盘。
- 必须在同一个 PowerShell 调用中设置环境变量并执行命令，例如：
  `$env:TEMP='E:\Temp'; $env:TMP='E:\Temp'; npx hyperframes render ...`
- 只修改当前进程及其子进程的环境变量，不修改 Windows 用户级或系统级环境变量。命令结束后不会永久改变系统配置。
- `E:\Temp` 必须提前存在且可写；如果不可用，应停止并提示用户，不要自动创建目录，也不要把环境变量改回系统默认值后继续渲染。
- 该设置只影响遵循 `TEMP`/`TMP` 的临时文件位置，不保证改变 npm/npx 缓存、HyperFrames 用户缓存、浏览器缓存或 Codex 插件缓存的位置；这些缓存仍可能位于 C 盘。
- 最终输出路径仍由项目的 `--output`、项目脚本或项目目录约定决定，不由 `TEMP`/`TMP` 决定。
