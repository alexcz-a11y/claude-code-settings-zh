#!/usr/bin/env python3
"""Parse official Claude Code settings docs and emit site data."""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

from zh import SCOPE_ZH, TOPIC_ORDER, TOPIC_ZH, ZH

ROOT = Path(__file__).resolve().parents[1]
DOCS = Path("/tmp/claude-docs/settings-reference.md")
SCHEMA = Path("/tmp/claude-code-settings.json")
OUT = ROOT / "data" / "keys.json"

SOURCE_BASE = "https://code.claude.com/docs/en/settings-reference"


def clean_md(s: str | None) -> str | None:
    if not s:
        return None
    s = re.sub(r"\[`([^`]+)`\]\([^)]+\)", r"`\1`", s)
    s = re.sub(r"\[([^\]]+)\]\([^)]+\)", r"\1", s)
    s = s.replace("[`", "`").replace("`]", "`")
    return re.sub(r"\s+", " ", s).strip()


def strip_example_json(s: str | None) -> str | None:
    if not s:
        return None
    # Parser must not swallow the following ```json example.
    s = re.split(r'\s+"[A-Za-z.$]+":\s*', s, maxsplit=1)[0]
    return s.strip().rstrip(",")


def parse_index(text: str) -> list[dict]:
    start = text.find("| Key")
    end = text.find("\n## Model and responses")
    table = text[start:end]
    index = []
    for line in table.splitlines():
        if not line.startswith("| [`"):
            continue
        m = re.match(
            r"\| \[`([^`]+)`\]\(#([^)]+)\)\s*\|\s*(.*?)\s*\|\s*(.*?)\s*\|\s*(.*?)\s*\|",
            line,
        )
        if not m:
            raise SystemExit(f"unparsed index row: {line[:140]}")
        key, anchor, desc, topic, scope = m.groups()
        desc = re.sub(r"\[([^\]]+)\]\([^)]+\)", r"\1", desc)
        desc = re.sub(r"`([^`]+)`", r"\1", desc).strip()
        index.append(
            {
                "key": key,
                "anchor": anchor,
                "desc_en": desc,
                "topic": topic.strip(),
                "scope": scope.strip(),
            }
        )
    return index


def parse_details(text: str) -> dict[str, dict]:
    start = text.find("## Model and responses")
    parts = re.split(r"\n### `([^`]+)`\n", text[start:])
    details: dict[str, dict] = {}
    for i in range(1, len(parts), 2):
        key = parts[i]
        body = parts[i + 1]
        lines = body.splitlines()
        scope = type_ = default = overrides = None
        extra: list[str] = []
        current = None
        for ln in lines:
            if ln.startswith("```") or ln.startswith("## "):
                break
            m = re.match(
                r"^\* \*\*(Scope|Type|Default|Per-session overrides)\*\*:\s*(.*)$",
                ln,
            )
            if m:
                current = m.group(1)
                val = m.group(2)
                if current == "Scope":
                    scope = val
                elif current == "Type":
                    type_ = val
                elif current == "Default":
                    default = val
                else:
                    overrides = val
                continue
            if current == "Type" and ln.startswith("  * "):
                extra.append(ln.strip()[2:].strip())
                continue
            if current and ln.startswith("* **"):
                current = None
                continue
            if current in ("Type", "Default", "Scope", "Per-session overrides") and ln.startswith("  "):
                add = " " + ln.strip()
                if current == "Type":
                    type_ = (type_ or "") + add
                elif current == "Default":
                    default = (default or "") + add
                elif current == "Scope":
                    scope = (scope or "") + add
                else:
                    overrides = (overrides or "") + add

        paras, buf = [], []
        for ln in lines:
            if ln.startswith("* **") or ln.startswith("```") or ln.startswith("## ") or ln.startswith("### "):
                break
            if ln.startswith("<"):
                continue
            if not ln.strip():
                if buf:
                    paras.append(" ".join(buf))
                    buf = []
                continue
            buf.append(ln.strip())
        if buf:
            paras.append(" ".join(buf))
        meaning = clean_md(paras[0] if paras else "") or ""

        details[key] = {
            "scope_detail": clean_md(scope),
            "type": clean_md(type_),
            "type_values": [clean_md(x) for x in extra if clean_md(x)],
            "default": strip_example_json(clean_md(default)),
            "overrides": clean_md(overrides),
            "meaning_en": meaning,
        }
    return details


def numeric_note(key: str, typ: str | None, default: str | None, type_values: list[str]) -> str | None:
    """Only restate official numeric / unit facts. Never invent min/max."""
    blob = " ".join(x for x in [typ or "", default or "", " ".join(type_values)] if x)
    notes = {
        "cleanupPeriodDays": "官方：天为单位的整数，最小 1，默认 30。设为 0 无法通过校验；长期保留可用如 3650。",
        "autoCompactWindow": "官方：token 数量，范围 100000 到 1000000；会再封顶到当前模型上下文窗口。默认未设置，由 Claude Code 按模型选择。",
        "feedbackSurveyRate": "官方：0 到 1 之间的概率。设为 0 关闭问卷。默认未设置，使用 Anthropic 远程配置的频率；Bedrock / Agent Platform / Foundry 上内置 0.005。",
        "skillListingBudgetFraction": "官方：大于 0 且至多 1 的分数。默认 0.01，即预留上下文窗口的 1%。",
        "skillListingMaxDescChars": "官方：正整数，单位是字符。默认 1536。",
        "policyHelper.timeoutMs": "官方：整数毫秒，最小 1000。默认 10000。",
        "policyHelper.refreshIntervalMs": "官方：整数毫秒。0 关闭刷新；否则至少 60000。默认未设置，只在启动时运行一次。",
        "sandbox.network.httpProxyPort": "官方：本地 TCP 端口号。默认未设置，由 Claude Code 自己跑 HTTP 代理。",
        "sandbox.network.socksProxyPort": "官方：本地 TCP 端口号。默认未设置，由 Claude Code 自己跑 SOCKS 代理。",
        "promptCacheTtl": "官方取值是字符串 \"5m\" 或 \"1h\"，不是原始数字。默认未设置，沿用各请求自己的默认寿命。",
        "subagentPromptCacheTtl": "官方取值是字符串 \"5m\" 或 \"1h\"，不是原始数字。默认未设置，沿用各请求自己的默认寿命。",
        "workflowSizeGuideline": "官方是代理数量档位，不是原始数字：\"small\" 少于 5 个代理，\"medium\" 少于 15，\"large\" 少于 50，\"unrestricted\" 无指引。默认 \"medium\"。这是给模型的建议，不是强制上限。",
        "alwaysThinkingEnabled": "相关环境变量 MAX_THINKING_TOKENS：官方写明 0 表示关闭思考；正值即使本键为 false 也会打开思考。自适应推理模型会忽略该数字本身。",
        "askUserQuestionTimeout": "官方枚举是 \"60s\"、\"5m\"、\"10m\" 或 \"never\"，不是原始毫秒数。默认 \"never\"。",
        "dialogExpiry": "官方枚举是 \"60s\"、\"5m\"、\"10m\" 或 \"never\"（关闭截止）。默认 \"5m\"。",
    }
    if key in notes:
        return notes[key]
    if re.search(r"milliseconds|number of (days|tokens|characters)|TCP port|fraction|minimum `?\d", blob, re.I):
        return f"官方类型说明：{typ}" if typ else "未在官方文档写明"
    return None


def files_for_scope(scope: str) -> list[str]:
    if scope == "Any file":
        return ["user", "project", "local", "managed"]
    if scope == "User or managed":
        return ["user", "managed"]
    if scope == "User, local, or managed":
        return ["user", "local", "managed"]
    if scope == "Managed":
        return ["managed"]
    if scope == "Global config":
        return ["global"]
    return []


def main() -> None:
    text = DOCS.read_text()
    index = parse_index(text)
    details = parse_details(text)
    missing_zh = [row["key"] for row in index if row["key"] not in ZH]
    missing_detail = [row["key"] for row in index if row["key"] not in details]
    if missing_zh or missing_detail:
        print("missing zh", missing_zh, file=sys.stderr)
        print("missing detail", missing_detail, file=sys.stderr)
        raise SystemExit(1)

    schema_keys = set()
    if SCHEMA.exists():
        schema = json.loads(SCHEMA.read_text())
        schema_keys = set(schema.get("properties", {}))

    keys = []
    incomplete = []
    for row in index:
        det = details[row["key"]]
        zh_name, zh_meaning = ZH[row["key"]]
        typ = det.get("type")
        default = det.get("default")
        if not typ or not default:
            incomplete.append(row["key"])
        keys.append(
            {
                "key": row["key"],
                "anchor": row["anchor"],
                "zhName": zh_name,
                "zhMeaning": zh_meaning,
                "descEn": row["desc_en"],
                "meaningEn": det.get("meaning_en") or row["desc_en"],
                "type": typ or "未在官方文档写明",
                "typeValues": det.get("type_values") or [],
                "default": default or "未在官方文档写明",
                "scope": row["scope"],
                "scopeZh": SCOPE_ZH.get(row["scope"], row["scope"]),
                "scopeDetail": det.get("scope_detail"),
                "files": files_for_scope(row["scope"]),
                "topic": row["topic"],
                "topicZh": TOPIC_ZH[row["topic"]],
                "overrides": det.get("overrides"),
                "numeric": numeric_note(row["key"], typ, default, det.get("type_values") or []),
                "source": f"{SOURCE_BASE}#{row['anchor']}",
                "kind": "global" if row["scope"] == "Global config" else "settings",
                "inSchema": row["key"].split(".")[0] in schema_keys,
            }
        )

    index_tops = {k["key"].split(".")[0] for k in keys}
    schema_only = sorted(schema_keys - index_tops - {"$schema"})

    payload = {
        "fetchedDate": "2026-08-26",
        "officialIndexCount": len(keys),
        "documentedCount": len(keys),
        "incompleteOfficial": incomplete,
        "schemaOnlyKeys": [
            {
                "key": k,
                "note": "出现在 json.schemastore.org/claude-code-settings.json，但未列入官方 All settings 索引。未在官方文档写明类型与默认值，本页不猜测枚举。",
                "source": "https://json.schemastore.org/claude-code-settings.json",
            }
            for k in schema_only
        ],
        "schemaLagNote": "JSON Schema 可能落后于 CLI。官方 All settings 索引里有若干键尚未出现在 schema 顶层。",
        "topics": [{"id": t, "zh": TOPIC_ZH[t]} for t in TOPIC_ORDER],
        "keys": keys,
        "sources": [
            "https://code.claude.com/docs/en/settings-reference",
            "https://code.claude.com/docs/en/settings",
            "https://code.claude.com/docs/en/settings-example",
            "https://code.claude.com/docs/en/claude-directory",
            "https://code.claude.com/docs/en/permissions",
            "https://code.claude.com/docs/en/permission-modes",
            "https://json.schemastore.org/claude-code-settings.json",
            "https://code.claude.com/docs/en/data-usage",
            "https://code.claude.com/docs/en/context-window",
            "https://code.claude.com/docs/en/prompt-caching",
            "https://code.claude.com/docs/en/sandboxing",
            "https://code.claude.com/docs/en/model-config",
            "https://code.claude.com/docs/en/managed-settings",
        ],
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n")
    print(f"wrote {OUT} keys={len(keys)} incomplete={incomplete} schema_only={schema_only}")


if __name__ == "__main__":
    main()
