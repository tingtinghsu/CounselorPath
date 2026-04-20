#!/usr/bin/env python3
"""
逐字稿轉結構化備考筆記工具
將 02-txt/ 目錄中的逐字稿使用 Claude 或 OpenAI API 轉成 03-notes/ 中的結構化 Markdown 筆記

用法:
  python make_notes.py                        # 預設使用 Claude
  python make_notes.py --provider claude      # 明確指定 Claude (claude-opus-4-7)
  python make_notes.py --provider openai      # 使用 OpenAI (gpt-4o)
  python make_notes.py --provider openai --model gpt-4o-mini  # 指定較便宜的模型
"""

import argparse
import os
import sys
from pathlib import Path
from typing import Optional, Tuple
import time

# 自動載入根目錄下的 .env 檔案
_env_file = Path(__file__).parent.parent / ".env"
if _env_file.exists():
    try:
        from dotenv import load_dotenv
        load_dotenv(_env_file)
    except ImportError:
        import subprocess
        subprocess.check_call([sys.executable, "-m", "pip", "install", "python-dotenv"])
        from dotenv import load_dotenv
        load_dotenv(_env_file)

TXT_DIR = Path("/Users/ting/Documents/mov_to_txt/02-txt")
NOTES_DIR = Path("/Users/ting/Documents/mov_to_txt/03-notes")

SYSTEM_PROMPT = """你是一位擁有30年教學經驗的補習班輔導老師，專門協助學生備考諮商所研究所入學考試。
你精通以下科目：普通心理學、輔導原理與諮商、教育研究法（含統計、測驗、研究法）、英文。

你的任務是將課堂錄音的逐字稿，轉換成「可背、可考、可寫申論」的結構化備考筆記。

筆記格式規範：
1. 使用 Markdown 格式，善用標題層級（#、##、###）
2. 善用 emoji 標記重要程度：🔥=必考、⭐=常考、📌=考點提醒、🧠=記憶法、🎯=題型預測、💡=申論用
3. 重要概念用 Markdown 表格整理（如理論比較、人格結構、發展階段等）
4. 每個主要章節標注預測題型（選擇題 / 解釋名詞 5-10分 / 申論題 25分）
5. 標注哪些學校特別愛考（如：教育大學系列、北師、師大、實踐、輔大等）
6. 提供記憶口訣或聯想記憶法
7. 最後提供「一句話總結」供申論開頭引用
8. 重新整理邏輯架構，不要照單全收逐字稿順序

請自動判斷主題，組織成清晰的考試筆記。"""


def install_package(package: str):
    """檢查並安裝 Python 套件"""
    try:
        __import__(package)
    except ImportError:
        print(f"正在安裝 {package}...")
        import subprocess
        subprocess.check_call([sys.executable, "-m", "pip", "install", package])


# ── Claude ────────────────────────────────────────────────────────────────────

def generate_notes_claude(transcript_text: str, filename: str, model: str) -> Tuple[Optional[str], dict]:
    """使用 Claude API（串流 + prompt caching）"""
    import anthropic

    client = anthropic.Anthropic(api_key=os.environ.get("ANTHROPIC_API_KEY"))
    usage_info = {}

    try:
        print(f"  呼叫 Claude API [{model}]（串流中）...")
        notes_parts = []

        with client.messages.stream(
            model=model,
            max_tokens=8192,
            thinking={"type": "adaptive"},
            system=[
                {
                    "type": "text",
                    "text": SYSTEM_PROMPT,
                    "cache_control": {"type": "ephemeral"},
                }
            ],
            messages=[
                {
                    "role": "user",
                    "content": (
                        f"以下是課程錄音的逐字稿（檔案：{filename}）。"
                        f"請整理成結構化備考筆記：\n\n{transcript_text}"
                    ),
                }
            ],
        ) as stream:
            for text in stream.text_stream:
                notes_parts.append(text)
                print(text, end="", flush=True)

            final = stream.get_final_message()
            u = final.usage
            usage_info = {
                "input_tokens": u.input_tokens,
                "output_tokens": u.output_tokens,
                "cache_creation_tokens": getattr(u, "cache_creation_input_tokens", 0),
                "cache_read_tokens": getattr(u, "cache_read_input_tokens", 0),
            }

        print()
        return "".join(notes_parts), usage_info

    except Exception as e:
        print(f"\n  API 錯誤: {e}")
        return None, {}


# 定價: claude-opus-4-7 ($/1M tokens)
CLAUDE_PRICING = {
    "input": 5.0,
    "output": 25.0,
    "cache_write": 6.25,
    "cache_read": 0.5,
}


def format_token_cost_claude(usage: dict) -> str:
    p = CLAUDE_PRICING
    input_cost  = usage.get("input_tokens", 0) * p["input"] / 1_000_000
    output_cost = usage.get("output_tokens", 0) * p["output"] / 1_000_000
    cache_write = usage.get("cache_creation_tokens", 0) * p["cache_write"] / 1_000_000
    cache_read  = usage.get("cache_read_tokens", 0) * p["cache_read"] / 1_000_000
    total = input_cost + output_cost + cache_write + cache_read

    lines = [
        f"    輸入:       {usage.get('input_tokens', 0):>8,} tokens  (${input_cost:.4f})",
        f"    輸出:       {usage.get('output_tokens', 0):>8,} tokens  (${output_cost:.4f})",
    ]
    if usage.get("cache_creation_tokens"):
        lines.append(f"    快取寫入:   {usage['cache_creation_tokens']:>8,} tokens  (${cache_write:.4f})")
    if usage.get("cache_read_tokens"):
        lines.append(f"    快取讀取:   {usage['cache_read_tokens']:>8,} tokens  (${cache_read:.4f})")
    lines.append(f"    本次費用:   ${total:.4f} USD")
    return "\n".join(lines)


# ── OpenAI ────────────────────────────────────────────────────────────────────

def generate_notes_openai(transcript_text: str, filename: str, model: str) -> Tuple[Optional[str], dict]:
    """使用 OpenAI API（串流模式）"""
    from openai import OpenAI

    client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))
    usage_info = {}

    try:
        print(f"  呼叫 OpenAI API [{model}]（串流中）...")
        notes_parts = []

        stream = client.chat.completions.create(
            model=model,
            max_tokens=8192,
            stream=True,
            stream_options={"include_usage": True},
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {
                    "role": "user",
                    "content": (
                        f"以下是課程錄音的逐字稿（檔案：{filename}）。"
                        f"請整理成結構化備考筆記：\n\n{transcript_text}"
                    ),
                },
            ],
        )

        for chunk in stream:
            delta = chunk.choices[0].delta if chunk.choices else None
            if delta and delta.content:
                notes_parts.append(delta.content)
                print(delta.content, end="", flush=True)
            if chunk.usage:
                usage_info = {
                    "input_tokens": chunk.usage.prompt_tokens,
                    "output_tokens": chunk.usage.completion_tokens,
                    "cached_input_tokens": getattr(chunk.usage.prompt_tokens_details, "cached_tokens", 0) if chunk.usage.prompt_tokens_details else 0,
                }

        print()
        return "".join(notes_parts), usage_info

    except Exception as e:
        print(f"\n  API 錯誤: {e}")
        return None, {}


# 定價: gpt-4o ($/1M tokens)
OPENAI_PRICING = {
    "gpt-4o":      {"input": 2.5,  "output": 10.0, "cached_input": 1.25},
    "gpt-4o-mini": {"input": 0.15, "output": 0.6,  "cached_input": 0.075},
}


def format_token_cost_openai(usage: dict, model: str) -> str:
    p = OPENAI_PRICING.get(model, OPENAI_PRICING["gpt-4o"])
    cached = usage.get("cached_input_tokens", 0)
    non_cached = usage.get("input_tokens", 0) - cached
    input_cost  = non_cached * p["input"] / 1_000_000
    cached_cost = cached * p["cached_input"] / 1_000_000
    output_cost = usage.get("output_tokens", 0) * p["output"] / 1_000_000
    total = input_cost + cached_cost + output_cost

    lines = [
        f"    輸入:       {non_cached:>8,} tokens  (${input_cost:.4f})",
        f"    輸出:       {usage.get('output_tokens', 0):>8,} tokens  (${output_cost:.4f})",
    ]
    if cached:
        lines.append(f"    快取讀取:   {cached:>8,} tokens  (${cached_cost:.4f})")
    lines.append(f"    本次費用:   ${total:.4f} USD")
    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(description="逐字稿轉結構化備考筆記")
    parser.add_argument(
        "--provider",
        choices=["claude", "openai"],
        default="claude",
        help="使用的 AI 服務（預設: claude）",
    )
    parser.add_argument(
        "--model",
        default=None,
        help="指定模型（claude 預設: claude-opus-4-7 / openai 預設: gpt-4o）",
    )
    args = parser.parse_args()

    provider = args.provider
    if provider == "claude":
        model = args.model or "claude-opus-4-7"
        api_key_name = "ANTHROPIC_API_KEY"
        install_package("anthropic")
        generate_fn = lambda txt, fname: generate_notes_claude(txt, fname, model)
        format_fn   = lambda usage: format_token_cost_claude(usage)
    else:
        model = args.model or "gpt-4o"
        api_key_name = "OPENAI_API_KEY"
        install_package("openai")
        generate_fn = lambda txt, fname: generate_notes_openai(txt, fname, model)
        format_fn   = lambda usage: format_token_cost_openai(usage, model)

    start_time = time.time()

    if not os.environ.get(api_key_name):
        print(f"錯誤: 未設定 {api_key_name} 環境變數")
        print(f"請執行: export {api_key_name}='your-api-key'")
        sys.exit(1)

    if not TXT_DIR.exists():
        print(f"錯誤: {TXT_DIR} 目錄不存在")
        sys.exit(1)

    if not NOTES_DIR.exists():
        NOTES_DIR.mkdir(parents=True, exist_ok=True)
        print(f"已建立目錄: {NOTES_DIR}")

    txt_files = sorted([
        f for f in TXT_DIR.iterdir()
        if f.is_file() and f.suffix.lower() == ".txt"
    ])

    if not txt_files:
        print(f"在 {TXT_DIR} 中找不到 .txt 檔案")
        sys.exit(0)

    print(f"Provider: {provider.upper()}  Model: {model}")
    print(f"找到 {len(txt_files)} 個逐字稿")
    print("-" * 50)

    converted_count = 0
    skipped_count = 0
    total_usage: dict = {}

    for txt_file in txt_files:
        notes_file = NOTES_DIR / f"{txt_file.stem}.md"

        if notes_file.exists():
            print(f"⊘ 跳過 (已存在): {txt_file.name}")
            skipped_count += 1
            continue

        print(f"正在處理: {txt_file.name}")

        try:
            transcript = txt_file.read_text(encoding="utf-8")
        except Exception as e:
            print(f"  讀取錯誤: {e}")
            continue

        notes, usage = generate_fn(transcript, txt_file.name)

        if notes:
            notes_file.write_text(notes, encoding="utf-8")
            print(f"✓ 完成: {txt_file.name} → {notes_file.name}")
            print(format_fn(usage))
            converted_count += 1
            for key, val in usage.items():
                total_usage[key] = total_usage.get(key, 0) + val
        else:
            print(f"✗ 失敗: {txt_file.name}")

        print("-" * 50)

    elapsed_time = time.time() - start_time
    minutes = int(elapsed_time // 60)
    seconds = int(elapsed_time % 60)

    print(f"完成!")
    print(f"  新產生: {converted_count} 個")
    print(f"  已跳過: {skipped_count} 個")
    print(f"  花費時間: {minutes}分{seconds}秒")

    if converted_count > 0:
        print(f"\n  Token 使用總計:")
        print(format_fn(total_usage))


if __name__ == "__main__":
    main()
