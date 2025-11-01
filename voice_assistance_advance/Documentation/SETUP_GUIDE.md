# Voice Assistant - Complete Setup Guide

## Quick Start

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

**For hybrid mode with Google STT (optional):**
```bash
pip install google-cloud-speech
```

### 2. Download Models

#### Whisper Models (STT)

**Option A: Small Model (Recommended for production)**
- **Size:** 486 MB
- **Accuracy:** 80-85% on Nigerian accent
- **Speed:** 2-3 seconds per command

📥 **Direct Download:** https://huggingface.co/Systran/faster-whisper-small

1. Click "Files and versions"
2. Download these files:
   - `config.json`
   - `model.bin`
   - `tokenizer.json`
   - `vocabulary.txt`
3. Place in: `whisper_model/`

**Option B: Tiny Model (Faster, less accurate)**
- **Size:** 75 MB
- **Accuracy:** 60-70% on Nigerian accent
- **Speed:** <1 second per command

📥 **Direct Download:** https://huggingface.co/Systran/faster-whisper-tiny

1. Download same files as above
2. Place in: `whisper_model_tiny/`

#### Piper Voices (TTS)

📥 **Direct Download:** https://github.com/rhasspy/piper/releases/tag/2023.11.14-2

**Recommended voices:**

1. **American Male (Bryce)** - Medium Quality
   - Download: `en_US-bryce-medium.onnx` (16 MB)
   - Download: `en_US-bryce-medium.onnx.json`
   - Place in: `voices/`

2. **British Female (Southern English)** - Low Quality
   - Download: `en_GB-southern_english_female-low.onnx` (8 MB)
   - Download: `en_GB-southern_english_female-low.onnx.json`
   - Place in: `voices/`

3. **More options available:**
   - American Female voices
   - British Male voices
   - Different quality levels (low/medium/high)

### 3. Organize Your Project

Create this folder structure:

```
AI_Assistance/
├── ai.py                                    # Main assistant
├── main.py                                  # Entry point
├── config.yaml                              # Configuration
├── quick_tune.py                            # Interactive tuner
│
├── whisper_model/                           # SMALL model (486MB)
│   ├── config.json
│   ├── model.bin
│   ├── tokenizer.json
│   └── vocabulary.txt
│
├── whisper_model_tiny/                      # TINY model (75MB) - optional
│   ├── config.json
│   ├── model.bin
│   ├── tokenizer.json
│   └── vocabulary.txt
│
├── en_US-bryce-medium.onnx                  # American Male voice
├── en_US-bryce-medium.onnx.json
├── en_GB-southern_english_female-low.onnx   # British Female voice
└── en_GB-southern_english_female-low.onnx.json
```

### 2. Configure Your Settings

Run the interactive tuner:

```bash
python quick_tune.py
```

#### Switch Between Models:
- **Option 6: Switch Whisper Model**
  - Choose `1` for Tiny (faster, less accurate)
  - Choose `2` for Small (slower, more accurate)

#### Switch Between Voices:
- **Option 7: Switch Voice**
  - Lists all `.onnx` files in your directory
  - Select the one you want

### 3. Run the Assistant

```bash
python main.py
```

---

## Configuration File Explained

### config.yaml Structure

```yaml
wake_word:
  phrase: "assistant"      # Your wake word
  timeout: 10              # Seconds to stay active
  
whisper:
  model_dir: "whisper_model"              # "whisper_model" or "whisper_model_tiny"
  accent_prompt: "Nigerian English..."     # Customize for your dialect
  
  vad:
    threshold: 0.45        # Lower = more sensitive (for accents)
    min_speech_duration_ms: 200
    speech_pad_ms: 600     # Prevent word cutoffs
    no_speech_threshold: 0.5
  
  transcription:
    beam_size: 3           # 1-5: Higher = more accurate
    
piper:
  model_file: "en_US-bryce-medium.onnx"  # Your chosen voice
  
audio:
  chunk_duration_seconds: 3   # How often to process audio
  rms_threshold: 0.015        # Audio detection sensitivity
  peak_threshold: 0.04
  noise_gate_threshold: 0.01
```

---

## Model Comparison

### Whisper Models

| Model | Size | Speed | Accuracy (Nigerian) | Recommended For |
|-------|------|-------|-------------------|-----------------|
| **Tiny** | 75 MB | ⚡⚡⚡ Fast | ~60-70% | Testing, low-end phones |
| **Small** | 486 MB | ⚡⚡ Medium | ~80-85% | Production, balanced |
| **Base** | 145 MB | ⚡⚡⚡ Fast | ~65-75% | Not recommended |

### TTS Voices

| Voice | Gender | Accent | Quality | Size |
|-------|--------|--------|---------|------|
| `en_US-bryce-medium` | Male | American | Medium | ~15 MB |
| `en_GB-southern_english_female-low` | Female | British | Low | ~8 MB |

**Download more voices:** https://github.com/rhasspy/piper/releases

---

## Tuning for Nigerian Accent

### 1. Update Accent Prompt

Edit `config.yaml`:

```yaml
whisper:
  accent_prompt: "Nigerian English with Yoruba influence. Lagos accent. Common expressions: abeg, abi, sha, oya."
```

**Dialect-specific prompts:**

- **Yoruba:** `"Nigerian English with Yoruba influence. Lagos accent."`
- **Igbo:** `"Nigerian English with Igbo influence. Eastern Nigerian accent."`
- **Hausa:** `"Nigerian English with Hausa influence. Northern Nigerian accent."`

### 2. Adjust VAD Settings

For Nigerian accent, use **more lenient** settings:

```yaml
vad:
  threshold: 0.40              # Lower than default
  no_speech_threshold: 0.45    # Lower than default
  min_speech_duration_ms: 180  # Catch shorter words
  speech_pad_ms: 700           # More padding
```

### 3. Test and Iterate

```bash
# Test with these phrases:
"assistant"
"assistant tell me a joke"
"assistant what is the time"
```

Check `voice_assistant.log` to see what was actually recognized.

---

## Switching Models/Voices

### Method 1: Interactive Tuner (Easiest)

```bash
python quick_tune.py
# Select option 6 (Switch Model) or 7 (Switch Voice)
```

### Method 2: Edit config.yaml Manually

```yaml
# Switch to Tiny model
whisper:
  model_dir: "whisper_model_tiny"

# Switch to British Female voice
piper:
  model_file: "en_GB-southern_english_female-low.onnx"
```

Save and restart the assistant.

---

## Troubleshooting

### Problem: "Model not found"

**Solution:**
1. Check folder names match config:
   ```
   whisper_model/          ← Must match config.yaml
   whisper_model_tiny/
   ```
2. Verify `model.bin` exists inside the folder

### Problem: "Voice not found"

**Solution:**
1. Check `.onnx` file exists in project root
2. Ensure filename matches config exactly (case-sensitive)
3. Verify `.onnx.json` file also exists

### Problem: Still poor accuracy

**Try these in order:**

1. **Lower VAD threshold:**
   ```yaml
   vad:
     threshold: 0.35  # Very lenient
   ```

2. **Customize accent prompt:**
   ```yaml
   accent_prompt: "Nigerian English. [Your city] accent. Common words: [list common words you use]"
   ```

3. **Switch to Small model** (if using Tiny)

4. **Increase speech padding:**
   ```yaml
   vad:
     speech_pad_ms: 800
   ```

### Problem: Too many false triggers

**Solution:**
```yaml
vad:
  threshold: 0.55              # More strict
  no_speech_threshold: 0.65
audio:
  rms_threshold: 0.025         # Higher threshold
```

---

## Performance Optimization

### For Mobile/Low-End Devices

```yaml
whisper:
  model_dir: "whisper_model_tiny"  # Faster
  transcription:
    beam_size: 1                    # Fastest
    best_of: 1

audio:
  chunk_duration_seconds: 2         # Process more frequently
```

### For Maximum Accuracy

```yaml
whisper:
  model_dir: "whisper_model"       # Small model
  transcription:
    beam_size: 5                    # Most accurate
    best_of: 5

audio:
  chunk_duration_seconds: 4         # Longer context
```

---

## Adding More Voices

### 1. Download Voice

Visit: https://github.com/rhasspy/piper/releases

Download `.onnx` and `.onnx.json` files.

### 2. Copy to Project

```bash
# Example:
cp en_US-amy-low.onnx AI_Assistance/
cp en_US-amy-low.onnx.json AI_Assistance/
```

### 3. Switch via Quick Tune

```bash
python quick_tune.py
# Select option 7: Switch Voice
# Your new voice will appear in the list
```

---

## Recommended Settings by Environment

### Quiet Room (Office, Bedroom)

```yaml
whisper:
  vad:
    threshold: 0.40
    no_speech_threshold: 0.45

audio:
  rms_threshold: 0.012
  noise_gate_threshold: 0.008
```

### Normal Home

```yaml
whisper:
  vad:
    threshold: 0.45
    no_speech_threshold: 0.50

audio:
  rms_threshold: 0.015
  noise_gate_threshold: 0.01
```

### Noisy Environment (Street, Cafe)

```yaml
whisper:
  vad:
    threshold: 0.60
    no_speech_threshold: 0.65

audio:
  rms_threshold: 0.025
  noise_gate_threshold: 0.02
```

---

## Testing Your Setup

### 1. Check Models

```bash
# Verify folder structure
ls whisper_model/model.bin          # Should exist
ls whisper_model_tiny/model.bin     # Should exist
```

### 2. Check Voices

```bash
# List all voices
ls *.onnx

# Should show:
# en_US-bryce-medium.onnx
# en_GB-southern_english_female-low.onnx
```

### 3. Test Run

```bash
python main.py

# You should see:
# Whisper Model: whisper_model (or whisper_model_tiny)
# Voice: en_US-bryce-medium (or your chosen voice)
# VAD Threshold: 0.45
```

### 4. Test Commands

Say:
1. "assistant" → Should respond "Yes? I'm listening"
2. "tell me a joke" → Should tell a joke
3. "what is the time" → Should tell time
4. "sleep" → Should go to sleep

---

## Advanced: Custom Accent Prompts

The `accent_prompt` is powerful! Customize it for better accuracy:

### Examples:

**For Code-Switching (English + Pidgin):**
```yaml
accent_prompt: "Nigerian English and Nigerian Pidgin. Code-switching common. Words like abeg, wetin, how far, no wahala."
```

**For Specific Names:**
```yaml
accent_prompt: "Nigerian English. Names like Chukwuemeka, Oluwaseun, Abubakar, Ngozi, Fatima are common."
```

**For Technical Vocabulary:**
```yaml
accent_prompt: "Nigerian English. Technical terms: software, hardware, application, database, programming."
```

---

## Summary

✅ **To switch models:** `quick_tune.py` → Option 6  
✅ **To switch voices:** `quick_tune.py` → Option 7  
✅ **To adjust for accent:** Edit `accent_prompt` in config.yaml  
✅ **To improve accuracy:** Lower VAD thresholds  
✅ **To reduce false triggers:** Raise VAD thresholds  

**Start with Small model + lenient VAD settings for best Nigerian accent results!**