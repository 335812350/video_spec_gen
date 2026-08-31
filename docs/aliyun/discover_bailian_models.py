#!/usr/bin/env python3
"""Generate a Markdown model table for the current Beijing Workspace."""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
from pathlib import Path

from bailian_client import discover_models


def _catalog_by_id(data: dict) -> dict[str, dict]:
    rows = data.get("catalog", {}).get("output", {}).get("models", [])
    return {row.get("model"): row for row in rows if row.get("model")}


def render(data: dict) -> str:
    catalog = _catalog_by_id(data)
    permissions = data.get("permissions", {}).get("output", {}).get("permissions", [])
    lines = [
        "# 当前账号可用模型",
        "",
        f"> Generated at {datetime.now(timezone.utc).isoformat()}",
        "> Source: `/api/v1/models/permissions?authorization_scope=AUTHORIZED&action=INFERENCE`",
        "",
        "| Model ID | Name | Inference | Capabilities | Features | Context | Request -> Response |",
        "|---|---|---:|---|---|---:|---|",
    ]
    for permission in permissions:
        model_id = permission.get("model", "")
        details = catalog.get(model_id, {})
        model_info = details.get("model_info") or {}
        metadata = details.get("inference_metadata") or {}
        request_modality = ", ".join(metadata.get("request_modality") or [])
        response_modality = ", ".join(metadata.get("response_modality") or [])
        lines.append(
            "| {model} | {name} | {inference} | {capabilities} | {features} | {context} | {request} -> {response} |".format(
                model=model_id,
                name=permission.get("name", details.get("name", "")),
                inference=str((permission.get("permissions") or {}).get("inference", False)).lower(),
                capabilities=", ".join(details.get("capabilities") or []),
                features=", ".join(details.get("features") or []),
                context=model_info.get("context_window", ""),
                request=request_modality,
                response=response_modality,
            )
        )
    if not permissions:
        lines.extend(["| _No authorized inference models returned_ | | | | | | |"])
    lines.extend(
        [
            "",
            "## Raw totals",
            "",
            f"- Catalog total: `{data.get('catalog', {}).get('output', {}).get('total', 0)}`",
            f"- Authorized rows: `{len(permissions)}`",
        ]
    )
    return "\n".join(lines) + "\n"


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, default=Path("bailian-models-current.md"))
    args = parser.parse_args()
    args.output.write_text(render(discover_models()), encoding="utf-8")
    print(f"Wrote {args.output}")


if __name__ == "__main__":
    main()
