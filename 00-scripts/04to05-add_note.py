#!/usr/bin/env python3
"""
將 03-notes/ 裡的 .md 筆記自動加入 docs/notes.html
用法：python3 04to05-add_note.py <筆記路徑>
"""

import sys
import re
import json
from pathlib import Path
from datetime import datetime
from typing import Optional

NOTES_HTML = Path("/Users/ting/Documents/mov_to_txt/docs/notes.html")

# 科目偵測規則：(SIDEBAR subject_id, category_id 或 None, 判斷條件)
SUBJECT_RULES = [
    {
        "subject_id": "education",
        "category_id": "statistics",
        "label": "教育研究法 > 統計",
        "filename_keywords": ["統計"],
        "content_markers": ["## 科目：統計"],
    },
    {
        "subject_id": "education",
        "category_id": "testing",
        "label": "教育研究法 > 測驗",
        "filename_keywords": ["測驗", "教育測驗"],
        "content_markers": ["## 科目：教育測驗"],
    },
    {
        "subject_id": "education",
        "category_id": "research_methods",
        "label": "教育研究法 > 研究法",
        "filename_keywords": ["研究法", "量化研究", "質性研究"],
        "content_markers": ["## 科目：研究法"],
    },
    {
        "subject_id": "psychology",
        "category_id": None,
        "label": "普通心理學",
        "filename_keywords": ["普心"],
        "content_markers": ["## 科目：普通心理學"],
    },
    {
        "subject_id": "counseling",
        "category_id": None,
        "label": "輔導原理",
        "filename_keywords": [],
        "content_markers": ["## 科目：輔導原理"],
    },
]


def detect_subject(filename: str, content: str) -> Optional[dict]:
    """根據檔名關鍵字或內文 ## 科目 標記偵測分類"""
    for rule in SUBJECT_RULES:
        # 先比對內文（更精確）
        for marker in rule["content_markers"]:
            if marker in content:
                return rule
        # 再比對檔名
        for kw in rule["filename_keywords"]:
            if kw in filename:
                return rule
    return None


def extract_title(content: str) -> str:
    """取第一行 # 標題"""
    for line in content.splitlines():
        line = line.strip()
        if line.startswith("# "):
            return line[2:].strip()
    return "（未命名筆記）"


def extract_date(filename: str) -> str:
    """從檔名取 YYYY-MM-DD"""
    m = re.match(r"(\d{4}-\d{2}-\d{2})", filename)
    return m.group(1) if m else datetime.today().strftime("%Y-%m-%d")


def note_already_exists(html: str, filename: str) -> bool:
    return f'"{filename}"' in html


def add_to_sidebar(html: str, filename: str, title: str, date: str, rule: dict) -> str:
    """在 SIDEBAR_DATA 裡找到正確位置，插入筆記條目"""
    new_entry = json.dumps({"filename": filename, "title": title, "date": date}, ensure_ascii=False)

    if rule["category_id"]:
        # 有子分類（education 底下的 statistics / testing / research_methods）
        cat_id = rule["category_id"]
        # 找到該 category 的 notes 陣列結尾 ]
        pattern = re.compile(
            r'(\{id:\s*"' + re.escape(cat_id) + r'".*?notes:\s*\[)(.*?)(\])',
            re.DOTALL,
        )
        m = pattern.search(html)
        if not m:
            print(f"✗ 找不到 category id='{cat_id}'，請確認 SIDEBAR_DATA 結構")
            sys.exit(1)
        existing_notes = m.group(2).strip()
        separator = ", " if existing_notes else ""
        replacement = m.group(1) + existing_notes + separator + new_entry + m.group(3)
        html = html[:m.start()] + replacement + html[m.end():]
    else:
        # 直接在 subject 的 notes 陣列加入
        subj_id = rule["subject_id"]
        pattern = re.compile(
            r'(\{[^{}]*id:\s*"' + re.escape(subj_id) + r'".*?notes:\s*\[)(.*?)(\])',
            re.DOTALL,
        )
        m = pattern.search(html)
        if not m:
            print(f"✗ 找不到 subject id='{subj_id}'，請確認 SIDEBAR_DATA 結構")
            sys.exit(1)
        existing_notes = m.group(2).strip()
        separator = ",\n      " if existing_notes else "\n      "
        replacement = m.group(1) + existing_notes + separator + new_entry + "\n    " + m.group(3)
        html = html[:m.start()] + replacement + html[m.end():]

    return html


def add_to_notes_content(html: str, filename: str, content: str) -> str:
    """在 NOTES_CONTENT 物件結尾插入新條目"""
    escaped = (
        content
        .replace("\\", "\\\\")
        .replace('"', '\\"')
        .replace("\n", "\\n")
    )
    first_note_pos = html.find("const FIRST_NOTE")
    insert_pos = html.rfind("};", 0, first_note_pos)
    if insert_pos == -1:
        print("✗ 找不到 NOTES_CONTENT 結尾，請確認 HTML 結構")
        sys.exit(1)
    new_entry = f', "{filename}": "{escaped}"'
    return html[:insert_pos] + new_entry + html[insert_pos:]


def main():
    if len(sys.argv) < 2:
        print("用法：python3 04to05-add_note.py <筆記路徑>")
        sys.exit(1)

    md_path = Path(sys.argv[1])
    if not md_path.exists():
        print(f"✗ 找不到檔案：{md_path}")
        sys.exit(1)

    content = md_path.read_text(encoding="utf-8")
    filename = md_path.name
    title = extract_title(content)
    date = extract_date(filename)

    # 偵測科目
    rule = detect_subject(filename, content)
    if not rule:
        print(f"✗ 無法偵測科目分類，請在筆記內文加上 '## 科目：XXX' 標記")
        sys.exit(1)

    print(f"📄 檔案：{filename}")
    print(f"📝 標題：{title}")
    print(f"📅 日期：{date}")
    print(f"📂 分類：{rule['label']}")

    html = NOTES_HTML.read_text(encoding="utf-8")

    # 檢查是否已存在
    if note_already_exists(html, filename):
        print(f"⊘ 已存在，跳過（{filename}）")
        sys.exit(0)

    # 加入 SIDEBAR_DATA
    html = add_to_sidebar(html, filename, title, date, rule)

    # 加入 NOTES_CONTENT
    html = add_to_notes_content(html, filename, content)

    NOTES_HTML.write_text(html, encoding="utf-8")
    print(f"✓ 成功加入 notes.html！")


if __name__ == "__main__":
    main()
