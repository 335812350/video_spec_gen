import OpenAI from "openai";

export const HOST =
  "https://ws-1pb723s50rmgu0wh.cn-beijing.maas.aliyuncs.com";
export const OPENAI_BASE_URL = `${HOST}/compatible-mode/v1`;
export const DASHSCOPE_BASE_URL = `${HOST}/api/v1`;

function key(apiKey) {
  const value = apiKey ?? process.env.DASHSCOPE_API_KEY;
  if (!value) throw new Error("Set DASHSCOPE_API_KEY or pass apiKey explicitly");
  return value;
}

export class BailianOpenAI {
  constructor({ apiKey, baseURL = OPENAI_BASE_URL } = {}) {
    this.client = new OpenAI({ apiKey: key(apiKey), baseURL });
  }

  chat({ model, messages, ...options }) {
    return this.client.chat.completions.create({ model, messages, ...options });
  }

  embedding({ model, input, ...options }) {
    return this.client.embeddings.create({ model, input, ...options });
  }
}

export class BailianDashScope {
  constructor({ apiKey, baseURL = DASHSCOPE_BASE_URL } = {}) {
    this.apiKey = key(apiKey);
    this.baseURL = baseURL.replace(/\/$/, "");
  }

  async request(path, body, { async = false } = {}) {
    const headers = {
      Authorization: `Bearer ${this.apiKey}`,
      "Content-Type": "application/json",
    };
    if (async) headers["X-DashScope-Async"] = "enable";
    const response = await fetch(`${this.baseURL}/${path.replace(/^\//, "")}`, {
      method: "POST",
      headers,
      body: JSON.stringify(body),
    });
    const payload = await response.json();
    if (!response.ok) {
      const error = new Error(payload.message || `HTTP ${response.status}`);
      error.payload = payload;
      throw error;
    }
    return payload;
  }

  text({ model, messages, parameters = {} }) {
    return this.request("services/aigc/text-generation/generation", {
      model,
      input: { messages },
      parameters: { result_format: "message", ...parameters },
    });
  }

  multimodal({ model, messages, parameters = {} }) {
    return this.request("services/aigc/multimodal-generation/generation", {
      model,
      input: { messages },
      parameters,
    });
  }

  embedding({ model, input, parameters = {} }) {
    return this.request("services/embeddings/text-embedding/text-embedding", {
      model,
      input: { texts: Array.isArray(input) ? input : [input] },
      parameters,
    });
  }

  image({ model = "wan2.7-image-pro", messages, parameters = {} }) {
    return this.request("services/aigc/multimodal-generation/generation", {
      model,
      input: { messages },
      parameters,
    });
  }

  video({ model, input, parameters = {} }) {
    return this.request(
      "services/aigc/video-generation/video-synthesis",
      { model, input, parameters },
      { async: true },
    );
  }
}

export async function discoverModels({ apiKey, pageSize = 200 } = {}) {
  const authorization = `Bearer ${key(apiKey)}`;
  const headers = { Authorization: authorization, "Content-Type": "application/json" };
  async function getAll(path, rowKey, extra, limit) {
    const rows = [];
    let page = 1;
    let last = {};
    while (true) {
      const params = new URLSearchParams({
        ...extra,
        page_no: String(page),
        page_size: String(limit),
      });
      const response = await fetch(`${DASHSCOPE_BASE_URL}/${path}?${params}`, { headers });
      const payload = await response.json();
      if (!response.ok) throw new Error(payload.message || `HTTP ${response.status}`);
      last = payload;
      const pageRows = payload.output?.[rowKey] ?? [];
      rows.push(...pageRows);
      const total = payload.output?.total;
      if (pageRows.length === 0 || (Number.isFinite(total) && rows.length >= total)) break;
      page += 1;
    }
    return {
      ...last,
      output: { ...(last.output ?? {}), [rowKey]: rows, total: last.output?.total ?? rows.length },
    };
  }

  const [catalog, permissions] = await Promise.all([
    getAll("models", "models", { supports: "inference" }, pageSize),
    getAll(
      "models/permissions",
      "permissions",
      { authorization_scope: "AUTHORIZED", action: "INFERENCE" },
      Math.min(pageSize, 200),
    ),
  ]);
  return { catalog, permissions };
}
