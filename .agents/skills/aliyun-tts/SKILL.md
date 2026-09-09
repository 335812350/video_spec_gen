---
name: aliyun-tts
description: Use when a video workflow needs Alibaba Cloud Model Studio TTS, model or voice selection, custom voice cloning, or DashScope HTTP/SSE audio generation.
---

# 阿里云 TTS

把阿里云百炼的模型、音色和复刻操作收敛到本 Skill 自带的独立入口。需要生成旁白时读取本 skill；影片需求收集、分镜和节奏规则仍由 `video-spec-director-dev` 负责。

## 边界

- 实现入口是 `scripts/aliyun_tts.py`，用它执行 `models`、`voices`、`synthesize` 和 `clone`；脚本只依赖 Python 标准库，可随 Skill 脱离仓库使用。
- 当前工具支持 HTTP 非流式和 HTTP SSE；不把实时 WebSocket 模型当作可用的普通合成路径。
- `qwen-audio-*`、`cosyvoice-*` 走 SpeechSynthesizer；`qwen3-tts-*` / `qwen-tts*` 走多模态 generation。不要把 Qwen-Audio 发到 OpenAI 兼容 Chat 接口。

## 配置与安全

- 当前工作目录的 `.env.local` 保存 `DASHSCOPE_API_KEY`；可选 `DASHSCOPE_BASE_URL`。优先级是显式 CLI 参数 > 环境变量 > `.env.local`。
- Key 只用于请求，禁止写入日志、manifest、spec、错误文本或示例；展示错误时先脱敏。
- `.env.local` 必须保持在 `.gitignore` 中；优先使用文件或环境变量，不把 `--api-key` 写进聊天记录、脚本或 shell history。
- `--voice` 必须显式提供。先用 `python scripts/aliyun_tts.py models` 查询授权，再查自定义音色：Qwen-Audio/CosyVoice 通常用 `voices --model voice-enrollment`，Qwen3-TTS 用 `voices --model qwen-voice-enrollment`；可追加 `--target-model <model>` 精确筛选。不要凭文档示例猜音色是否属于账号。

## 模型选择

| 场景 | 首选 | 说明 |
|---|---|---|
| 质量优先的普通旁白 | `qwen-audio-3.0-tts-plus` 或 `cosyvoice-v3.5-plus` | 更适合长旁白、情绪和指令控制；先试听再定稿 |
| 成本/速度优先 | `qwen-audio-3.0-tts-flash` 或 `cosyvoice-v3.5-flash` | 当前默认模型是 `qwen-audio-3.0-tts-flash` |
| 已有当前账号的 CosyVoice 复刻音色 | 与音色的 `target_model` 完全一致的 `cosyvoice-*` | 用户当前的自定义音色必须按查询结果配对 |
| Qwen3 系统音色 | `qwen3-tts-flash` / `qwen3-tts-instruct-flash` | `flash` 不是复刻模型；不要用它做本地声音复刻 |
| Qwen3 声音能力 | `qwen3-tts-vc-*` 复刻，`qwen3-tts-vd-*` 声音设计 | 复刻后的合成模型必须与 `--target-model` 完全相同 |
| 旧版兼容 | `qwen-tts*` | 仅在项目明确需要时使用 |

账号授权列表可能还包含 MiniMax、Sambert 或 realtime 模型；若 `aliyun_tts.py` 未提供对应路由，不要声称当前 CLI 已支持，先看 `--help` 或补充适配。

## 音色参考

- `references/qwen-audio-3.0-tts-plus基础音色.xlsx` 是 qwen-audio-3.0-tts-plus 的基础音色对照表；选择该模型音色时先查阅此文件，再按账号 `voices` 查询结果确认可用性。
## 音色与复刻

- 系统音色：直接将账号和模型文档确认过的 voice ID 传给 `--voice`。
- 自定义音色：先查询 `voices`，检查状态为可用，并确认其 `target_model` 与合成模型一致。
- Qwen-Audio/CosyVoice 复刻使用可访问、在请求期间有效的 `--audio-url`；本地路径直接报错，不自动引入 OSS 上传。
- Qwen-TTS 的 `qwen3-tts-vc-*` 等官方复刻模型才使用 `--audio` 本地文件，工具会检查扩展名、非空、大小和基础音频质量并转 Data URI。不要用 `qwen3-tts-flash` 做复刻；样本必须获得授权。
- 复刻名称、语言和其他模型专属字段按官方接口校验；不把一个模型的 voice ID 交给另一个模型。

## 常用操作

```powershell
python scripts/aliyun_tts.py models
python scripts/aliyun_tts.py voices --model voice-enrollment --target-model <model>
python scripts/aliyun_tts.py synthesize --model <model> --voice <voice> --text "..." --out outputs/voice.mp3 --format mp3 --sample-rate 24000
python scripts/aliyun_tts.py synthesize --model <model> --voice <voice> --script script.txt --out outputs/voice.mp3 --stream
python scripts/aliyun_tts.py clone --target-model <model> --prefix <name> --audio-url <url>
```

`--extra-json` 只传入目标模型支持的参数。默认产物为 MP3/24000 Hz；需要章节旁白时使用项目生成脚本，让它同时维护 manifest 和 SRT，避免在 skill 中重复实现时间轴。

## 交给视频规格编排的信息

询问并记录：模型、voice ID、系统音色或复刻音色、语言/发音要求、是否 SSE、输出格式、采样率，以及音色样本的来源和授权状态。manifest 记录实际模型、音色、格式、采样率和参数，但绝不记录 Key。不要覆盖历史 Edge 音频或历史 manifest，迁移产物使用新的输出版本或目录。

## 官方参考

- [TTS 模型概览](https://help.aliyun.com/zh/model-studio/tts-model)
- [非实时 TTS HTTP API](https://help.aliyun.com/zh/model-studio/non-realtime-tts-user-guide)
- [声音复刻 HTTP API](https://help.aliyun.com/zh/model-studio/voice-clone-design-http-api)
- [CosyVoice 音色列表](https://help.aliyun.com/zh/model-studio/cosyvoice-voice-list)
- [Qwen3-TTS 音色列表](https://help.aliyun.com/en/model-studio/qwen-tts-voice-list)
