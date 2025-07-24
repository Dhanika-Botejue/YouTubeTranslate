# YouTubeTranslate: AI-Powered Video Translation Platform  
#### Video Demo: Working on it
## Overview  

YouTubeTranslate is a **full-stack web application** that enables users to translate YouTube videos into different languages while preserving the original video content. Built with Python's Flask framework, the system combines:  

- **Speech Recognition** (OpenAI Whisper)  
- **Machine Translation** (MyMemory API)  
- **Text-to-Speech Synthesis** (gTTS)  
- **Video/Audio Processing** (FFmpeg, pydub)  

The project addresses a key limitation of YouTube's built-in captions by **creating dubbed versions** of videos with synchronized translated audio. Unlike simple subtitle tools, this solution modifies the media itself, making content accessible to non-native speakers and hearing-impaired audiences.  

---

## Technical Architecture  

### Core Components  

#### 1. `app.py` (Backend)  
The Flask application handles:  
- **User authentication** (login/logout via server's file system)  
- **Video processing pipeline**:  
  1. YouTube audio extraction (`yt-dlp`)  
  2. Speech-to-text transcription (Whisper)  
  3. Text translation (MyMemory API)  
  4. Audio synthesis (gTTS)  
  5. Video reassembly (FFmpeg)  
- **Database operations** (SQLite for user/video tracking)  

**Key Design Choices**:  
- Used **global variables** for transcript state to simplify inter-route data sharing (debated using Redis but opted for simplicity)  


#### 2. `init_db.py` (Database)  
Initializes SQLite with two tables:  
- `user`: Stores credentials (plaintext passwords for demo purposes only - **not production-safe**)  
- `video`: Tracks translated videos per user  

#### 3. Templates (Frontend)  
- **Jinja2-based HTML** with minimal JavaScript for interactivity  
- **Responsive design** works on mobile/desktop  

| File | Purpose |  
|-------|---------|  
| `index.html` | Video submission form |  
| `video.html` | Download success page |  
| `login.html` | Authentication |  
| `register.html` | Account creation |  
| `select_video.html` | User video library |  

#### 4. `static/styles.css`  
Custom CSS providing:  
- **Red-themed UI** matching YouTube's branding  
- **Mobile-friendly** flexbox layouts  
- **Animated buttons** for better UX  

---

## Setup Guide  

### System Requirements  
- **Python 3.8+**  
- **FFmpeg** (audio processing):  
  ```bash
  # Linux
  sudo apt install ffmpeg
  # macOS
  brew install ffmpeg
  # Windows (Admin PowerShell)
  choco install ffmpeg
  ```

### Installation  
1. **Create virtual environment** (isolates dependencies):  
   ```bash
   python -m venv venv
   source venv/bin/activate  # Linux/macOS
   .\venv\Scripts\activate   # Windows
   ```

2. **Install Python packages**:  
   ```bash
   pip install -r requirements.txt
   ```

3. **Initialize database**:  
   ```bash
   python init_db.py
   ```
---

## Usage Walkthrough  
Run your app:
```flask
flask run
```
Now you can visit it at:
```bash
http://127.0.0.1:5000
```
### 1. Account Creation  
Users register via `/register` with:  
- Unique username  
- Password (stored in plaintext - **demo only**)  

### 2. Video Translation 
1. Submit YouTube URL at `/`  
2. Select languages:  
   - **Source**: Original video language
   - **Target**: 99 supported output languages  
3. Process flow:  
   ```text
     A[YouTube URL] --> B[Download Audio]
     B --> C[Transcribe with Whisper]
     C --> D[Translate Text]
     D --> E[Generate TTS Audio]
     E --> F[Merge with Video]
   ```

### 3. Output  
- Videos save to `static/` with user-defined names  
- Users can browse their translations at `/select_video`  

---

## Design Decisions  
### 1. Translation Service Selection  
Compared:  
- **MyMemory API** (free tier)  
- **Google Cloud Translation** (more accurate but paid)  

Selected MyMemory for:  
- Zero cost  
- Adequate quality for demo purposes  

### 2. State Management  
Global `transcript_details` dictionary was preferred over:  
- **Database storage**: Too slow for interim processing  
- **Client-side storage**: Insecure for sensitive data  

---

## Performance Considerations  

### Optimizations  
- **Whisper Model Size**: Using `small` (1GB RAM) instead of `large` (10GB)  
- **Parallel Processing**: Future upgrade path with Celery  

### Benchmarks  
| Task | Time (1-min video) |  
|-------|-------------------|  
| Audio Download | ~10s |  
| Transcription | ~30s (CPU) / ~5s (GPU) |  
| Translation | ~20s |  
| TTS Generation | ~15s |  

---

## Limitations & Future Work  

### Current Constraints  
- **No batch processing** (one video at a time)  
- **Translation quality** varies by language pair  
- **Audio artifacts** in speed-adjusted TTS  

### Planned Enhancements  
1. **Subtitle support**: Burn translated text into video  
2. **Voice cloning**: Match original speaker's tone  
3. **Cloud deployment**: AWS Elastic Beanstalk ready  

---

## Conclusion  

YouTubeTranslate demonstrates how **open-source AI tools** can create powerful media applications. By combining Whisper's transcription, machine translation APIs, and Flask's simplicity, the project achieves clean results without proprietary software.  
