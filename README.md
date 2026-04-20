# CounselorPath – Study Notes Automation

CounselorPath – Study Notes Automation is a practical toolkit designed to streamline the process of preparing for counseling psychology graduate program entrance exams. It transforms course material into structured, exam-ready study notes through an automated pipeline, reducing manual effort and improving learning efficiency.

## Overview

The workflow covers transcription, audio conversion, and note generation. Media files are first transcribed using Whisper, then processed by large language models (Claude or OpenAI) to generate well-organized markdown notes. These notes include key concepts, comparison tables, memory aids, and exam-oriented insights such as likely question formats and concise summaries for essay writing.

Built with batch processing and skip-on-exist logic, the system is optimized for handling large volumes of lecture content. It supports Chinese transcription and produces outputs tailored to the structure and demands of counseling-related exams.

**CounselorPath is not only a productivity tool, but also a learning companion — helping users move from passive listening to active understanding, and from fragmented information to structured knowledge.**


## Tech steps

### 1. Setup
```bash
# Install dependencies
pip install openai-whisper anthropic openai python-dotenv
brew install ffmpeg

# Create .env with API keys
echo "ANTHROPIC_API_KEY=sk-ant-..." > .env
echo "OPENAI_API_KEY=sk-..." >> .env
```

### 2. Transcribe Media
```bash
python 00-scripts/01to02-transcribe.py
```
Converts media files in `01-mov/` to text transcriptions in `02-txt/`

### 3. Generate Study Notes
```bash
python 00-scripts/02to03-make_notes.py
```
Transforms transcriptions into structured markdown notes in `03-notes/`

## Features

✅ **Batch Processing** – Handles multiple lecture files automatically  
✅ **Smart Caching** – Skips already-processed files  
✅ **Multi-Model Support** – Claude (default) or OpenAI models  
✅ **Prompt Caching** – Reduces API costs through intelligent caching  
✅ **Token Tracking** – Detailed usage and cost reporting  
✅ **Chinese Support** – Native Chinese transcription and note generation  
✅ **Exam-Focused Output** – Notes include:
  - 🔥 Priority indicators (Must-know / Often tested / Caution)
  - 📌 Comparison tables & concept maps
  - 🧠 Memory techniques & mnemonics
  - 🎯 Predicted exam formats (Multiple choice / Term definition / Essay)
  - 💡 One-sentence summaries for essay openings
  - 🎓 School-specific coverage insights

## Subject Coverage

- 普通心理學 (General Psychology)
- 輔導原理與諮商 (Counseling Principles)
- 教育研究法 (Educational Research Methods)
  - 統計 (Statistics)
  - 測驗 (Testing)
  - 研究法 (Research Methods)
- 英文 (English)

## API Configuration

### Claude (Recommended)
```bash
python 00-scripts/02to03-make_notes.py --provider claude --model claude-opus-4-7
```

### OpenAI
```bash
python 00-scripts/02to03-make_notes.py --provider openai --model gpt-4o-mini
```

Get API keys:
- [Anthropic Console](https://console.anthropic.com)
- [OpenAI API Keys](https://platform.openai.com/api-keys)

## How It Works

1. **Transcription**: Whisper converts speech to text (supports multiple formats)
2. **Processing**: Raw transcription is fed to LLM with exam-prep system prompt
3. **Generation**: Model structures notes with concepts, tables, memory aids, and exam insights
4. **Output**: Markdown files ready for review and further editing

## System Requirements

- Python 3.8+
- ffmpeg (for audio conversion)
- Internet connection (for API calls)
- Valid API keys (Anthropic or OpenAI)

---

**Transform lectures into knowledge. From listening to understanding.**
