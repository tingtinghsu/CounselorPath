#!/usr/bin/env python3
"""
備考網站生成器
從 03-notes/ 讀取 Markdown 筆記，生成靜態 study_site/index.html
執行: python3 build_site.py
"""

import json
import re
import sys
from pathlib import Path

NOTES_DIR   = Path("/Users/ting/Documents/mov_to_txt/03-notes")
SITE_DIR    = Path("/Users/ting/Documents/mov_to_txt/docs")
CONFIG_FILE = Path("/Users/ting/Documents/mov_to_txt/notes_config.json")

SUBJECTS = [
    {"id": "education",     "name": "教育研究法", "sub": "統計・測驗・研究法"},
    {"id": "psychology",    "name": "普通心理學", "sub": ""},
    {"id": "counseling",    "name": "輔導原理",   "sub": ""},
    {"id": "english",       "name": "英文",       "sub": ""},
    {"id": "uncategorized", "name": "未分類",     "sub": ""},
]

KEYWORDS = {
    "education":  r"研究法|統計|測驗|量化|質化|描述性研究|實驗設計|問卷|信度|效度|常模|標準化",
    "psychology": r"心理學|Freud|佛洛伊德|精神分析|人格結構|認知|發展階段|記憶|學習|動機|情緒|Jung|Adler",
    "counseling": r"輔導|諮商|治療|敘事|後現代|個案概念|會談|同理心|Rogers|完形|SFBT|溝通分析",
    "english":    r"英文|English|vocabulary|grammar|托福|雅思",
}


SUBJECT_TAG_MAP = {
    "教育研究法": "education",
    "普通心理學": "psychology",
    "輔導原理":   "counseling",
    "英文":       "english",
}

def detect_subject(title: str, content: str) -> str:
    # 優先偵測筆記內的「科目：XXX」標記
    m = re.search(r"科目[：:]\s*(.+)", content)
    if m:
        tag = m.group(1).strip()
        for name, sid in SUBJECT_TAG_MAP.items():
            if name in tag:
                return sid

    text = title + " " + content[:500]
    for subject_id, pattern in KEYWORDS.items():
        if re.search(pattern, text):
            return subject_id
    return "uncategorized"


def extract_title(content: str, filename: str) -> str:
    for line in content.splitlines():
        line = line.strip()
        if line.startswith("# "):
            return line[2:].strip()
    stem = Path(filename).stem
    # Remove timestamp prefix
    stem = re.sub(r"^\d{4}-\d{2}-\d{2} \d{2}-\d{2}-\d{2}-?", "", stem).strip()
    return stem or Path(filename).stem


def extract_date(filename: str) -> str:
    m = re.match(r"(\d{4}-\d{2}-\d{2})", filename)
    return m.group(1) if m else ""


def load_config() -> dict:
    if CONFIG_FILE.exists():
        return json.loads(CONFIG_FILE.read_text(encoding="utf-8"))
    return {}


def save_config(config: dict):
    CONFIG_FILE.write_text(
        json.dumps(config, ensure_ascii=False, indent=2), encoding="utf-8"
    )


def build():
    SITE_DIR.mkdir(exist_ok=True)

    md_files = sorted(NOTES_DIR.glob("*.md"))
    if not md_files:
        print(f"在 {NOTES_DIR} 找不到 .md 筆記")
        sys.exit(0)

    config = load_config()
    updated = False

    notes_by_subject: dict = {s["id"]: [] for s in SUBJECTS}

    for md_file in md_files:
        content = md_file.read_text(encoding="utf-8")
        title   = extract_title(content, md_file.name)
        date    = extract_date(md_file.name)

        if md_file.name not in config:
            config[md_file.name] = detect_subject(title, content)
            updated = True

        subject_id = config[md_file.name]
        if subject_id not in notes_by_subject:
            subject_id = "uncategorized"

        notes_by_subject[subject_id].append({
            "filename": md_file.name,
            "title":    title,
            "date":     date,
            "content":  content,
        })

    if updated:
        save_config(config)
        print(f"已更新 notes_config.json（可手動調整每篇筆記的科目分類）")

    # Build sidebar data for JS
    sidebar_data = []
    for subj in SUBJECTS:
        notes = notes_by_subject[subj["id"]]
        if not notes:
            continue
        sidebar_data.append({
            "id":    subj["id"],
            "name":  subj["name"],
            "sub":   subj["sub"],
            "notes": [{"filename": n["filename"], "title": n["title"], "date": n["date"]}
                      for n in notes],
        })

    # Build notes content map for JS (escape for JSON embedding)
    notes_content = {n["filename"]: n["content"]
                     for notes in notes_by_subject.values() for n in notes}

    js_sidebar  = json.dumps(sidebar_data, ensure_ascii=False)
    js_content  = json.dumps(notes_content, ensure_ascii=False)

    # Find first note filename
    first_note = ""
    for subj in sidebar_data:
        if subj["notes"]:
            first_note = subj["notes"][0]["filename"]
            break

    html = HTML_TEMPLATE.replace("__SIDEBAR_DATA__", js_sidebar)
    html = html.replace("__NOTES_CONTENT__", js_content)
    html = html.replace("__FIRST_NOTE__", first_note)

    out = SITE_DIR / "index.html"
    out.write_text(html, encoding="utf-8")

    # 告訴 GitHub Pages 不要用 Jekyll 處理，直接發布 HTML
    (SITE_DIR / ".nojekyll").touch()

    print(f"✓ 網站已生成: {out}")
    print(f"  本機預覽: open {out}")
    print(f"  部署: git add docs/ && git commit -m 'update notes' && git push")


# ── HTML Template ─────────────────────────────────────────────────────────────

HTML_TEMPLATE = r"""<!DOCTYPE html>
<html lang="zh-TW">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>諮商所備考筆記</title>
<script src="https://cdn.jsdelivr.net/npm/marked/marked.min.js"></script>
<script src="https://cdn.jsdelivr.net/npm/markmap-autoloader@0.17.0"></script>
<style>
:root {
  --sidebar-width: 280px;
  --header-height: 56px;
  --accent: #2869e6;
  --accent-light: #e8f0fe;
  --sidebar-bg: #f8f9fa;
  --border: #e1e4e8;
  --text: #24292e;
  --text-muted: #586069;
  --code-bg: #f6f8fa;
}

* { box-sizing: border-box; margin: 0; padding: 0; }

body {
  font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
  color: var(--text);
  background: #fff;
}

/* ── Header ── */
.header {
  position: fixed; top: 0; left: 0; right: 0;
  height: var(--header-height);
  background: var(--accent);
  display: flex; align-items: center; padding: 0 20px;
  z-index: 100;
  box-shadow: 0 1px 4px rgba(0,0,0,.2);
}
.header h1 {
  color: #fff; font-size: 18px; font-weight: 600; letter-spacing: .3px;
}
.header-sub {
  color: rgba(255,255,255,.75); font-size: 13px; margin-left: 12px;
}

/* ── Layout ── */
.layout {
  display: flex;
  margin-top: var(--header-height);
  min-height: calc(100vh - var(--header-height));
}

/* ── Sidebar ── */
.sidebar {
  width: var(--sidebar-width);
  min-width: var(--sidebar-width);
  background: var(--sidebar-bg);
  border-right: 1px solid var(--border);
  padding: 20px 0;
  position: sticky;
  top: var(--header-height);
  height: calc(100vh - var(--header-height));
  overflow-y: auto;
}

.sidebar-subject {
  margin-bottom: 6px;
}
.sidebar-subject-header {
  display: flex; align-items: center;
  padding: 8px 20px;
  cursor: pointer;
  user-select: none;
  gap: 8px;
}
.sidebar-subject-header:hover { background: rgba(0,0,0,.04); }

.subject-icon {
  width: 28px; height: 28px; border-radius: 6px;
  display: flex; align-items: center; justify-content: center;
  font-size: 14px; flex-shrink: 0;
}
.subject-label { flex: 1; }
.subject-name {
  font-size: 13px; font-weight: 600; color: var(--text);
  display: block; line-height: 1.2;
}
.subject-sub {
  font-size: 11px; color: var(--text-muted); display: block;
}
.subject-toggle {
  font-size: 10px; color: var(--text-muted);
  transition: transform .2s;
}
.sidebar-subject.open .subject-toggle { transform: rotate(90deg); }

.sidebar-notes {
  display: none; padding: 0 0 4px 0;
}
.sidebar-subject.open .sidebar-notes { display: block; }

.note-link {
  display: block; padding: 6px 20px 6px 56px;
  font-size: 13px; color: var(--text-muted);
  text-decoration: none; cursor: pointer;
  border-left: 3px solid transparent;
  line-height: 1.4;
}
.note-link:hover { background: rgba(0,0,0,.04); color: var(--text); }
.note-link.active {
  background: var(--accent-light);
  color: var(--accent);
  border-left-color: var(--accent);
  font-weight: 500;
}
.note-date {
  display: block; font-size: 11px; color: #999; margin-top: 1px;
}

/* ── Main Content ── */
.main {
  flex: 1;
  padding: 40px 48px;
  max-width: 860px;
  overflow: hidden;
}

.note-title-bar {
  margin-bottom: 32px;
  padding-bottom: 16px;
  border-bottom: 1px solid var(--border);
}
.note-subject-tag {
  display: inline-block;
  padding: 2px 10px; border-radius: 12px;
  font-size: 12px; font-weight: 500; margin-bottom: 8px;
}

/* ── Markdown Styles ── */
.content h1 { font-size: 26px; margin: 32px 0 16px; line-height: 1.3; }
.content h2 { font-size: 20px; margin: 28px 0 12px; padding-bottom: 6px; border-bottom: 1px solid var(--border); }
.content h3 { font-size: 16px; margin: 20px 0 8px; }
.content h4 { font-size: 14px; margin: 16px 0 6px; }
.content p  { margin: 10px 0; line-height: 1.8; font-size: 15px; }
.content ul, .content ol { margin: 8px 0 8px 24px; }
.content li { margin: 4px 0; line-height: 1.7; font-size: 15px; }
.content li > ul { margin-top: 4px; }

.content table {
  border-collapse: collapse; width: 100%; margin: 16px 0; font-size: 14px;
}
.content th {
  background: var(--code-bg); padding: 8px 12px;
  border: 1px solid var(--border); font-weight: 600; text-align: left;
}
.content td {
  padding: 8px 12px; border: 1px solid var(--border);
}
.content tr:nth-child(even) td { background: #fafafa; }

.content code {
  background: var(--code-bg); padding: 2px 6px; border-radius: 3px;
  font-size: 13px; font-family: "SFMono-Regular", Consolas, monospace;
}
.content pre {
  background: var(--code-bg); padding: 16px; border-radius: 6px;
  overflow-x: auto; margin: 12px 0; border: 1px solid var(--border);
}
.content pre code { background: none; padding: 0; font-size: 13px; }

.content blockquote {
  border-left: 4px solid var(--accent); padding: 4px 16px;
  margin: 12px 0; color: var(--text-muted); background: var(--accent-light);
  border-radius: 0 4px 4px 0;
}

.content strong { font-weight: 600; }
.content hr { border: none; border-top: 1px solid var(--border); margin: 24px 0; }

/* ── Subject Colors ── */
.education  { background: #e3f2fd; color: #1565c0; }
.psychology { background: #f3e5f5; color: #6a1b9a; }
.counseling { background: #e8f5e9; color: #2e7d32; }
.english    { background: #fff3e0; color: #e65100; }
.uncategorized { background: #f5f5f5; color: #616161; }

.icon-education  { background: #bbdefb; }
.icon-psychology { background: #e1bee7; }
.icon-counseling { background: #c8e6c9; }
.icon-english    { background: #ffe0b2; }
.icon-uncategorized { background: #eeeeee; }

/* ── Empty state ── */
.empty {
  text-align: center; padding: 80px 40px;
  color: var(--text-muted);
}
.empty-icon { font-size: 48px; margin-bottom: 16px; }

/* ── Mind Map ── */
.mindmap-section {
  margin-top: 48px;
  border-top: 2px dashed var(--border);
  padding-top: 32px;
}
.mindmap-header {
  display: flex; align-items: center; gap: 12px; margin-bottom: 16px;
}
.mindmap-header h2 {
  font-size: 18px; font-weight: 600; border: none !important; margin: 0 !important; padding: 0 !important;
}
.mindmap-toggle {
  background: var(--accent); color: #fff;
  border: none; border-radius: 6px; padding: 6px 14px;
  font-size: 13px; cursor: pointer; font-weight: 500;
}
.mindmap-toggle:hover { background: #1a56d4; }
.mindmap-wrap {
  border: 1px solid var(--border); border-radius: 8px;
  overflow: hidden; background: #fafeff;
}
.mindmap-wrap svg { display: block; }

/* ── Scrollbar ── */
.sidebar::-webkit-scrollbar { width: 4px; }
.sidebar::-webkit-scrollbar-track { background: transparent; }
.sidebar::-webkit-scrollbar-thumb { background: #ccc; border-radius: 2px; }
</style>
</head>
<body>

<header class="header">
  <h1>📚 諮商所備考筆記</h1>
  <span class="header-sub">研究所入學考試 · 上課筆記整理</span>
</header>

<div class="layout">
  <nav class="sidebar" id="sidebar"></nav>
  <main class="main" id="main">
    <div class="empty">
      <div class="empty-icon">📖</div>
      <p>從左側選擇筆記開始複習</p>
    </div>
  </main>
</div>

<script>
const SIDEBAR_DATA  = __SIDEBAR_DATA__;
const NOTES_CONTENT = __NOTES_CONTENT__;
const FIRST_NOTE    = "__FIRST_NOTE__";

const SUBJECT_ICONS = {
  education:     "📊",
  psychology:    "🧠",
  counseling:    "💬",
  english:       "📝",
  uncategorized: "📄",
};

const SUBJECT_LABELS = {
  education:     "教育研究法",
  psychology:    "普通心理學",
  counseling:    "輔導原理",
  english:       "英文",
  uncategorized: "未分類",
};

// ── Build sidebar ──
function buildSidebar() {
  const sidebar = document.getElementById("sidebar");
  SIDEBAR_DATA.forEach(subj => {
    const div = document.createElement("div");
    div.className = "sidebar-subject";
    div.dataset.id = subj.id;
    div.innerHTML = `
      <div class="sidebar-subject-header" onclick="toggleSubject('${subj.id}')">
        <div class="subject-icon icon-${subj.id}">${SUBJECT_ICONS[subj.id] || "📄"}</div>
        <div class="subject-label">
          <span class="subject-name">${subj.name}</span>
          ${subj.sub ? `<span class="subject-sub">${subj.sub}</span>` : ""}
        </div>
        <span class="subject-toggle">▶</span>
      </div>
      <div class="sidebar-notes">
        ${subj.notes.map(n => `
          <a class="note-link" data-filename="${n.filename}" onclick="loadNote('${n.filename}', '${subj.id}', '${subj.name}')">
            ${n.title}
            ${n.date ? `<span class="note-date">${n.date}</span>` : ""}
          </a>
        `).join("")}
      </div>
    `;
    sidebar.appendChild(div);
  });
}

function toggleSubject(id) {
  const el = document.querySelector(`.sidebar-subject[data-id="${id}"]`);
  if (el) el.classList.toggle("open");
}

function loadNote(filename, subjectId, subjectName) {
  document.querySelectorAll(".note-link").forEach(l => l.classList.remove("active"));
  const link = document.querySelector(`.note-link[data-filename="${filename}"]`);
  if (link) link.classList.add("active");

  const md = NOTES_CONTENT[filename] || "（筆記內容載入失敗）";
  const html = marked.parse(md);

  document.getElementById("main").innerHTML = `
    <div class="note-title-bar">
      <span class="note-subject-tag ${subjectId}">${subjectName}</span>
    </div>
    <div class="content">${html}</div>
    <div class="mindmap-section" id="mindmap-section">
      <div class="mindmap-header">
        <h2>📊 心智圖</h2>
        <button class="mindmap-toggle" id="mindmap-toggle" onclick="toggleMindMap()">展開心智圖</button>
      </div>
      <div class="mindmap-wrap" id="mindmap-wrap" style="display:none;"></div>
    </div>
  `;
  window.scrollTo(0, 0);

  // Store current note md for mind map rendering
  window._currentNoteMd = md;
  window._mindmapRendered = false;
}

function toggleMindMap() {
  const wrap   = document.getElementById("mindmap-wrap");
  const btn    = document.getElementById("mindmap-toggle");
  const hidden = wrap.style.display === "none";

  if (hidden) {
    wrap.style.display = "block";
    btn.textContent = "收起心智圖";
    if (!window._mindmapRendered) {
      renderMindMap(window._currentNoteMd, wrap);
      window._mindmapRendered = true;
    }
  } else {
    wrap.style.display = "none";
    btn.textContent = "展開心智圖";
  }
}

function renderMindMap(mdContent, container) {
  // Extract only headings for a clean mind map
  const headingLines = mdContent.split("\n")
    .filter(l => /^#{1,4}\s/.test(l.trim()))
    .join("\n");

  const { Transformer } = window.markmap;
  const transformer = new Transformer();
  const { root } = transformer.transform(headingLines || mdContent);

  const svg = document.createElementNS("http://www.w3.org/2000/svg", "svg");
  svg.style.cssText = "width:100%;height:520px;";
  container.innerHTML = "";
  container.appendChild(svg);

  const { Markmap } = window.markmap;
  const mm = Markmap.create(svg, {
    duration: 400,
    maxWidth: 260,
    paddingX: 16,
    spacingVertical: 8,
    spacingHorizontal: 80,
  });
  mm.setData(root);
  mm.fit();
}

// ── Init ──
buildSidebar();

// Auto-open first subject and load first note
if (SIDEBAR_DATA.length > 0) {
  toggleSubject(SIDEBAR_DATA[0].id);
}
if (FIRST_NOTE) {
  const firstSubj = SIDEBAR_DATA.find(s => s.notes.some(n => n.filename === FIRST_NOTE));
  if (firstSubj) {
    toggleSubject(firstSubj.id);
    loadNote(FIRST_NOTE, firstSubj.id, firstSubj.name);
  }
}
</script>
</body>
</html>
"""

if __name__ == "__main__":
    build()
