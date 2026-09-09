# Scripts

`aliyun_tts.py` 是随 `aliyun-tts` Skill 一起分发的独立命令行脚本，使用 Python 标准库实现，不依赖仓库根目录的 `tools/`。

## 使用前提

1. 用户本机要有 Python 3.11+
2. 用户要有自己的 DASHSCOPE_API_KEY

## 配置

脚本按以下优先级读取配置：

1. 显式参数
2. 环境变量
3. 当前工作目录的 `.env.local`

常用变量：

```powershell
$env:DASHSCOPE_API_KEY="<your-key>"
$env:DASHSCOPE_BASE_URL="https://<endpoint>/api/v1"
```

不要在命令、日志、spec、manifest 或提交内容中写入真实 API Key。

## 常用命令

查询模型与授权：

```powershell
python scripts/aliyun_tts.py models
```

查询自定义音色：

```powershell
python scripts/aliyun_tts.py voices --model voice-enrollment --target-model <model>
```

生成 MP3：

```powershell
python scripts/aliyun_tts.py synthesize --model <model> --voice <voice> --text "你好" --out outputs/voice.mp3 --format mp3 --sample-rate 24000
```

流式生成：

```powershell
python scripts/aliyun_tts.py synthesize --model <model> --voice <voice> --script script.txt --out outputs/voice.mp3 --stream
```

声音复刻：

```powershell
python scripts/aliyun_tts.py clone --target-model <model> --prefix <name> --audio-url <url>
```
