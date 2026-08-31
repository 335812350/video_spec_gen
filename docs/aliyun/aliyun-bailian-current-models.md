# 阿里云百炼北京 Workspace：当前账号模型表与调用封装

> 本文针对以下业务空间专属域名编写：
>
> `ws-1pb723s50rmgu0wh.cn-beijing.maas.aliyuncs.com`

## 1. 结论与边界

该域名属于百炼华北 2（北京）业务空间专属域名。两个 Base URL 是正确的：

```text
OpenAI 兼容：
https://ws-1pb723s50rmgu0wh.cn-beijing.maas.aliyuncs.com/compatible-mode/v1

DashScope 原生：
https://ws-1pb723s50rmgu0wh.cn-beijing.maas.aliyuncs.com/api/v1
```

API Key 必须同时满足：

- 北京地域创建；
- 属于 `ws-1pb723s50rmgu0wh` 这个业务空间；
- 具有目标模型的推理权限；
- 与使用的计费方案匹配。

不能根据 URL 推断“当前账号”可用模型。本文的精确模型表由接口实时生成，公共模型目录只作为参考。

官方资料：[Base URL 总览](https://help.aliyun.com/zh/model-studio/base-url)、[地域与业务空间](https://help.aliyun.com/zh/model-studio/regions/)。

## 2. 安全配置

不要把 API Key 写入代码、Markdown、Git 或聊天记录。PowerShell 临时配置：

```powershell
$env:DASHSCOPE_API_KEY = "<你的北京 Workspace API Key>"
```

永久配置请使用系统环境变量或密钥管理服务。Node.js 使用 `process.env.DASHSCOPE_API_KEY`，Python 使用 `os.environ["DASHSCOPE_API_KEY"]`。

## 3. 生成当前账号精确模型表

### 3.1 直接查询

```powershell
$bailianHost = "https://ws-1pb723s50rmgu0wh.cn-beijing.maas.aliyuncs.com"
$dashBase = "$bailianHost/api/v1"
$headers = @{ Authorization = "Bearer $env:DASHSCOPE_API_KEY" }

# 区域/平台模型目录，可按能力筛选
Invoke-RestMethod `
  "$dashBase/models?capabilities=TG&page_no=1&page_size=200" `
  -Headers $headers

# 当前 Workspace 已授权推理模型
Invoke-RestMethod `
  "$dashBase/models/permissions?authorization_scope=AUTHORIZED&action=INFERENCE&page_no=1&page_size=200" `
  -Headers $headers
```

精确可调用模型以第二个接口为准：

```text
output.permissions[].model
output.permissions[].permissions.inference == true
```

第一个接口还会返回 `capabilities`、`features`、上下文长度、模态、价格等字段。[查询模型列表](https://help.aliyun.com/zh/model-studio/list-models) ｜ [查询模型授权](https://help.aliyun.com/zh/model-studio/list-model-permissions)

### 3.2 自动生成 Markdown 表

仓库中的 `discover_bailian_models.py` 会同时查询模型目录和授权接口，并生成 `bailian-models-current.md`：

```powershell
python .\discover_bailian_models.py --output .\bailian-models-current.md
```

脚本会自动处理分页，覆盖全部返回记录。每次权限或模型开通发生变化后重新运行即可。脚本输出不会包含 API Key。

## 4. 模型能力总表

下面是当前官方目录中常见的模型族；具体 ID、地域、授权和参数以实时接口返回为准。

| 能力 | 常见模型 | 推荐协议/接口 |
|---|---|---|
| 文本对话 | `qwen3.8-max`、`qwen3.8-flash`、`qwen3.7-plus`、`qwen3.7-flash`、`qwen-plus`、`qwen-turbo` | OpenAI Chat 或 DashScope 文本 |
| 编程 | `qwen3-coder-plus`、`qwen3-coder-flash`、`qwen-coder-plus` | OpenAI Chat |
| 第三方文本 | `deepseek-v4-pro`、`deepseek-v4-flash`、`kimi-k2.6`、`glm-5.2`、`MiniMax-M2.5` | OpenAI Chat；部分模型需先开通 |
| 图像/视频理解 | `qwen3.8-max`、`qwen3.7-plus`、`qwen3.7-flash`、`qwen3-vl-plus`、`qwen3-vl-flash` | OpenAI 多模态 Chat 或 DashScope 多模态 |
| 全模态 | `qwen3.5-omni-plus`、`qwen3.5-omni-flash`、`qwen-omni-turbo` | Chat；实时语音使用 DashScope WebSocket |
| 文本向量 | `qwen3.7-text-embedding`、`text-embedding-v4`、`text-embedding-v3` | OpenAI `/embeddings` 或 DashScope |
| 多模态向量 | `qwen3-vl-embedding`、`tongyi-embedding-vision-plus` | DashScope 原生，不走 OpenAI Embeddings |
| 图片生成 | `wan2.7-image`、`wan2.7-image-pro`、`qwen-image-3.0-pro`、`z-image-turbo` | DashScope 图片专用接口 |
| 视频生成 | `wan2.7-t2v`、`wan2.7-i2v`、`wan2.7-r2v`、`happyhorse-1.1-t2v` | DashScope 视频异步接口 |
| 语音识别/合成 | `qwen-audio-3.0-asr-flash`、`qwen-audio-3.0-tts-plus`、`cosyvoice` | DashScope HTTP/WebSocket |

OpenAI 兼容 Chat 支持 Qwen、DeepSeek、Kimi、GLM、MiniMax 等模型族；`Qwen-Audio` 不支持 OpenAI 兼容协议。图片、视频生成模型也不能调用 `/chat/completions`。[OpenAI 兼容 Chat](https://help.aliyun.com/zh/model-studio/qwen-api-via-openai-chat-completions) ｜ [官方模型列表](https://help.aliyun.com/zh/model-studio/models)

## 5. Python 封装

安装依赖：

```powershell
pip install -U openai dashscope
```

使用仓库中的 `bailian_client.py`：

```python
import os
from bailian_client import BailianOpenAI, BailianDashScope

key = os.environ["DASHSCOPE_API_KEY"]

# OpenAI 兼容：文本、视觉、第三方模型、文本向量
oa = BailianOpenAI(api_key=key)
answer = oa.chat(
    model="qwen3.7-plus",
    messages=[{"role": "user", "content": "你好，请介绍一下自己"}],
)
print(answer.choices[0].message.content)

vision = oa.chat(
    model="qwen3-vl-plus",
    messages=[{
        "role": "user",
        "content": [
            {"type": "image_url", "image_url": {"url": "https://example.com/a.jpg"}},
            {"type": "text", "text": "描述这张图片"},
        ],
    }],
)
print(vision.choices[0].message.content)

embedding = oa.embedding(
    model="qwen3.7-text-embedding",
    input=["这是一段待向量化的文本"],
)
print(len(embedding.data[0].embedding))

# DashScope 原生：文本、多模态、图像/视频/音频模型
ds = BailianDashScope(api_key=key)
native = ds.text(
    model="qwen-plus",
    messages=[{"role": "user", "content": "你好"}],
)
print(native.output.choices[0].message.content)

native_vision = ds.multimodal(
    model="qwen3-vl-plus",
    messages=[{
        "role": "user",
        "content": [
            {"image": "https://example.com/a.jpg"},
            {"text": "描述这张图片"},
        ],
    }],
)
print(native_vision.output.choices[0].message.content)
```

流式文本：

```python
for chunk in oa.chat(
    model="qwen3.7-flash",
    messages=[{"role": "user", "content": "写一首短诗"}],
    stream=True,
):
    if chunk.choices:
        print(chunk.choices[0].delta.content or "", end="")
```

## 6. Node.js 封装

安装依赖：

```powershell
npm install openai
```

使用仓库中的 `bailian-client.mjs`：

```javascript
import { BailianOpenAI, BailianDashScope } from "./bailian-client.mjs";

const key = process.env.DASHSCOPE_API_KEY;
const oa = new BailianOpenAI({ apiKey: key });

const answer = await oa.chat({
  model: "qwen3.7-plus",
  messages: [{ role: "user", content: "你好，请介绍一下自己" }],
});
console.log(answer.choices[0].message.content);

const vision = await oa.chat({
  model: "qwen3-vl-plus",
  messages: [{
    role: "user",
    content: [
      { type: "image_url", image_url: { url: "https://example.com/a.jpg" } },
      { type: "text", text: "描述这张图片" },
    ],
  }],
});
console.log(vision.choices[0].message.content);

const vector = await oa.embedding({
  model: "qwen3.7-text-embedding",
  input: ["这是一段待向量化的文本"],
});
console.log(vector.data[0].embedding.length);

// 原生 DashScope 端点
const ds = new BailianDashScope({ apiKey: key });
const native = await ds.text({
  model: "qwen-plus",
  messages: [{ role: "user", content: "你好" }],
});
console.log(native.output.choices[0].message.content);
```

## 7. DashScope 专用模型接口

### 图片生成

`wan2.7-image` / `wan2.7-image-pro` 使用多模态生成接口：

```powershell
$json = @'
{
  "model": "wan2.7-image-pro",
  "input": {"messages": [{"role": "user", "content": [{"text": "一只坐在窗边的橘猫"}]}]},
  "parameters": {"size": "2K", "n": 1, "watermark": false}
}
'@

Invoke-RestMethod `
  "$dashBase/services/aigc/multimodal-generation/generation" `
  -Method Post -Headers $headers -ContentType "application/json" -Body $json
```

旧版 `wanx` / `wan2.6-t2i` 的接口可能是 `text2image/image-synthesis`，必须按模型文档选择，不能混用。

### 视频生成

`wan2.7-t2v`、`wan2.7-i2v`、`wan2.7-r2v` 使用异步任务：

```powershell
$videoBody = '{"model":"wan2.7-t2v","input":{"prompt":"一只小猫在月光下奔跑"},"parameters":{"resolution":"720P","ratio":"16:9","duration":5}}'
$created = Invoke-RestMethod `
  "$dashBase/services/aigc/video-generation/video-synthesis" `
  -Method Post -Headers ($headers + @{"X-DashScope-Async"="enable"}) `
  -ContentType "application/json" -Body $videoBody

$taskId = $created.output.task_id
Invoke-RestMethod "$dashBase/tasks/$taskId" -Headers $headers
```

任务通常需要轮询，成功后的 `video_url` 只有有限有效期，应立即下载保存。[图片生成 API](https://help.aliyun.com/zh/model-studio/wan-image-generation-and-editing-api-reference) ｜ [视频生成 API](https://help.aliyun.com/zh/model-studio/text-to-video-api-reference)

### 语音

`qwen-audio-3.0-*`、CosyVoice 等使用 DashScope 音频 HTTP 或 WebSocket 协议；实时语音使用 WebSocket，普通 TTS/ASR 使用对应音频 API。不要将这些模型改成 OpenAI Chat 请求。[语音合成](https://help.aliyun.com/zh/model-studio/tts-model)

## 8. 常见错误排查

| 错误 | 常见原因 |
|---|---|
| `401` / `InvalidApiKey` | Key 不属于北京 Workspace、地域不匹配、Key 未传或计费方案不匹配 |
| `model_not_found` | 模型 ID 拼写错误、模型未授权，或部署模型应使用部署服务 ID |
| `model_not_supported` | 该模型不支持当前协议，改用 DashScope 原生接口 |
| `url error` | 文本模型、多模态模型、图片/视频模型使用了错误 Endpoint |
| `current user api does not support http call` | 模型需要 DashScope 专用接口或 WebSocket |

如果是专属部署模型，`model` 必须填写控制台返回的部署模型 ID，而不是基础模型名称。

## 9. 官方参考

语音模型的独立调用指南见：[aliyun-bailian-voice-models.md](./aliyun-bailian-voice-models.md)

- [Base URL 总览](https://help.aliyun.com/zh/model-studio/base-url)
- [查询模型列表](https://help.aliyun.com/zh/model-studio/list-models)
- [查询模型授权](https://help.aliyun.com/zh/model-studio/list-model-permissions)
- [OpenAI 兼容 Chat](https://help.aliyun.com/zh/model-studio/qwen-api-via-openai-chat-completions)
- [DashScope API 参考](https://help.aliyun.com/zh/model-studio/qwen-api-via-dashscope)
- [向量化](https://help.aliyun.com/zh/model-studio/embedding?disableWebsiteRedirect=true)
- [图片生成](https://help.aliyun.com/zh/model-studio/wan-image-generation-and-editing-api-reference)
- [视频生成](https://help.aliyun.com/zh/model-studio/text-to-video-api-reference)
- [语音合成](https://help.aliyun.com/zh/model-studio/tts-model)
