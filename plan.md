# 計畫：逐字稿轉結構化備考筆記腳本

## Context
用戶是諮商所備考生，已有完整的影片→逐字稿 pipeline。
現在需要第三步：把 Whisper 產生的「無標點連續中文逐字稿」，透過 Claude API 轉成可背、可考、可寫申論的結構化筆記（Markdown + emoji 格式）。

## 目標
- 輸入：`/Users/ting/Documents/mov_to_txt/02-txt/*.txt`（7個逐字稿）
- 輸出：`/Users/ting/Documents/mov_to_txt/03-notes/*.md`（對應筆記）
- 架構：沿用 `convert_to_mp3.py` 的 code pattern

## 新增檔案
`/Users/ting/Documents/mov_to_txt/make_notes.py`

## 實作細節

### 路徑設定（沿用既有 pattern）
```python
TXT_DIR   = Path("/Users/ting/Documents/mov_to_txt/02-txt")
NOTES_DIR = Path("/Users/ting/Documents/mov_to_txt/03-notes")
```

### API 設定
- 使用 `anthropic` SDK（需 `pip install anthropic`）
- API key 從環境變數讀取：`os.environ.get("ANTHROPIC_API_KEY")`
- 找不到 key 時顯示明確錯誤訊息並 `sys.exit(1)`
- Model：`claude-opus-4-7`（最佳推理能力，適合內容理解）
- 啟用 **prompt caching**（system prompt 加 `cache_control`），降低重複呼叫成本

#### claude API
 Use skill "claude-api"?
 Claude may use instructions, code, or files from this Skill.

   Build, debug, and optimize Claude API / Anthropic SDK apps. Apps built with this skill should include prompt caching. Also handles migrating existing Claude API code between Claude model versions (4.5 → 4.6, 4.6 → 4.7, retired-model replacements).
   TRIGGER when: code imports `anthropic`/`@anthropic-ai/sdk`; user asks for the Claude API, Anthropic SDK, or Managed Agents; user adds/modifies/tunes a Claude feature (caching, thinking, compaction, tool use, batch, files, citations, memory) or model (Opus/Sonnet/Haiku) in a file; questions about prompt caching / cache hit rate in an Anthropic SDK project.
   SKIP: file imports `openai`/other-provider SDK, filename like `*-openai.py`/`*-generic.py`, provider-neutral code, general programming/ML.


### System Prompt（角色設定）
- 30年經驗補習班輔導老師
- 精通諮商所考試科目：普通心理學、輔導原理、教育研究法、英文
- 任務：將逐字稿轉成「可背、可考、可寫申論」的筆記

### 筆記格式（依用戶範例）
- 標題 + 核心人物/概念
- 按理論分章節
- 表格呈現（人格結構、發展階段等）
- 考點標注（🔥⭐ emoji）
- 題型預測（選擇/解釋名詞/申論）
- 一句話總結（申論用）
- 輸出格式：Markdown（.md），支援 emoji

### 核心邏輯（沿用 convert_to_mp3.py pattern）
1. 前置檢查：API key、目錄存在、`anthropic` 套件
2. 遍歷 `02-txt/*.txt`
3. skip-if-exists：`03-notes/<stem>.md` 已存在則跳過
4. 呼叫 Claude API，輸入逐字稿全文
5. 將回應寫入 `03-notes/<stem>.md`（UTF-8）
6. 計時、統計、摘要輸出

### Token 處理
- 逐字稿最大 65KB（約 3萬字）→ 使用 `max_tokens=8192` for output

## 驗證方式
1. 執行腳本，確認 `03-notes/` 下產生 .md 筆記
2. 開啟筆記確認：有章節、有表格、有 emoji 考點標注
3. 再次執行確認 skip-if-exists 正常運作
