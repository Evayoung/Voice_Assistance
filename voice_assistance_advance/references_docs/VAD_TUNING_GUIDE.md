# VAD Tuning Guide for Whisper

## Understanding VAD Parameters

Voice Activity Detection (VAD) filters out noise and silence, keeping only speech. Proper tuning is critical for accuracy.

## Parameter Reference

### `threshold` (0.0 - 1.0)
**What it does**: Sets the confidence level required to consider audio as "speech"

| Value | Effect | Use Case |
|-------|--------|----------|
| 0.3 | Very sensitive | Quiet environments, soft speakers |
| 0.5 | Balanced (default) | Normal use |
| 0.7 | Aggressive filtering | Noisy environments |
| 0.9 | Very strict | Extreme noise, mechanical sounds |

**Example**:
```yaml
whisper:
  vad:
    threshold: 0.5  # Start here, increase if too noisy
```

### `min_speech_duration_ms` (milliseconds)
**What it does**: Minimum length of audio to consider as speech

| Value | Effect | Use Case |
|-------|--------|----------|
| 100 | Catches very short sounds | Fast speakers, short words |
| 250 | Balanced (default) | Normal speech |
| 500 | Filters quick sounds | Ignore clicks, coughs |

**Example**:
```yaml
whisper:
  vad:
    min_speech_duration_ms: 250  # Adjust if missing words
```

### `max_speech_duration_s` (seconds)
**What it does**: Maximum continuous speech segment length

| Value | Effect | Use Case |
|-------|--------|----------|
| 10 | Short segments | Quick commands |
| 30 | Balanced (default) | Normal conversation |
| 60+ | Long segments | Dictation, stories |

**Example**:
```yaml
whisper:
  vad:
    max_speech_duration_s: 30  # Increase for longer speech
```

### `min_silence_duration_ms` (milliseconds)
**What it does**: How long silence must be to split speech segments

| Value | Effect | Use Case |
|-------|--------|----------|
| 200 | Splits on brief pauses | Fast, choppy speech |
| 500 | Balanced (default) | Natural speech |
| 1000 | Keeps sentences together | Slow speakers, long pauses |

**Example**:
```yaml
whisper:
  vad:
    min_silence_duration_ms: 500  # Lower = split more often
```

### `speech_pad_ms` (milliseconds)
**What it does**: Extra audio added before/after detected speech

| Value | Effect | Use Case |
|-------|--------|----------|
| 200 | Minimal padding | Clean audio |
| 400 | Balanced (default) | Normal use |
| 800 | Extra padding | Avoid cut-off words |

**Example**:
```yaml
whisper:
  vad:
    speech_pad_ms: 400  # Increase if words get cut off
```

### `no_speech_threshold` (0.0 - 1.0)
**What it does**: Confidence required to reject audio as "not speech"

| Value | Effect | Use Case |
|-------|--------|----------|
| 0.3 | Lenient | Accept borderline audio |
| 0.6 | Balanced (default) | Normal filtering |
| 0.8 | Strict | Reject most non-speech |

**Example**:
```yaml
whisper:
  transcription:
    no_speech_threshold: 0.6  # Higher = stricter filtering
```

## Common Scenarios

### Scenario 1: Quiet Room, Clear Speech
**Problem**: System works perfectly
**Action**: Keep defaults

```yaml
whisper:
  vad:
    threshold: 0.5
    min_speech_duration_ms: 250
    no_speech_threshold: 0.6
```

### Scenario 2: Noisy Environment (Fan, AC, Traffic)
**Problem**: Random sounds trigger recognition
**Solution**: Increase thresholds

```yaml
whisper:
  vad:
    threshold: 0.7              # More aggressive
    min_speech_duration_ms: 300 # Ignore quick sounds
    no_speech_threshold: 0.7    # Stricter silence detection
```

### Scenario 3: Quiet Speaker
**Problem**: Not picking up speech
**Solution**: Lower thresholds

```yaml
whisper:
  vad:
    threshold: 0.3              # More sensitive
    min_speech_duration_ms: 150 # Catch short words
    no_speech_threshold: 0.5    # Accept more audio
```

### Scenario 4: Fast Speaker
**Problem**: Words getting cut off
**Solution**: Faster segmentation

```yaml
whisper:
  vad:
    min_speech_duration_ms: 150  # Catch quick words
    min_silence_duration_ms: 300 # Split faster
    speech_pad_ms: 500           # Extra padding
```

### Scenario 5: Slow Speaker with Pauses
**Problem**: Sentences split into multiple parts
**Solution**: Longer silence threshold

```yaml
whisper:
  vad:
    min_silence_duration_ms: 1000  # Wait longer before splitting
    max_speech_duration_s: 45       # Allow longer segments
```

### Scenario 6: Background Music
**Problem**: Music triggering recognition
**Solution**: Maximum strictness

```yaml
whisper:
  vad:
    threshold: 0.8              # Very strict
    no_speech_threshold: 0.8    # Reject non-speech
    min_speech_duration_ms: 400 # Ignore musical notes
```

## Tuning Workflow

### Step 1: Test Baseline
```yaml
# Start with defaults
whisper:
  vad:
    threshold: 0.5
    min_speech_duration_ms: 250
    no_speech_threshold: 0.6
```

### Step 2: Identify Problems
Run the assistant and note:
- ❌ Too many false triggers → Increase `threshold`
- ❌ Missing speech → Decrease `threshold`
- ❌ Words cut off → Increase `speech_pad_ms`
- ❌ Slow response → Decrease `min_speech_duration_ms`

### Step 3: Adjust One at a Time
Change only ONE parameter, test, then adjust again.

### Step 4: Fine-tune
Make small adjustments (±0.1 for thresholds, ±50ms for durations)

## Testing Your Settings

### Quick Test Script

```python
# test_vad.py
import logging
from ai import VoiceAssistant

logging.basicConfig(level=logging.DEBUG)

# Test different phrases
test_phrases = [
    "hey assistant",
    "tell me a joke",
    "what time is it",
    "goodbye"
]

print("\n=== VAD Test ===")
print("Say each phrase clearly and check if recognized correctly:\n")
for phrase in test_phrases:
    print(f"Say: '{phrase}'")
    input("Press Enter when ready...")

assistant = VoiceAssistant()
assistant.listen()
```

### Metrics to Track

1. **False Positive Rate**: How often non-speech triggers recognition
2. **False Negative Rate**: How often speech is missed
3. **Word Error Rate**: Incorrect transcriptions
4. **Latency**: Time from speech end to response

## Advanced: Dynamic Threshold Adjustment

For production systems, consider dynamic threshold adjustment:

```python
class AdaptiveVAD:
    def __init__(self):
        self.base_threshold = 0.5
        self.false_positives = 0
        self.false_negatives = 0
    
    def adjust_threshold(self):
        """Adjust threshold based on error rates"""
        if self.false_positives > 5:
            self.base_threshold += 0.1  # More strict
            self.false_positives = 0
        elif self.false_negatives > 5:
            self.base_threshold -= 0.1  # More lenient
            self.false_negatives = 0
        
        # Clamp between 0.3 and 0.9
        self.base_threshold = max(0.3, min(0.9, self.base_threshold))
        
        return self.base_threshold
```

## Environment-Specific Presets

### Office Environment
```yaml
whisper:
  vad:
    threshold: 0.6
    min_speech_duration_ms: 250
    no_speech_threshold: 0.65
```

### Home with TV/Radio
```yaml
whisper:
  vad:
    threshold: 0.7
    min_speech_duration_ms: 300
    no_speech_threshold: 0.75
```

### Library/Quiet Space
```yaml
whisper:
  vad:
    threshold: 0.4
    min_speech_duration_ms: 200
    no_speech_threshold: 0.5
```

### Outdoor/Street
```yaml
whisper:
  vad:
    threshold: 0.8
    min_speech_duration_ms: 350
    no_speech_threshold: 0.8
```

## Debugging Tips

### Enable Debug Logging
```yaml
logging:
  level: "DEBUG"
```

### Check VAD in Logs
Look for patterns like:
```
DEBUG - VAD detected speech: 1.2s at threshold 0.5
DEBUG - Rejected as non-speech: confidence 0.4
DEBUG - Speech segment too short: 180ms (min: 250ms)
```

### Visual Debugging
Install `matplotlib` and visualize audio:

```python
import matplotlib.pyplot as plt
import numpy as np

# Plot audio with VAD decisions
def plot_vad(audio, vad_segments):
    plt.figure(figsize=(12, 4))
    plt.plot(audio)
    for start, end in vad_segments:
        plt.axvspan(start, end, alpha=0.3, color='green')
    plt.title('Audio with VAD Segments')
    plt.show()
```

## Summary

| Goal | Adjust |
|------|--------|
| Reduce noise triggers | ↑ `threshold`, ↑ `no_speech_threshold` |
| Catch quiet speech | ↓ `threshold`, ↓ `no_speech_threshold` |
| Catch short words | ↓ `min_speech_duration_ms` |
| Avoid word cutoffs | ↑ `speech_pad_ms` |
| Keep sentences together | ↑ `min_silence_duration_ms` |
| Split faster | ↓ `min_silence_duration_ms` |

Start conservative (high thresholds), then gradually decrease until you find the sweet spot for your environment.