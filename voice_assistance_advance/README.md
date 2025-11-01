# Voice Assistant for Blind Students

A production-ready Speech-to-Text (STT) and Text-to-Speech (TTS) learning system designed specifically for blind students, built with Python using Faster-Whisper and Piper TTS.

## Features

✅ **Non-blocking TTS**: Recognition continues while assistant is speaking  
✅ **Wake Word Detection**: Only responds after hearing "hey assistant"  
✅ **Advanced VAD**: Filters background noise and focuses on speech  
✅ **Error Recovery**: Auto-restarts on failures  
✅ **Comprehensive Logging**: Full audit trail in log files  
✅ **Configurable**: Easy YAML-based configuration  

## Project Structure

```
AI_Assistance/
├── ai.py                                    # Main assistant logic
├── main.py                                  # Entry point
├── config.yaml                              # Configuration file
├── config_loader.py                         # Config management
├── en_GB-southern_english_female-low.onnx   # Piper TTS model
├── en_GB-southern_english_female-low.onnx.json
├── whisper_model/                           # Faster-Whisper files
│   ├── config.json
│   ├── model.bin
│   ├── tokenizer.json
│   └── vocabulary.txt
└── voice_assistant.log                      # Log file (auto-created)
```

## Installation

### Requirements

- Python 3.8+
- Microphone
- Audio output device

### Install Dependencies

```bash
pip install numpy sounddevice faster-whisper piper-tts pyjokes pyyaml
```

### Download Models

1. **Whisper Model**: Download from [Hugging Face](https://huggingface.co/Systran/faster-whisper-base.en)
2. **Piper Model**: Download from [Piper Voices](https://github.com/rhasspy/piper/releases)

Place models in the correct directories as shown in project structure.

## Usage

### Basic Usage

```bash
python main.py
```

### First-Time Setup

1. Run the assistant
2. Wait for "Assistant initialized. Say hey assistant to activate me."
3. Say **"hey assistant"** to wake up the system
4. Give commands like:
   - "Tell me a joke"
   - "What time is it?"
   - "What's the date?"
   - "Sleep" (deactivate until next wake word)
   - "Goodbye" (exit)

## Configuration

Edit `config.yaml` to tune the system for your environment.

### Key Settings

#### Wake Word
```yaml
wake_word:
  phrase: "hey assistant"  # Change to your preferred phrase
  timeout: 10              # Seconds to stay active
```

#### Voice Activity Detection (VAD)
```yaml
whisper:
  vad:
    threshold: 0.5                  # 0.0-1.0, higher = less noise
    min_speech_duration_ms: 250     # Minimum speech length
    no_speech_threshold: 0.6        # Higher = stricter silence filtering
```

#### Audio Quality
```yaml
whisper:
  transcription:
    beam_size: 5        # Higher = more accurate (1-5)
    language: "en"
```

## Tuning for Your Environment

### Problem: Too Much Background Noise

**Solution**: Increase VAD thresholds

```yaml
whisper:
  vad:
    threshold: 0.7              # Was 0.5
    no_speech_threshold: 0.7    # Was 0.6
```

### Problem: Missing Short Words

**Solution**: Decrease minimum speech duration

```yaml
whisper:
  vad:
    min_speech_duration_ms: 150  # Was 250
```

### Problem: Wake Word Not Detected

**Solution**: Lower threshold or change phrase

```yaml
wake_word:
  phrase: "computer"    # Shorter, clearer word
  threshold: 0.5        # Was 0.7
```

### Problem: Slow Recognition

**Solution**: Reduce beam size

```yaml
whisper:
  transcription:
    beam_size: 3        # Was 5
    best_of: 3          # Was 5
```

### Problem: Assistant Keeps Listening Too Long

**Solution**: Reduce timeout

```yaml
wake_word:
  timeout: 5           # Was 10 seconds
```

## Advanced Features

### Non-Blocking Speech

The TTS runs in a background thread, so the assistant can listen while speaking:

```python
# In your code
self.tts.speak("I'm saying something long", blocking=False)
# Recognition continues immediately
```

### Custom Commands

Add new skills in `ai.py`:

```python
def _skill_weather(self):
    """Tell the weather"""
    weather = get_weather()  # Your implementation
    self.tts.speak(f"The weather is {weather}")

# Add to command_map
self.command_map = {
    ...
    "weather": self._skill_weather,
}
```

Then update `config.yaml`:

```yaml
commands:
  weather: ["weather", "what's the weather", "how's the weather"]
```

## Logging

Logs are written to `voice_assistant.log` with timestamps:

```
2025-10-30 10:30:45 - ai - INFO - Wake word detected!
2025-10-30 10:30:46 - ai - INFO - Recognized: 'tell me a joke'
2025-10-30 10:30:46 - ai - INFO - Executing skill: joke
```

Change log level in `config.yaml`:

```yaml
logging:
  level: "DEBUG"  # For more detailed logs
```

## Troubleshooting

### Audio Issues

**No audio input detected**
```bash
# Test your microphone
python -c "import sounddevice as sd; print(sd.query_devices())"
```

**TTS not playing**
- Check audio output device
- Verify Piper model path in `config.yaml`

### Model Issues

**Whisper model not found**
- Ensure `whisper_model/` directory exists
- Check for `model.bin` file

**Piper model not found**
- Verify `.onnx` file exists
- Check path in `config.yaml`

### Performance Issues

**High CPU usage**
- Use smaller Whisper model (tiny, base instead of large)
- Reduce `beam_size` to 1-3
- Increase `chunk_duration_seconds`

**Recognition delays**
- Decrease `chunk_duration_seconds` to 2
- Use faster Whisper model

## Production Deployment

### For Blind Students

1. **Auto-start on login**: Create a startup script
2. **Keyboard shortcuts**: Add global hotkeys for common commands
3. **Audio feedback**: Enable sound for all events
4. **Error notifications**: Use text-to-speech for all errors

### System Service