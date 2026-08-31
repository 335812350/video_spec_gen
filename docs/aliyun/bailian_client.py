"""Small, dependency-light clients for the Beijing Alibaba Cloud Model Studio workspace."""

from __future__ import annotations

import json
import os
from typing import Any
from urllib.parse import urlencode
from urllib.request import Request, urlopen


HOST = "https://ws-1pb723s50rmgu0wh.cn-beijing.maas.aliyuncs.com"
OPENAI_BASE_URL = f"{HOST}/compatible-mode/v1"
DASHSCOPE_BASE_URL = f"{HOST}/api/v1"


def _key(api_key: str | None) -> str:
    value = api_key or os.getenv("DASHSCOPE_API_KEY")
    if not value:
        raise RuntimeError("Set DASHSCOPE_API_KEY or pass api_key explicitly")
    return value


class BailianOpenAI:
    """OpenAI-compatible Chat and text-embedding client."""

    def __init__(self, api_key: str | None = None, base_url: str = OPENAI_BASE_URL):
        try:
            from openai import OpenAI
        except ImportError as exc:  # pragma: no cover - depends on user environment
            raise RuntimeError("Install the dependency with: pip install -U openai") from exc
        self.client = OpenAI(api_key=_key(api_key), base_url=base_url)

    def chat(self, *, model: str, messages: list[dict[str, Any]], **kwargs: Any) -> Any:
        return self.client.chat.completions.create(model=model, messages=messages, **kwargs)

    def embedding(self, *, model: str, input: str | list[str], **kwargs: Any) -> Any:
        return self.client.embeddings.create(model=model, input=input, **kwargs)


class BailianDashScope:
    """DashScope-native text and multimodal client."""

    def __init__(self, api_key: str | None = None, base_url: str = DASHSCOPE_BASE_URL):
        try:
            import dashscope
        except ImportError as exc:  # pragma: no cover - depends on user environment
            raise RuntimeError("Install the dependency with: pip install -U dashscope") from exc
        self.api_key = _key(api_key)
        dashscope.base_http_api_url = base_url.rstrip("/")
        self._dashscope = dashscope

    def text(self, *, model: str, messages: list[dict[str, Any]], **kwargs: Any) -> Any:
        return self._dashscope.Generation.call(
            api_key=self.api_key,
            model=model,
            messages=messages,
            result_format=kwargs.pop("result_format", "message"),
            **kwargs,
        )

    def multimodal(self, *, model: str, messages: list[dict[str, Any]], **kwargs: Any) -> Any:
        return self._dashscope.MultiModalConversation.call(
            api_key=self.api_key,
            model=model,
            messages=messages,
            **kwargs,
        )

    def embedding(self, *, model: str, input: str | list[str], **kwargs: Any) -> Any:
        return self._dashscope.TextEmbedding.call(
            api_key=self.api_key,
            model=model,
            input=input,
            **kwargs,
        )


def _get_json(path: str, *, api_key: str, query: dict[str, Any] | None = None) -> dict[str, Any]:
    url = f"{DASHSCOPE_BASE_URL.rstrip('/')}/{path.lstrip('/')}"
    if query:
        url = f"{url}?{urlencode(query, doseq=True)}"
    request = Request(
        url,
        headers={
            "Authorization": f"Bearer {_key(api_key)}",
            "Content-Type": "application/json",
        },
        method="GET",
    )
    with urlopen(request, timeout=30) as response:
        return json.load(response)


def _get_all(
    path: str,
    *,
    api_key: str,
    row_key: str,
    page_size: int,
    query: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Fetch every page while retaining the API response shape."""
    base_query = dict(query or {})
    page = 1
    combined: list[dict[str, Any]] = []
    last: dict[str, Any] = {}
    total: int | None = None
    while True:
        payload = _get_json(
            path,
            api_key=api_key,
            query={**base_query, "page_no": page, "page_size": page_size},
        )
        last = payload
        output = payload.get("output") or {}
        rows = output.get(row_key) or []
        combined.extend(rows)
        total = output.get("total", total)
        if not rows or (total is not None and len(combined) >= total):
            break
        page += 1
    output = dict(last.get("output") or {})
    output[row_key] = combined
    output["total"] = total if total is not None else len(combined)
    last["output"] = output
    return last


def discover_models(api_key: str | None = None, *, page_size: int = 200) -> dict[str, Any]:
    """Return catalog and current-workspace inference permissions without exposing the key."""
    key = _key(api_key)
    catalog = _get_all(
        "/models",
        api_key=key,
        row_key="models",
        page_size=page_size,
        query={"supports": "inference"},
    )
    permissions = _get_all(
        "/models/permissions",
        api_key=key,
        row_key="permissions",
        page_size=min(page_size, 200),
        query={
            "authorization_scope": "AUTHORIZED",
            "action": "INFERENCE",
        },
    )
    return {"catalog": catalog, "permissions": permissions}


def authorized_model_ids(data: dict[str, Any]) -> list[str]:
    """Extract models with inference=true from the permissions response."""
    rows = data.get("permissions", {}).get("output", {}).get("permissions", [])
    return [
        row["model"]
        for row in rows
        if row.get("model") and row.get("permissions", {}).get("inference") is True
    ]
