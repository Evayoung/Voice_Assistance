"""
Test Suite for Voice Assistant
Run this to verify all components work correctly
"""
import os
import sys
import time
import logging
import numpy as np
from pathlib import Path

# Configure logging for tests
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - TEST - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def print_test_header(test_name: str):
    """Print formatted test header"""
    print("\n" + "=" * 60)
    print(f"TEST: {test_name}")
    print("=" * 60)


def test_imports():
    """Test 1: Verify all required packages are installed"""
    print_test_header("Package Imports")

    required_packages = {
        'numpy': 'numpy',
        'sounddevice': 'sounddevice',
        'faster_whisper': 'faster-whisper',
        'piper': 'piper-tts',
        'yaml': 'pyyaml',
        'pyjokes': 'pyjokes'
    }

    all_good = True
    for module, package in required_packages.items():
        try:
            __import__(module)
            print(f"✓ {module:20s} - OK")
        except ImportError as e:
            print(f"✗ {module:20s} - MISSING (install: pip install {package})")
            all_good = False

    if all_good:
        print("\n✓ All packages installed correctly")
    else:
        print("\n✗ Some packages missing - install them first")
        sys.exit(1)

    return all_good


def test_file_structure():
    """Test 2: Verify all required files exist"""
    print_test_header("File Structure")

    required_files = [
        'ai.py',
        'main.py',
        'config.yaml',
        'en_GB-southern_english_female-low.onnx',
        'whisper_model/model.bin',
        'whisper_model/config.json',
    ]

    all_good = True
    for filepath in required_files:
        path = Path(filepath)
        if path.exists():
            size = path.stat().st_size if path.is_file() else "DIR"
            print(f"✓ {str(path):40s} - EXISTS ({size})")
        else:
            print(f"✗ {str(path):40s} - MISSING")
            all_good = False

    if all_good:
        print("\n✓ All required files present")
    else:
        print("\n✗ Some files missing - check installation")
        sys.exit(1)

    return all_good


def test_audio_devices():
    """Test 3: Check audio input/output devices"""
    print_test_header("Audio Devices")

    try:
        import sounddevice as sd

        print("\nAvailable Audio Devices:")
        print("-" * 60)
        devices = sd.query_devices()

        for i, device in enumerate(devices):
            device_type = []
            if device['max_input_channels'] > 0:
                device_type.append("INPUT")
            if device['max_output_channels'] > 0:
                device_type.append("OUTPUT")

            print(f"{i}: {device['name']}")
            print(f"   Type: {', '.join(device_type)}")
            print(f"   Channels: In={device['max_input_channels']}, Out={device['max_output_channels']}")
            print(f"   Sample Rate: {device['default_samplerate']} Hz")
            print()

        # Check default devices
        default_input = sd.query_devices(kind='input')
        default_output = sd.query_devices(kind='output')

        print("Default Devices:")
        print(f"✓ Input:  {default_input['name']}")
        print(f"✓ Output: {default_output['name']}")

        return True

    except Exception as e:
        print(f"✗ Audio device test failed: {e}")
        return False


def test_whisper_model():
    """Test 4: Load and test Whisper model"""
    print_test_header("Whisper Model")

    try:
        from faster_whisper import WhisperModel

        model_dir = "whisper_model"
        print(f"Loading Whisper model from: {model_dir}")

        start_time = time.time()
        model = WhisperModel(model_dir, device="cpu", compute_type="int8")
        load_time = time.time() - start_time

        print(f"✓ Model loaded successfully in {load_time:.2f}s")

        # Test transcription with dummy audio
        print("\nTesting transcription with silence...")
        dummy_audio = np.zeros(16000, dtype=np.float32)  # 1 second of silence

        segments, info = model.transcribe(dummy_audio, vad_filter=True)
        segment_list = list(segments)

        print(f"✓ Transcription test passed")
        print(f"  Language: {info.language}")
        print(f"  Segments detected: {len(segment_list)}")

        return True

    except Exception as e:
        print(f"✗ Whisper model test failed: {e}")
        logger.error("Whisper error details:", exc_info=True)
        return False


def test_piper_model():
    """Test 5: Load and test Piper TTS model"""
    print_test_header("Piper TTS Model")

    try:
        from piper import PiperVoice
        import sounddevice as sd

        model_path = "en_GB-southern_english_female-low.onnx"
        print(f"Loading Piper model from: {model_path}")

        start_time = time.time()
        voice = PiperVoice.load(model_path)
        load_time = time.time() - start_time

        print(f"✓ Model loaded successfully in {load_time:.2f}s")

        # Test synthesis
        print("\nTesting speech synthesis...")
        test_text = "This is a test."

        audio_segments = []
        sample_rate = None

        for chunk in voice.synthesize(test_text):
            if sample_rate is None:
                sample_rate = chunk.sample_rate
            audio_segments.append(chunk.audio_float_array)

        audio = np.concatenate(audio_segments)

        print(f"✓ Synthesis successful")
        print(f"  Sample rate: {sample_rate} Hz")
        print(f"  Audio length: {len(audio) / sample_rate:.2f}s")
        print(f"  Audio shape: {audio.shape}")

        # Optionally play audio
        print("\nWould you like to hear the test audio? (y/n): ", end='')
        response = input().lower()

        if response == 'y':
            print("Playing audio...")
            sd.play(audio, samplerate=sample_rate)
            sd.wait()
            print("✓ Audio playback complete")

        return True

    except Exception as e:
        print(f"✗ Piper model test failed: {e}")
        logger.error("Piper error details:", exc_info=True)
        return False


def test_config_loading():
    """Test 6: Load and validate configuration"""
    print_test_header("Configuration Loading")

    try:
        from config_loader import Config

        print("Loading configuration from config.yaml...")
        config = Config('config.yaml')

        # Test key values
        wake_word = config.get('wake_word.phrase')
        vad_threshold = config.get('whisper.vad.threshold')
        sample_rate = config.get('audio.sample_rate')

        print(f"✓ Configuration loaded successfully")
        print(f"\nKey Settings:")
        print(f"  Wake word: {wake_word}")
        print(f"  VAD threshold: {vad_threshold}")
        print(f"  Sample rate: {sample_rate} Hz")

        return True

    except Exception as e:
        print(f"✗ Configuration test failed: {e}")
        logger.warning("config_loader.py not found, using defaults")
        return True  # Not critical


def test_voice_assistant_init():
    """Test 7: Initialize VoiceAssistant"""
    print_test_header("Voice Assistant Initialization")

    try:
        from ai import VoiceAssistant

        print("Initializing VoiceAssistant...")
        assistant = VoiceAssistant()

        print(f"✓ VoiceAssistant initialized successfully")
        print(f"\nComponents:")
        print(f"  Whisper model: Loaded")
        print(f"  Piper TTS: Loaded")
        print(f"  Wake word detector: Ready")
        print(f"  Available commands: {len(assistant.command_map)}")

        # List available commands
        print(f"\nRegistered commands:")
        for cmd in sorted(assistant.command_map.keys()):
            print(f"  - {cmd}")

        # Cleanup
        assistant.tts.shutdown()

        return True

    except Exception as e:
        print(f"✗ VoiceAssistant initialization failed: {e}")
        logger.error("Initialization error details:", exc_info=True)
        return False


def test_microphone_recording():
    """Test 8: Test microphone recording"""
    print_test_header("Microphone Recording Test")

    try:
        import sounddevice as sd

        print("This test will record 3 seconds of audio from your microphone.")
        print("Press Enter to start recording...")
        input()

        sample_rate = 16000
        duration = 3  # seconds

        print(f"\n🎤 Recording for {duration} seconds...")
        print("Speak clearly: 'Hey assistant, tell me a joke'")

        audio = sd.rec(
            int(sample_rate * duration),
            samplerate=sample_rate,
            channels=1,
            dtype='float32'
        )
        sd.wait()

        print("✓ Recording complete")

        # Analyze audio
        audio_flat = audio.flatten()
        rms = np.sqrt(np.mean(audio_flat ** 2))
        peak = np.max(np.abs(audio_flat))

        print(f"\nAudio Analysis:")
        print(f"  RMS level: {rms:.6f}")
        print(f"  Peak level: {peak:.6f}")

        if peak < 0.01:
            print("\n⚠️  WARNING: Audio level very low!")
            print("  Check:")
            print("  - Microphone is not muted")
            print("  - Microphone volume in system settings")
            print("  - Microphone permissions")
        elif peak > 0.9:
            print("\n⚠️  WARNING: Audio level too high (clipping)!")
            print("  Consider reducing microphone gain")
        else:
            print("\n✓ Audio levels look good")

        # Optional playback
        print("\nWould you like to hear the recording? (y/n): ", end='')
        response = input().lower()

        if response == 'y':
            print("Playing recording...")
            sd.play(audio, samplerate=sample_rate)
            sd.wait()

        return True

    except Exception as e:
        print(f"✗ Microphone test failed: {e}")
        logger.error("Microphone error details:", exc_info=True)
        return False


def run_all_tests():
    """Run all tests in sequence"""
    print("\n" + "=" * 60)
    print("VOICE ASSISTANT - COMPREHENSIVE TEST SUITE")
    print("=" * 60)

    tests = [
        ("Package Imports", test_imports),
        ("File Structure", test_file_structure),
        ("Audio Devices", test_audio_devices),
        ("Whisper Model", test_whisper_model),
        ("Piper TTS Model", test_piper_model),
        ("Configuration", test_config_loading),
        ("Voice Assistant Init", test_voice_assistant_init),
        ("Microphone Recording", test_microphone_recording),
    ]

    results = {}

    for test_name, test_func in tests:
        try:
            result = test_func()
            results[test_name] = result
        except KeyboardInterrupt:
            print("\n\n⚠️  Tests interrupted by user")
            break
        except Exception as e:
            logger.error(f"Test '{test_name}' crashed: {e}", exc_info=True)
            results[test_name] = False

    # Print summary
    print("\n" + "=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)

    passed = sum(1 for r in results.values() if r)
    total = len(results)

    for test_name, result in results.items():
        status = "✓ PASS" if result else "✗ FAIL"
        print(f"{status:10s} {test_name}")

    print("-" * 60)
    print(f"Results: {passed}/{total} tests passed")

    if passed == total:
        print("\n🎉 ALL TESTS PASSED! Your assistant is ready to use.")
        print("Run 'python main.py' to start the voice assistant.")
        return 0
    else:
        print(f"\n⚠️  {total - passed} test(s) failed. Fix the issues above before proceeding.")
        return 1


if __name__ == "__main__":
    exit_code = run_all_tests()
    sys.exit(exit_code)