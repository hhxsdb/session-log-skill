#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import re
from datetime import datetime
from pathlib import Path


FILENAME = "session-log.md"
OVERVIEW_START = "<!-- SESSION_OVERVIEW_START -->"
OVERVIEW_END = "<!-- SESSION_OVERVIEW_END -->"
ENTRIES_START = "<!-- SESSION_ENTRIES_START -->"
ENTRIES_END = "<!-- SESSION_ENTRIES_END -->"
TEXT_ENCODING = "utf-8-sig"
STATUS_ALIASES = {
    "in-progress": "进行中",
    "completed": "已完成",
    "blocked": "阻塞中",
    "partial": "部分完成",
}
PHASE_ALIASES = {
    "init": "已初始化会话日志",
    "requirements": "需求确认",
    "implementing": "实现中",
    "testing": "测试中",
    "wrap-up": "已收尾",
}


def now_text() -> str:
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def log_path(cwd: str | None) -> Path:
    base = Path(cwd).resolve() if cwd else Path.cwd().resolve()
    return base / FILENAME


def default_content(target: Path, timestamp: str) -> str:
    return f"""# Session Log

{OVERVIEW_START}
## 会话概览
- 创建时间：{timestamp}
- 最近更新时间：{timestamp}
- 当前项目目录：{target.parent}
- 当前状态：进行中
- 当前阶段：已初始化会话日志
- 累计记录数：0
{OVERVIEW_END}

---

{ENTRIES_START}
{ENTRIES_END}
"""


def ensure_file(path: Path) -> tuple[bool, str]:
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists():
        text = path.read_text(encoding=TEXT_ENCODING)
        if OVERVIEW_START not in text or OVERVIEW_END not in text or ENTRIES_START not in text or ENTRIES_END not in text:
            timestamp = now_text()
            path.write_text(default_content(path, timestamp), encoding=TEXT_ENCODING, newline="\n")
            return True, "文件存在但结构不完整，已重建为标准结构"
        return False, "文件已存在"
    timestamp = now_text()
    path.write_text(default_content(path, timestamp), encoding=TEXT_ENCODING, newline="\n")
    return True, "已创建新日志文件"


def extract_value(text: str, label: str) -> str | None:
    pattern = rf"^- {re.escape(label)}：\s*(.*)$"
    match = re.search(pattern, text, re.MULTILINE)
    return match.group(1).strip() if match else None


def count_entries(text: str) -> int:
    if ENTRIES_START not in text or ENTRIES_END not in text:
        return 0
    section = text.split(ENTRIES_START, 1)[1].split(ENTRIES_END, 1)[0]
    return len(re.findall(r"^## \d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}$", section, re.MULTILINE))


def normalize_status(value: str | None) -> str | None:
    if value is None:
        return None
    return STATUS_ALIASES.get(value, value)


def normalize_phase(value: str | None, phase_code: str | None) -> str | None:
    if value:
        return value
    if phase_code:
        return PHASE_ALIASES.get(phase_code, phase_code)
    return None


def overview_block(path: Path, text: str) -> str:
    created = extract_value(text, "创建时间") or now_text()
    updated = extract_value(text, "最近更新时间") or now_text()
    project_dir = extract_value(text, "当前项目目录") or str(path.parent)
    status = extract_value(text, "当前状态") or "进行中"
    phase = extract_value(text, "当前阶段") or "已初始化会话日志"
    entry_count = count_entries(text)
    return "\n".join(
        [
            OVERVIEW_START,
            "## 会话概览",
            f"- 创建时间：{created}",
            f"- 最近更新时间：{updated}",
            f"- 当前项目目录：{project_dir}",
            f"- 当前状态：{status}",
            f"- 当前阶段：{phase}",
            f"- 累计记录数：{entry_count}",
            OVERVIEW_END,
        ]
    )


def rebuild_overview(
    text: str,
    path: Path,
    *,
    status: str | None = None,
    phase: str | None = None,
    updated_at: str | None = None,
) -> str:
    if OVERVIEW_START not in text or OVERVIEW_END not in text:
        text = default_content(path, now_text())
    current_created = extract_value(text, "创建时间") or now_text()
    current_project_dir = extract_value(text, "当前项目目录") or str(path.parent)
    current_status = extract_value(text, "当前状态") or "进行中"
    current_phase = extract_value(text, "当前阶段") or "已初始化会话日志"
    new_updated = updated_at or now_text()
    new_status = status or current_status
    new_phase = phase or current_phase
    entry_count = count_entries(text)
    new_block = "\n".join(
        [
            OVERVIEW_START,
            "## 会话概览",
            f"- 创建时间：{current_created}",
            f"- 最近更新时间：{new_updated}",
            f"- 当前项目目录：{current_project_dir}",
            f"- 当前状态：{new_status}",
            f"- 当前阶段：{new_phase}",
            f"- 累计记录数：{entry_count}",
            OVERVIEW_END,
        ]
    )
    pattern = rf"{re.escape(OVERVIEW_START)}.*?{re.escape(OVERVIEW_END)}"
    return re.sub(pattern, lambda _: new_block, text, count=1, flags=re.DOTALL)


def cmd_init(args: argparse.Namespace) -> int:
    path = log_path(args.cwd)
    changed, message = ensure_file(path)
    text = path.read_text(encoding=TEXT_ENCODING)
    text = rebuild_overview(text, path)
    path.write_text(text, encoding=TEXT_ENCODING, newline="\n")
    payload = {
        "ok": True,
        "path": str(path),
        "changed": changed,
        "message": message,
    }
    print(json.dumps(payload, ensure_ascii=True, indent=2))
    return 0


def cmd_status(args: argparse.Namespace) -> int:
    path = log_path(args.cwd)
    exists = path.exists()
    if not exists:
        payload = {
            "ok": True,
            "path": str(path),
            "exists": False,
            "overview_exists": False,
            "entry_count": 0,
        }
        print(json.dumps(payload, ensure_ascii=True, indent=2))
        return 0
    text = path.read_text(encoding=TEXT_ENCODING)
    payload = {
        "ok": True,
        "path": str(path),
        "exists": True,
        "overview_exists": OVERVIEW_START in text and OVERVIEW_END in text,
        "entry_count": count_entries(text),
        "created_at": extract_value(text, "创建时间"),
        "updated_at": extract_value(text, "最近更新时间"),
        "project_dir": extract_value(text, "当前项目目录"),
        "current_status": extract_value(text, "当前状态"),
        "current_phase": extract_value(text, "当前阶段"),
    }
    print(json.dumps(payload, ensure_ascii=True, indent=2))
    return 0


def cmd_update_overview(args: argparse.Namespace) -> int:
    path = log_path(args.cwd)
    ensure_file(path)
    text = path.read_text(encoding=TEXT_ENCODING)
    normalized_status = normalize_status(args.status)
    normalized_phase = normalize_phase(args.phase, args.phase_code)
    text = rebuild_overview(
        text,
        path,
        status=normalized_status,
        phase=normalized_phase,
        updated_at=args.updated_at,
    )
    path.write_text(text, encoding=TEXT_ENCODING, newline="\n")
    payload = {
        "ok": True,
        "path": str(path),
        "updated_at": extract_value(text, "最近更新时间"),
        "current_status": extract_value(text, "当前状态"),
        "current_phase": extract_value(text, "当前阶段"),
        "entry_count": count_entries(text),
    }
    print(json.dumps(payload, ensure_ascii=True, indent=2))
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Session log helper for UTF-8 Chinese Markdown logs.")
    parser.add_argument("--cwd", help="工作目录；默认使用当前目录")
    subparsers = parser.add_subparsers(dest="command", required=True)

    init_parser = subparsers.add_parser("init", help="创建或初始化 session-log.md")
    init_parser.set_defaults(func=cmd_init)

    status_parser = subparsers.add_parser("status", help="查看当前日志状态")
    status_parser.set_defaults(func=cmd_status)

    update_parser = subparsers.add_parser("update-overview", help="更新顶部概览")
    update_parser.add_argument("--status", help="新的当前状态；可传中文，或用 in-progress/completed/blocked/partial")
    update_parser.add_argument("--phase", help="新的当前阶段；建议直接传中文")
    update_parser.add_argument("--phase-code", help="阶段英文别名：init/requirements/implementing/testing/wrap-up")
    update_parser.add_argument("--updated-at", help="覆盖最近更新时间，格式 YYYY-MM-DD HH:MM:SS")
    update_parser.set_defaults(func=cmd_update_overview)

    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
