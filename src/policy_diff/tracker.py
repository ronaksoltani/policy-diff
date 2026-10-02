from __future__ import annotations

import hashlib
import html
import json
import re
from datetime import datetime, timezone
from difflib import HtmlDiff, unified_diff
from pathlib import Path
from urllib.parse import urlparse

import requests
from bs4 import BeautifulSoup

MAX_RESPONSE_BYTES = 5 * 1024 * 1024


def normalize_html(document: str) -> str:
    soup = BeautifulSoup(document, "html.parser")
    for node in soup.select("script, style, noscript, svg, nav, footer, header"):
        node.decompose()
    lines = [re.sub(r"\s+", " ", line).strip() for line in soup.get_text("\n").splitlines()]
    return "\n".join(line for line in lines if line)


def _safe_url_key(url: str) -> str:
    parsed = urlparse(url)
    if parsed.scheme not in {"http", "https"} or not parsed.netloc:
        raise ValueError("URL must be an absolute http(s) URL")
    return hashlib.sha256(url.encode("utf-8")).hexdigest()[:20]


def fetch_text(url: str, timeout: float = 15) -> str:
    response = requests.get(url, timeout=timeout, headers={"User-Agent": "PolicyDiffTracker/1.0 (+local monitoring)"}, stream=True)
    response.raise_for_status()
    chunks: list[bytes] = []
    size = 0
    for chunk in response.iter_content(32_768):
        size += len(chunk)
        if size > MAX_RESPONSE_BYTES:
            raise ValueError("page exceeds the 5 MiB response limit")
        chunks.append(chunk)
    return normalize_html(b"".join(chunks).decode(response.encoding or "utf-8", errors="replace"))


def compare_snapshots(before: str, after: str) -> tuple[str, str]:
    old_lines, new_lines = before.splitlines(), after.splitlines()
    unified = "\n".join(unified_diff(old_lines, new_lines, fromfile="previous", tofile="current", lineterm=""))
    side_by_side = HtmlDiff(wrapcolumn=90).make_file(old_lines, new_lines,
        fromdesc="Previous snapshot", todesc="Current snapshot", context=True, numlines=3)
    return unified, side_by_side


def check_url(url: str, state_dir: Path) -> dict[str, str | bool]:
    key = _safe_url_key(url)
    state_dir.mkdir(parents=True, exist_ok=True)
    state_path = state_dir / f"{key}.json"
    current = fetch_text(url)
    digest = hashlib.sha256(current.encode("utf-8")).hexdigest()
    now = datetime.now(timezone.utc).isoformat()
    if not state_path.exists():
        state_path.write_text(json.dumps({"url": url, "sha256": digest, "checked_at": now, "text": current}, indent=2), encoding="utf-8")
        return {"status": "baseline", "changed": False, "report": ""}
    previous = json.loads(state_path.read_text(encoding="utf-8"))
    if previous.get("sha256") == digest:
        return {"status": "unchanged", "changed": False, "report": ""}
    unified, side_by_side = compare_snapshots(previous.get("text", ""), current)
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    report_path = state_dir / f"{key}-{stamp}.html"
    report_path.write_text(side_by_side, encoding="utf-8")
    diff_path = state_dir / f"{key}-{stamp}.diff"
    diff_path.write_text(unified + "\n", encoding="utf-8")
    state_path.write_text(json.dumps({"url": url, "sha256": digest, "checked_at": now, "text": current}, indent=2), encoding="utf-8")
    return {"status": "changed", "changed": True, "report": str(report_path), "diff": str(diff_path)}
