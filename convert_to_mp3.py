#!/usr/bin/env python3
"""
音訊轉換工具
將 mov/ 目錄中的影音檔轉換成 mp3/ 目錄中的 MP3 檔案
"""

import os
import sys
import subprocess
from pathlib import Path
import time
from datetime import datetime

# 設定路徑
MOV_DIR = Path("/Users/ting/Documents/mov_to_txt/01-mov")
MP3_DIR = Path("/Users/ting/Documents/mov_to_txt/04-mp3")

# 支援的媒體格式
SUPPORTED_FORMATS = {'.mp4', '.wav', '.m4a', '.mp3', '.mov', '.webm', '.flac', '.ogg'}

def convert_to_mp3(file_path, output_path):
    """使用 ffmpeg 將音訊檔轉換為 MP3"""
    try:
        print(f"正在轉換: {file_path.name}")
        # ffmpeg 轉換命令
        cmd = [
            'ffmpeg',
            '-i', str(file_path),
            '-q:a', '5',  # 品質設定 (0-9, 5 是默認)
            '-y',  # 覆蓋輸出檔案
            str(output_path)
        ]

        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True
        )

        if result.returncode == 0:
            return True
        else:
            print(f"  ffmpeg 錯誤: {result.stderr}")
            return False
    except Exception as e:
        print(f"  錯誤: {e}")
        return False

def main():
    start_time = time.time()

    # 檢查目錄
    if not MOV_DIR.exists():
        print(f"錯誤: {MOV_DIR} 目錄不存在")
        sys.exit(1)

    if not MP3_DIR.exists():
        MP3_DIR.mkdir(parents=True, exist_ok=True)
        print(f"已建立目錄: {MP3_DIR}")

    # 檢查 ffmpeg
    try:
        subprocess.run(['ffmpeg', '-version'], capture_output=True, check=True)
    except (subprocess.CalledProcessError, FileNotFoundError):
        print("錯誤: 未安裝 ffmpeg")
        print("請執行: brew install ffmpeg")
        sys.exit(1)

    # 找出所有媒體檔案
    media_files = [f for f in MOV_DIR.iterdir()
                   if f.is_file() and f.suffix.lower() in SUPPORTED_FORMATS]

    if not media_files:
        print(f"在 {MOV_DIR} 中找不到媒體檔案")
        sys.exit(0)

    print(f"找到 {len(media_files)} 個媒體檔案")
    print("-" * 50)

    converted_count = 0
    skipped_count = 0

    # 逐個轉換
    for media_file in sorted(media_files):
        mp3_file = MP3_DIR / f"{media_file.stem}.mp3"

        # 跳過已存在的檔案
        if mp3_file.exists():
            print(f"⊘ 跳過 (已存在): {media_file.name}")
            skipped_count += 1
            continue

        # 轉換
        if convert_to_mp3(media_file, mp3_file):
            print(f"✓ 完成: {media_file.name} → {mp3_file.name}")
            converted_count += 1
        else:
            print(f"✗ 失敗: {media_file.name}")

    print("-" * 50)

    # 計算花費時間
    elapsed_time = time.time() - start_time
    minutes = int(elapsed_time // 60)
    seconds = int(elapsed_time % 60)

    print(f"轉換完成!")
    print(f"  新轉換: {converted_count} 個")
    print(f"  已跳過: {skipped_count} 個")
    print(f"  花費時間: {minutes}分{seconds}秒")

if __name__ == "__main__":
    main()
