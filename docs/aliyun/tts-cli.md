# 阿里云语音合成 CLI

仓库内的语音生成统一使用 `.agents/skills/aliyun-tts/scripts/aliyun_tts.py`，不再依赖 Edge TTS。默认请求北京业务空间的 HTTP 非流式接口，必要时可用 `--stream` 使用 SSE。

## 配置

复制 `.env.example` 为仓库根目录的 `.env.local`，填入百炼 API Key：

```text
DASHSCOPE_API_KEY=你的Key
```

也可以通过环境变量或 CLI 显式参数传入。优先级为：CLI 参数 > 环境变量 > `.env.local`。`.env.local` 已被 `.gitignore` 排除，Key 不会写入 manifest 或日志。

## 合成

`--voice` 必须显式提供，避免误用不属于当前账号的示例音色：

```powershell
python .agents/skills/aliyun-tts/scripts/aliyun_tts.py synthesize `
  --model qwen-audio-3.0-tts-flash `
  --voice longanhuan_v3.6 `
  --text "你好，欢迎使用语音合成。" `
  --out outputs/voice.mp3 `
  --format mp3 `
  --sample-rate 24000
```

`qwen-audio-*` 和 `cosyvoice-*` 使用 `/services/audio/tts/SpeechSynthesizer`；`qwen3-tts-*` 使用多模态 generation 接口。合成返回临时 URL 时，CLI 会立即下载到 `--out`。

长文本或需要逐块接收时增加 `--stream`。`--script` 可代替 `--text` 读取 UTF-8 文本文件；模型专属字段可用 `--extra-json '{"parameters":{"volume":60}}'` 传入。

## 模型与音色

```powershell
python .agents/skills/aliyun-tts/scripts/aliyun_tts.py models
python .agents/skills/aliyun-tts/scripts/aliyun_tts.py voices --model voice-enrollment
```

`voices` 只查询自定义音色；系统音色直接填写给 `--voice`。

## 音色复刻

Qwen-Audio/CosyVoice 使用可访问的音频 URL，不会自动上传本地文件，也不需要 OSS 配置：

```powershell
python .agents/skills/aliyun-tts/scripts/aliyun_tts.py clone `
  --target-model cosyvoice-v3-flash `
  --prefix my_voice `
  --audio-url https://example.com/reference.wav
```

Qwen-TTS 支持本地文件，CLI 会执行扩展名、非空、10 MB 大小检查，并转成 Data URI：

```powershell
python .agents/skills/aliyun-tts/scripts/aliyun_tts.py clone `
  --target-model qwen3-tts-flash `
  --prefix my_voice `
  --audio .\reference.wav
```

`--target-model` 必须与后续合成使用的模型完全一致。请确保音频样本已获授权并符合阿里云接口要求。

## 项目脚本

电视示例保留旧输出目录兼容性：

```powershell
python tools/generate_tv_voice.py --voice my_voice
```

年会旁白使用：

```powershell
python projects/annual-meeting-commentary/tools/generate_aliyun_voiceover.py `
  --voice my_voice
```

原 `generate_edge_voiceover.py` 文件名作为兼容入口保留，但内部已转发到上述阿里云实现。每个输入段都会生成完整 SRT cue；时长优先由 `ffprobe` 读取，缺失时使用 `--fallback-duration` 并保留可追溯的 manifest 参数。
