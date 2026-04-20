#!/usr/bin/env python3
"""
Whisper AI 批次逐字稿轉換工具
將 mov/ 目錄中的影音檔轉換成 txt/ 目錄中的逐字稿
"""

import os
import sys
import subprocess
from pathlib import Path
import time
from datetime import datetime

# 設定路徑
MOV_DIR = Path("/Users/ting/Documents/mov_to_txt/01-mov")
TXT_DIR = Path("/Users/ting/Documents/mov_to_txt/02-txt")

# 支援的媒體格式
SUPPORTED_FORMATS = {'.mp4', '.wav', '.m4a', '.mp3', '.mov', '.webm', '.flac', '.ogg'}

def install_whisper():
    """檢查並安裝 openai-whisper"""
    try:
        import whisper
    except ImportError:
        print("正在安裝 openai-whisper...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", "openai-whisper"])

def transcribe_file(file_path):
    """使用 Whisper 轉錄單個文件"""
    import whisper

    try:
        print(f"正在轉錄: {file_path.name}")
        model = whisper.load_model("base")
        result = model.transcribe(str(file_path), language="zh")
        return result["text"]
    except Exception as e:
        print(f"錯誤 {file_path.name}: {e}")
        return None

def main():
    start_time = time.time()
    start_datetime = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    # 檢查目錄
    if not MOV_DIR.exists():
        print(f"錯誤: {MOV_DIR} 目錄不存在")
        sys.exit(1)

    if not TXT_DIR.exists():
        TXT_DIR.mkdir(parents=True, exist_ok=True)

    # 安裝 whisper
    install_whisper()

    # 找出所有媒體檔案
    media_files = [f for f in MOV_DIR.iterdir()
                   if f.is_file() and f.suffix.lower() in SUPPORTED_FORMATS]

    if not media_files:
        print(f"在 {MOV_DIR} 中找不到媒體檔案")
        sys.exit(0)

    print(f"找到 {len(media_files)} 個媒體檔案")
    print("-" * 50)

    # 逐個轉錄
    for media_file in sorted(media_files):
        txt_file = TXT_DIR / f"{media_file.stem}.txt"

        # 跳過已存在的檔案
        if txt_file.exists():
            print(f"⊘ 跳過 (已存在): {media_file.name}")
            continue

        # 轉錄
        text = transcribe_file(media_file)

        if text:
            txt_file.write_text(text, encoding='utf-8')
            print(f"✓ 完成: {media_file.name} → {txt_file.name}")
        else:
            print(f"✗ 失敗: {media_file.name}")

    print("-" * 50)

    # 計算花費時間
    elapsed_time = time.time() - start_time
    minutes = int(elapsed_time // 60)
    seconds = int(elapsed_time % 60)

    print(f"轉錄完成! (花費時間: {minutes}分{seconds}秒)")

if __name__ == "__main__":
    main()
