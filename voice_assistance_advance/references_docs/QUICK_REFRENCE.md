# Voice Assistant - Quick Reference

## 📁 Folder Structure
```
AI_Assistance/
├── ai.py, main.py, config.yaml, quick_tune.py
├── whisper_model/          # Small (486MB) - use this
├── whisper_model_tiny/     # Tiny (75MB) - faster
└── voices/                 # All TTS voices here
    ├── en_US-bryce-medium.onnx
    └── en_GB-southern_english_female-low.onnx
```

## 🚀 Quick Start
```bash
# 1. Install
pip install -r requirements.txt

# 2. Configure
python quick_tune.py

# 3. Run
python main.py
```

## 📥 Download Links

| What | Where |
|------|-------|
| **Whisper Small** | https://huggingface.co/Systran/faster-whisper-small |
| **Whisper Tiny** | https://huggingface.co/Systran/faster-whisper-tiny |
| **Piper Voices** | https://github.com/rhasspy/piper/releases/tag/2023.11.14-2 |

## ⚙️ Quick Tune Menu

| Option | Function |
|--------|----------|
| **6** | Switch Model (Tiny ⇄ Small) |
| **7** | Switch Voice (from voices/ folder) |
| **8** | Switch STT Mode (Offline ⇄ Hybrid) |

## 🎯 STT Modes

### Offline (Default)
```yaml
whisper:
  mode: "offline"
```
- ✅ Free, private, works offline
- 80-85% accuracy on Nigerian accent

### Hybrid (Better Accuracy)
```yaml
whisper:
  mode: "hybrid"
```
- ✅ 95%+ accuracy with Google STT (en-NG)
- ✅ Auto-fallback to Whisper offline
- ⚠️ Requires Google Cloud setup
- Cost: ~$0.40/hour

**Setup:** https://cloud.google.com/speech-to-text/docs/quickstart

## 🔧 Key Settings

### For Nigerian Accent
```yaml
whisper:
  vad:
    threshold: 0.45              # Lower = more sensitive
    no_speech_threshold: 0.5
    min_speech_duration_ms: 200  # Catch short words
    speech_pad_ms: 600           # Prevent cutoffs
  
  accent_prompt: "Nigerian English. West African accent."
  
  transcription:
    beam_size: 3  # 1=fast, 5=accurate
```

### For Quiet Environment
```yaml
threshold: 0.40
no_speech_threshold: 0.45
rms_threshold: 0.012
```

### For Noisy Environment
```yaml
threshold: 0.60
no_speech_threshold: 0.65
rms_threshold: 0.025
```

## 📊 Performance Comparison

| Setup | Accuracy | Speed | Internet | Cost |
|-------|----------|-------|----------|------|
| Tiny + Offline | 60-70% | <1s | No | Free |
| Small + Offline | 80-85% | 2-3s | No | Free |
| Small + Hybrid | 95%+ | <1s | Optional | ~$0.40/hr |

## 🎤 Commands

| Say | Response |
|-----|----------|
| "assistant" | Wakes up |
| "tell me a joke" | Tells joke |
| "what is the time" | Tells time |
| "sleep" | Goes to sleep |
| "exit" | Shuts down |

## 🐛 Troubleshooting

| Problem | Solution |
|---------|----------|
| Model not found | Check `whisper_model/model.bin` exists |
| Voice not found | Check `voices/your_voice.onnx` exists |
| Poor accuracy | Lower thresholds OR enable hybrid mode |
| Too many false triggers | Raise thresholds to 0.60+ |
| Words cut off | Increase `speech_pad_ms` to 800 |

## 📝 Files You Edit

| File | What to Change |
|------|----------------|
| `config.yaml` | All settings |
| `quick_tune.py` | Interactive tuner (no edit needed) |
| `voices/` folder | Add/remove voice files |

## 🔗 Useful Commands

```bash
# Test installation
pip list | grep -E "faster-whisper|piper|numpy|sounddevice"

# Check voices
ls voices/*.onnx

# Check models
ls whisper_model/model.bin
ls whisper_model_tiny/model.bin

# View logs
tail -f voice_assistant.log

# Test Google STT setup (if hybrid)
python -c "from google.cloud import speech_v1; print('✓ Google STT available')"
```

## 💡 Pro Tips

1. **Start with Small model + Offline mode** - Good balance
2. **Use hybrid mode for demos** - Best accuracy
3. **Customize accent_prompt** - Add your common words/names
4. **Keep voices/ organized** - Easy to manage multiple voices
5. **Monitor logs** - See what's actually recognized
6. **Test different environments** - Adjust VAD per location

## 📱 Mobile Deployment (Future)

```bash
# Install KivyMD requirements
pip install kivy kivymd

# Use Tiny model for mobile
whisper:
  model_dir: "whisper_model_tiny"

# Reduce chunk size
audio:
  chunk_duration_seconds: 2
```

## 🎯 Recommended Defaults

```yaml
# Production-ready Nigerian accent setup
wake_word:
  phrase: "assistant"
  timeout: 10

whisper:
  model_dir: "whisper_model"     # Small model
  mode: "offline"                 # Or "hybrid" if you have Google setup
  
  vad:
    threshold: 0.45
    no_speech_threshold: 0.5
    min_speech_duration_ms: 200
    speech_pad_ms: 600
  
  transcription:
    beam_size: 3

piper:
  voices_dir: "voices"
  model_file: "en_US-bryce-medium.onnx"
```

---

**Need help?** Check `voice_assistant.log` for errors

**Want more voices?** https://github.com/rhasspy/piper/releases/tag/2023.11.14-2

**Want better accuracy?** Enable hybrid mode with Google STT (en-NG)