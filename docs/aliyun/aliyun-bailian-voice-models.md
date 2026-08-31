# 阿里云百炼语音模型调用指南

适用 Host：

```text
https://ws-1pb723s50rmgu0wh.cn-beijing.maas.aliyuncs.com
```

API Key 从环境变量读取：

```powershell
$env:DASHSCOPE_API_KEY = "<你的北京 Workspace API Key>"
```

该 Host 是北京业务空间专属域名，Key 必须属于同一 Workspace 和地域。语音模型不能统一使用 OpenAI Chat；应按模型和实时性选择接口。[语音模型总览](https://help.aliyun.com/zh/model-studio/tts-model) ｜ [实时 API 总览](https://help.aliyun.com/zh/model-studio/realtime-api-overview)

## 1. 模型选择

| 场景 | 推荐模型 | 协议 | 备注 |
|---|---|---|---|
| 实时语音识别 | `qwen-audio-3.0-asr-flash-streaming`、`fun-asr-realtime`、`qwen3-asr-flash-realtime` | WebSocket | 二进制音频流输入、文本流输出 |
| 短音频转写 | `qwen-audio-3.0-asr-flash`、`qwen3-asr-flash`、`fun-asr-flash-2026-06-15` | HTTP 同步 | 通常不超过 5 分钟 |
| 长音频/会议转写 | `qwen-audio-3.0-asr-flash-filetrans`、`qwen3-asr-flash-filetrans`、`fun-asr`、`paraformer-v2` | HTTP 异步 | 最长可到 12 小时/2GB，支持说话人分离的模型以目录为准 |
| 普通语音合成 | `qwen-audio-3.0-tts-plus`、`qwen-audio-3.0-tts-flash` | HTTP 或 SSE | 返回音频 URL，或逐段输出音频 |
| CosyVoice 合成 | `cosyvoice-v3.5-plus`、`cosyvoice-v3.5-flash`、`cosyvoice-v3-plus`、`cosyvoice-v3-flash`、`cosyvoice-v2` | HTTP 或 WebSocket | 支持系统音色、声音设计等能力 |
| Qwen-TTS | `qwen3-tts-flash`、`qwen3-tts-instruct-flash`、`qwen-tts` | DashScope 多模态 HTTP | `-instruct` 支持自然语言控制表现力 |
| 实时语音合成 | `qwen-audio-3.0-tts-flash`、`qwen-audio-3.0-tts-plus`、CosyVoice | WebSocket | 低首包延迟，边输入边输出 |
| 实时语音对话 | `qwen-audio-3.0-realtime-plus`、`qwen-audio-3.0-realtime-flash` | WebSocket/WebRTC/AOQ | 输入语音、输出语音和文本 |

最终是否对当前账号开放，以 `/api/v1/models` 和 `/api/v1/models/permissions` 返回为准。

## 2. 公共配置

Python：

```powershell
pip install -U dashscope openai requests websockets
```

Node.js：

```powershell
# Node.js 18+ 可直接使用内置 fetch；更低版本请改用 undici
npm install openai ws
```

```python
import os

KEY = os.environ["DASHSCOPE_API_KEY"]
HOST = "https://ws-1pb723s50rmgu0wh.cn-beijing.maas.aliyuncs.com"
DASH_BASE = f"{HOST}/api/v1"
OPENAI_BASE = f"{HOST}/compatible-mode/v1"
```

## 3. 非实时语音合成 TTS

### 3.1 Qwen-Audio-TTS / CosyVoice：HTTP 非流式

端点：

```text
POST /api/v1/services/audio/tts/SpeechSynthesizer
```

Python：

```python
import os
import requests

url = "https://ws-1pb723s50rmgu0wh.cn-beijing.maas.aliyuncs.com/api/v1/services/audio/tts/SpeechSynthesizer"
payload = {
    "model": "qwen-audio-3.0-tts-flash",
    "input": {
        "text": "欢迎使用阿里云百炼语音服务。",
        "voice": "longanhuan_v3.6",
        "format": "wav",
        "sample_rate": 24000,
    },
}

r = requests.post(
    url,
    headers={"Authorization": f"Bearer {os.environ['DASHSCOPE_API_KEY']}"},
    json=payload,
    timeout=60,
)
r.raise_for_status()
data = r.json()
audio = data.get("output", {}).get("audio", {})
audio_url = audio.get("url") or data.get("output", {}).get("audio_url")
if not audio_url:
    raise RuntimeError(f"响应中没有音频 URL，请检查模型文档和响应：{data}")
print(audio_url)  # URL 有效期通常为 24 小时，应立即下载
open("tts.wav", "wb").write(requests.get(audio_url, timeout=60).content)
```

CosyVoice 只需要替换模型和音色，例如：

```python
payload["model"] = "cosyvoice-v3-flash"
payload["input"]["voice"] = "longanyang"
```

### 3.2 HTTP SSE 流式合成

在同一个端点增加请求头：

```text
X-DashScope-SSE: enable
```

SSE 响应中的音频数据需要按事件逐段解析并追加写入文件或播放设备。下面示例将 Base64 音频片段写入文件；生产环境可在收到片段后交给播放器：

```python
import base64
import json
import os
import requests

url = "https://ws-1pb723s50rmgu0wh.cn-beijing.maas.aliyuncs.com/api/v1/services/audio/tts/SpeechSynthesizer"
payload = {
    "model": "qwen-audio-3.0-tts-flash",
    "input": {
        "text": "这是一段流式语音合成测试。",
        "voice": "longanhuan_v3.6",
        "format": "mp3",
        "sample_rate": 24000,
    },
}
with requests.post(
    url,
    headers={
        "Authorization": f"Bearer {os.environ['DASHSCOPE_API_KEY']}",
        "X-DashScope-SSE": "enable",
    },
    json=payload,
    stream=True,
    timeout=120,
) as response:
    response.raise_for_status()
    with open("tts-stream.mp3", "wb") as output:
        for line in response.iter_lines(decode_unicode=True):
            if not line or not line.startswith("data:"):
                continue
            event = json.loads(line[5:].strip())
            chunk = event.get("output", {}).get("audio", {}).get("data")
            if chunk:
                output.write(base64.b64decode(chunk))
```

不要把 SSE 音频当作普通 JSON 一次性解析。Qwen-TTS 流式响应的中间 chunk 也通过 `output.audio.data` 返回 Base64，最后一个 chunk 提供完整音频 URL。[非实时语音合成](https://help.aliyun.com/zh/model-studio/non-realtime-tts-user-guide)

### 3.3 Qwen-TTS：DashScope 多模态接口

Qwen-TTS 使用的端点与 Qwen-Audio-TTS 不同：

```text
POST /api/v1/services/aigc/multimodal-generation/generation
```

```python
import os
import dashscope
from dashscope import MultiModalConversation

dashscope.base_http_api_url = "https://ws-1pb723s50rmgu0wh.cn-beijing.maas.aliyuncs.com/api/v1"
resp = MultiModalConversation.call(
    api_key=os.environ["DASHSCOPE_API_KEY"],
    model="qwen3-tts-flash",
    text="今天是美好的一天，让我们开始工作吧。",
    voice="Cherry",
    language_type="Chinese",
    stream=False,
)
print(resp.output.audio.url)
```

`voice`、`language_type`、音频格式等字段随 Qwen-TTS 版本变化，使用前查看该模型的 API 参考。

## 4. 非实时语音识别 ASR

### 4.1 短音频同步识别

`qwen-audio-3.0-asr-flash` 支持 URL 或 Base64，通常适合 5 分钟以内音频。DashScope 端点：

```text
POST /api/v1/services/aigc/multimodal-generation/generation
```

```python
import os
import requests

url = "https://ws-1pb723s50rmgu0wh.cn-beijing.maas.aliyuncs.com/api/v1/services/aigc/multimodal-generation/generation"
r = requests.post(
    url,
    headers={"Authorization": f"Bearer {os.environ['DASHSCOPE_API_KEY']}"},
    json={
        "model": "qwen-audio-3.0-asr-flash",
        "input": {"messages": [{
            "role": "user",
            "content": [{
                "type": "input_audio",
                "input_audio": {"data": "https://example.com/audio.wav"},
            }],
        }]},
        "parameters": {"format": "wav", "sample_rate": 16000},
    },
    timeout=60,
)
r.raise_for_status()
resp = r.json()

# 该模型的返回结构不是 choices，而是 output.text
print(resp["output"]["text"])
```

如果使用 OpenAI 兼容的 `qwen3-asr-flash`，请求形态是 Chat Completions，音频内容使用 `input_audio`，输出为普通 `chat.completion`。需要时间戳时改用异步 Filetrans 模型。[Qwen-ASR API](https://help.aliyun.com/zh/model-studio/qwen-asr-api-reference)

#### OpenAI 兼容的 `qwen3-asr-flash`

该模型是语音模型中少数同时支持 OpenAI 兼容协议的模型。音频可以传公网 URL，也可以传 `data:audio/...;base64,...`；非标准的识别选项通过 `extra_body` 传入：

```python
from openai import OpenAI
import os

client = OpenAI(
    api_key=os.environ["DASHSCOPE_API_KEY"],
    base_url="https://ws-1pb723s50rmgu0wh.cn-beijing.maas.aliyuncs.com/compatible-mode/v1",
)
completion = client.chat.completions.create(
    model="qwen3-asr-flash",
    messages=[{
        "role": "user",
        "content": [{
            "type": "input_audio",
            "input_audio": {"data": "https://example.com/audio.wav"},
        }],
    }],
    extra_body={"asr_options": {"language": "zh", "enable_itn": False}},
)
print(completion.choices[0].message.content)
```

Node.js：

```javascript
import OpenAI from "openai";

const client = new OpenAI({
  apiKey: process.env.DASHSCOPE_API_KEY,
  baseURL: "https://ws-1pb723s50rmgu0wh.cn-beijing.maas.aliyuncs.com/compatible-mode/v1",
});

const completion = await client.chat.completions.create({
  model: "qwen3-asr-flash",
  messages: [{
    role: "user",
    content: [{
      type: "input_audio",
      input_audio: { data: "https://example.com/audio.wav" },
    }],
  }],
  asr_options: { language: "zh", enable_itn: false },
});
console.log(completion.choices[0].message.content);
```

### 4.2 长音频异步转写

提交接口：

```text
POST /api/v1/services/audio/asr/transcription
X-DashScope-Async: enable
```

```python
import os
import requests
import time

base = "https://ws-1pb723s50rmgu0wh.cn-beijing.maas.aliyuncs.com/api/v1"
headers = {"Authorization": f"Bearer {os.environ['DASHSCOPE_API_KEY']}"}
body = {
    "model": "qwen-audio-3.0-asr-flash-filetrans",
    "input": {"file_urls": ["https://example.com/meeting.mp3"]},
    "parameters": {"language_hints": ["zh", "en"]},
}

created = requests.post(
    f"{base}/services/audio/asr/transcription",
    headers={**headers, "X-DashScope-Async": "enable"},
    json=body,
    timeout=60,
)
created.raise_for_status()
task_id = created.json()["output"]["task_id"]

while True:
    result = requests.get(f"{base}/tasks/{task_id}", headers=headers, timeout=30).json()
    status = result["output"]["task_status"]
    if status in {"SUCCEEDED", "FAILED", "CANCELED"}:
        break
    time.sleep(3)

if status == "SUCCEEDED":
    transcription_url = result["output"]["results"][0]["transcription_url"]
    transcription = requests.get(transcription_url, timeout=60).json()
    print(transcription)
else:
    raise RuntimeError(result)
```

任务查询接口：

```text
GET /api/v1/tasks/{task_id}
```

任务和结果 URL 通常仅保留 24 小时。长音频模型支持说话人分离、句级/词级时间戳等能力，但需要按模型设置参数。[非实时语音识别](https://help.aliyun.com/zh/model-studio/non-realtime-speech-recognition-user-guide)

## 5. 实时语音识别 ASR WebSocket

北京 WebSocket 地址：

```text
wss://ws-1pb723s50rmgu0wh.cn-beijing.maas.aliyuncs.com/api-ws/v1/inference
```

Python SDK 示例：

```python
import os
import dashscope
from dashscope.audio.asr import Recognition, RecognitionCallback, RecognitionResult


class Callback(RecognitionCallback):
    def on_complete(self):
        print("\n识别完成")

    def on_error(self, result):
        print("识别失败:", result)

    def on_event(self, result):
        sentence = result.get_sentence()
        if "text" in sentence:
            print(sentence["text"], end="", flush=True)
        if RecognitionResult.is_sentence_end(sentence):
            print()

dashscope.api_key = os.environ["DASHSCOPE_API_KEY"]
dashscope.base_websocket_api_url = (
    "wss://ws-1pb723s50rmgu0wh.cn-beijing.maas.aliyuncs.com/api-ws/v1/inference"
)

recognition = Recognition(
    model="qwen-audio-3.0-asr-flash-streaming",
    format="pcm",
    sample_rate=16000,
    callback=Callback(),
)
recognition.start()

with open("mic.pcm", "rb") as audio_file:
    while chunk := audio_file.read(3200):
        recognition.send_audio_frame(chunk)

recognition.stop()
```

原始 WebSocket 的事件顺序是：

```text
连接 -> run-task -> task-started -> 二进制音频帧 -> result-generated -> finish-task -> task-finished
```

实时 ASR 的音频格式、采样率和单声道要求必须按模型目录核对。`qwen-audio-3.0-asr-flash-streaming` 与 `fun-asr-realtime` 使用同一类事件协议。[实时语音识别](https://help.aliyun.com/zh/model-studio/real-time-speech-recognition-user-guide) ｜ [客户端事件](https://help.aliyun.com/zh/model-studio/fun-asr-client-events)

## 6. 实时语音合成 TTS WebSocket

Python SDK：

```python
import os
import dashscope
from dashscope.audio.tts_v2 import SpeechSynthesizer

dashscope.api_key = os.environ["DASHSCOPE_API_KEY"]
dashscope.base_websocket_api_url = (
    "wss://ws-1pb723s50rmgu0wh.cn-beijing.maas.aliyuncs.com/api-ws/v1/inference"
)

synthesizer = SpeechSynthesizer(
    model="qwen-audio-3.0-tts-flash",
    voice="longanhuan_v3.6",
)
audio = synthesizer.call("这是一段实时语音合成测试。")
with open("realtime-tts.mp3", "wb") as f:
    f.write(audio)
```

CosyVoice 使用相同的 WebSocket 协议，只替换 `model` 和对应的 `voice`。实时 TTS 适合客服、语音助手、播报等场景；批量有声内容应使用 HTTP 非实时接口。[实时语音合成](https://help.aliyun.com/zh/model-studio/realtime-tts-user-guide)

## 7. Node.js 调用

### 7.1 非实时 TTS

```javascript
const host = "https://ws-1pb723s50rmgu0wh.cn-beijing.maas.aliyuncs.com";
const apiKey = process.env.DASHSCOPE_API_KEY;

const response = await fetch(`${host}/api/v1/services/audio/tts/SpeechSynthesizer`, {
  method: "POST",
  headers: {
    Authorization: `Bearer ${apiKey}`,
    "Content-Type": "application/json",
  },
  body: JSON.stringify({
    model: "qwen-audio-3.0-tts-flash",
    input: {
      text: "欢迎使用阿里云百炼语音服务。",
      voice: "longanhuan_v3.6",
      format: "mp3",
      sample_rate: 24000,
    },
  }),
});

if (!response.ok) throw new Error(await response.text());
const result = await response.json();
const audioUrl = result.output?.audio?.url ?? result.output?.audio_url;
if (!audioUrl) throw new Error(`响应中没有音频 URL: ${JSON.stringify(result)}`);
console.log(audioUrl);
```

### 7.2 长音频 ASR

```javascript
const created = await fetch(`${host}/api/v1/services/audio/asr/transcription`, {
  method: "POST",
  headers: {
    Authorization: `Bearer ${apiKey}`,
    "Content-Type": "application/json",
    "X-DashScope-Async": "enable",
  },
  body: JSON.stringify({
    model: "qwen-audio-3.0-asr-flash-filetrans",
    input: { file_urls: ["https://example.com/meeting.mp3"] },
  }),
});

if (!created.ok) throw new Error(await created.text());
const task = await created.json();
const taskId = task.output.task_id;
let finalResult;
for (;;) {
  const poll = await fetch(`${host}/api/v1/tasks/${taskId}`, {
    headers: { Authorization: `Bearer ${apiKey}` },
  });
  if (!poll.ok) throw new Error(await poll.text());
  finalResult = await poll.json();
  const status = finalResult.output?.task_status;
  if (["SUCCEEDED", "FAILED", "CANCELED"].includes(status)) break;
  await new Promise((resolve) => setTimeout(resolve, 3000));
}
if (finalResult.output.task_status !== "SUCCEEDED") {
  throw new Error(JSON.stringify(finalResult));
}
const transcriptionUrl = finalResult.output.results[0].transcription_url;
console.log(await fetch(transcriptionUrl).then((r) => r.json()));
```

### 7.3 实时 TTS WebSocket

```javascript
import WebSocket from "ws";
import { randomUUID } from "node:crypto";

const ws = new WebSocket(
  `${host.replace("https://", "wss://")}/api-ws/v1/inference`,
  { headers: { Authorization: `Bearer ${apiKey}` } },
);

const taskId = randomUUID();
ws.on("open", () => {
  ws.send(JSON.stringify({
    header: { action: "run-task", task_id: taskId, streaming: "duplex" },
    payload: {
      task_group: "audio",
      task: "tts",
      function: "SpeechSynthesizer",
      model: "qwen-audio-3.0-tts-flash",
      parameters: {
        text_type: "PlainText",
        voice: "longanhuan_v3.6",
        format: "mp3",
        sample_rate: 22050,
        volume: 50,
        rate: 1,
        pitch: 1,
        enable_ssml: false,
      },
      input: {},
    },
  }));
});

ws.on("message", (data, isBinary) => {
  if (isBinary) {
    // 将音频二进制帧写入播放器或文件
    return;
  }
  const event = JSON.parse(data.toString());
  const name = event.header?.event;
  if (name === "task-started") {
    ws.send(JSON.stringify({
      header: { action: "continue-task", task_id: taskId, streaming: "duplex" },
      payload: { input: { text: "你好，这是一段实时语音合成测试。" } },
    }));
    ws.send(JSON.stringify({
      header: { action: "finish-task", task_id: taskId, streaming: "duplex" },
      payload: { input: {} },
    }));
  } else if (name === "task-finished" || name === "task-failed") {
    ws.close();
  }
});
```

生产环境还应处理 `result-generated` 音频帧、错误字段、连接超时和背压；上面的原始协议字段对应[客户端事件](https://help.aliyun.com/zh/model-studio/cosyvoice-client-events)和[服务端事件](https://help.aliyun.com/zh/model-studio/cosyvoice-server-events)，生产项目优先使用 DashScope SDK。

## 7.4 声音复刻（可选）

声音复刻需要单独的声音注册流程和账号权限，不能把任意音频直接当作 `voice` 使用。接口为：

```text
POST /api/v1/services/audio/tts/customization
```

Qwen-Audio-TTS/CosyVoice 通常使用 `voice-enrollment`，Qwen-TTS 使用 `qwen-voice-enrollment`。请求中需要指定目标模型、声音名称前缀，以及可访问的音频 URL（或按文档要求提交音频数据）：

```python
import os
import requests

base = "https://ws-1pb723s50rmgu0wh.cn-beijing.maas.aliyuncs.com/api/v1"
body = {
    "model": "voice-enrollment",
    "input": {
        "action": "create_voice",
        "target_model": "qwen-audio-3.0-tts-flash",
        "prefix": "demovoice",
        "url": "https://example.com/reference.wav",
        "language_hints": ["zh"],
    },
}
r = requests.post(
    f"{base}/services/audio/tts/customization",
    headers={"Authorization": f"Bearer {os.environ['DASHSCOPE_API_KEY']}"},
    json=body,
    timeout=60,
)
r.raise_for_status()
created_voice = r.json()
print(created_voice)
# Qwen-Audio-TTS/CosyVoice 返回 output.voice_id；审核通过后才可用于 TTS
voice_id = created_voice.get("output", {}).get("voice_id")
```

返回的声音 ID 需先在控制台或接口确认状态，再作为 TTS 请求的 `voice` 使用。音频样本、授权和合规要求以[声音复刻 HTTP API](https://help.aliyun.com/zh/model-studio/voice-clone-design-http-api)为准。

## 8. 重要限制与排错

| 现象 | 处理方式 |
|---|---|
| `401` | 检查北京 Workspace Key、Host 和计费方案是否一致 |
| `url error` | 检查模型族对应的端点；Qwen-Audio-TTS、Qwen-TTS、CosyVoice 端点不同 |
| 长音频同步调用失败 | Filetrans/Fun-ASR/Paraformer 使用 `X-DashScope-Async: enable` 异步流程 |
| ASR 返回没有 `choices` | `qwen-audio-3.0-asr-flash` 的 DashScope 返回通常读取 `output.text` |
| 实时无结果 | 必须先等待 `task-started`，再发送二进制音频帧；音频通常要求单声道 |
| 音频 URL 失效 | TTS 音频 URL、ASR 转写 URL 通常 24 小时有效，收到后立即下载 |

不要把 `Qwen-Audio` 直接改成普通 OpenAI Chat 请求；只有文档明确标注 OpenAI 兼容的 `qwen3-asr-flash` 等模型才使用 `/compatible-mode/v1/chat/completions`。[语音识别模型列表](https://help.aliyun.com/zh/model-studio/asr-model) ｜ [语音合成模型列表](https://help.aliyun.com/zh/model-studio/tts-model)
