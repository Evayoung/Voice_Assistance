import os
import queue
import threading
import numpy as np
import sounddevice as sd
from faster_whisper import WhisperModel
from piper import PiperVoice
import pyjokes
import datetime
import logging
from typing import Optional, Callable, List
import time
import yaml

# Google Cloud Speech (optional - only imported if available)
try:
    from google.cloud import speech_v1

    GOOGLE_STT_AVAILABLE = True
except ImportError:
    GOOGLE_STT_AVAILABLE = False
    speech_v1 = None

# --- Logging Setup ---
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('voice_assistant.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


# --- Configuration Loader ---
def load_config(config_file='config.yaml'):
    """Load configuration from YAML file with defaults"""
    default_config = {
        'wake_word': {
            'phrase': 'assistant',
            'timeout': 10,
            'threshold': 0.7
        },
        'whisper': {
            'model_dir': 'whisper_model',
            'device': 'cpu',
            'compute_type': 'int8',
            'vad': {
                'enabled': True,
                'threshold': 0.45,
                'min_speech_duration_ms': 200,
                'max_speech_duration_s': 30,
                'min_silence_duration_ms': 500,
                'speech_pad_ms': 600,
                'no_speech_threshold': 0.5
            },
            'transcription': {
                'language': 'en',
                'beam_size': 3,
                'best_of': 3,
                'temperature': 0.0,
                'compression_ratio_threshold': 2.4,
                'log_prob_threshold': -1.0,
                'no_speech_threshold': 0.5
            },
            'accent_prompt': 'Nigerian English. West African accent. Common Nigerian names and expressions.'
        },
        'piper': {
            'model_file': 'voices/en_US-bryce-medium.onnx',
            'blocking_mode': False
        },
        'audio': {
            'sample_rate': 16000,
            'chunk_duration_seconds': 3,
            'blocksize': 4096,
            'channels': 1,
            'rms_threshold': 0.015,
            'peak_threshold': 0.04,
            'noise_gate_threshold': 0.01
        },
        'logging': {
            'level': 'INFO',
            'file': 'voice_assistant.log',
            'console': True
        },
        'error_recovery': {
            'max_restart_attempts': 3,
            'restart_delay_seconds': 1
        }
    }

    if os.path.exists(config_file):
        try:
            with open(config_file, 'r') as f:
                user_config = yaml.safe_load(f)

            # Merge user config with defaults (deep merge)
            def merge_dict(base, update):
                for key, value in update.items():
                    if key in base and isinstance(base[key], dict) and isinstance(value, dict):
                        merge_dict(base[key], value)
                    else:
                        base[key] = value

            merge_dict(default_config, user_config)
            logger.info(f"Configuration loaded from {config_file}")
        except Exception as e:
            logger.warning(f"Error loading config file: {e}, using defaults")
    else:
        logger.warning(f"Config file {config_file} not found, using defaults")
        # Save default config
        try:
            with open(config_file, 'w') as f:
                yaml.dump(default_config, f, default_flow_style=False, sort_keys=False)
            logger.info(f"Default configuration saved to {config_file}")
        except Exception as e:
            logger.error(f"Could not save default config: {e}")

    return default_config


# Load global config
CONFIG = load_config()

# --- Constants from Config ---
WHISPER_MODEL_DIR = os.path.join(os.path.dirname(__file__), CONFIG['whisper']['model_dir'])
WAKE_WORD = CONFIG['wake_word']['phrase']
WAKE_WORD_TIMEOUT = CONFIG['wake_word']['timeout']


# --- Utility Audio Filters ---
def is_significant_audio(audio, rms_threshold=None, peak_threshold=None):
    """Check if audio contains significant sound energy."""
    if rms_threshold is None:
        rms_threshold = CONFIG['audio']['rms_threshold']
    if peak_threshold is None:
        peak_threshold = CONFIG['audio']['peak_threshold']

    if len(audio) == 0:
        return False
    rms = np.sqrt(np.mean(audio ** 2))
    peak = np.max(np.abs(audio))
    return rms > rms_threshold or peak > peak_threshold


def noise_gate(audio, threshold=None):
    """Simple noise gate to mute low-level sounds."""
    if threshold is None:
        threshold = CONFIG['audio']['noise_gate_threshold']
    mask = np.abs(audio) > threshold
    return audio * mask


class PiperTTS:
    """Thread-safe Piper TTS class with non-blocking speech queue"""

    def __init__(self, model_path: str):
        logger.info("Loading Piper voice model...")
        if not os.path.exists(model_path):
            raise FileNotFoundError(f"Piper model not found at {model_path}")

        self.voice = PiperVoice.load(model_path)
        logger.info(f"Piper voice loaded: {os.path.basename(model_path)}")

        self.lock = threading.Lock()
        self.samplerate = None

        # Non-blocking TTS queue
        self.speech_queue = queue.Queue()
        self.is_speaking = threading.Event()
        self.shutdown_flag = threading.Event()

        # Start background speech thread
        self.speech_thread = threading.Thread(target=self._speech_worker, daemon=True)
        self.speech_thread.start()
        logger.info("TTS worker thread started")

    def _speech_worker(self):
        """Background worker that processes speech queue"""
        while not self.shutdown_flag.is_set():
            try:
                text = self.speech_queue.get(timeout=0.5)
                if text is None:  # Shutdown signal
                    break

                self.is_speaking.set()
                self._speak_blocking(text)
                self.is_speaking.clear()
                self.speech_queue.task_done()

            except queue.Empty:
                continue
            except Exception as e:
                logger.error(f"Error in speech worker: {e}", exc_info=True)
                self.is_speaking.clear()

    def _speak_blocking(self, text: str):
        """Internal blocking speech synthesis"""
        with self.lock:
            logger.info(f"Speaking: {text[:50]}{'...' if len(text) > 50 else ''}")
            try:
                audio_segments = []
                for chunk in self.voice.synthesize(text):
                    if self.samplerate is None:
                        self.samplerate = chunk.sample_rate
                        logger.debug(f"TTS sample rate: {self.samplerate} Hz")
                    audio_segments.append(chunk.audio_float_array)

                if not audio_segments:
                    logger.warning("No audio data generated")
                    return

                audio = np.concatenate(audio_segments)
                sd.play(audio, samplerate=self.samplerate)
                sd.wait()

            except Exception as e:
                logger.error(f"TTS error for '{text[:30]}...': {e}", exc_info=True)

    def speak(self, text: str, blocking: bool = False):
        if blocking:
            self._speak_blocking(text)
        else:
            self.speech_queue.put(text)

    def wait_until_done(self):
        self.speech_queue.join()
        while self.is_speaking.is_set():
            time.sleep(0.1)

    def shutdown(self):
        logger.info("Shutting down TTS...")
        self.shutdown_flag.set()
        self.speech_queue.put(None)
        self.speech_thread.join(timeout=2)


class WakeWordDetector:
    """Simple wake word detection using fuzzy matching"""

    def __init__(self, wake_word: str, threshold: float = 0.7):
        self.wake_word = wake_word.lower()
        self.threshold = threshold
        self.is_awake = False
        self.last_wake_time = 0
        self.timeout = WAKE_WORD_TIMEOUT
        logger.info(f"Wake word detector initialized: '{wake_word}'")

    def check(self, text: str) -> bool:
        text_lower = text.lower().strip()

        if self.wake_word in text_lower:
            logger.info("Wake word detected!")
            self.is_awake = True
            self.last_wake_time = time.time()
            return True

        if self.is_awake:
            if time.time() - self.last_wake_time < self.timeout:
                return True
            else:
                logger.info("Wake word timeout - going to sleep")
                self.is_awake = False
                return False

        return False

    def reset(self):
        self.is_awake = False
        self.last_wake_time = 0


class VoiceAssistant:
    """Production-ready voice assistant with config-based settings"""

    def __init__(self):
        logger.info("Initializing Voice Assistant...")

        # Load config
        self.config = CONFIG

        # Get model info
        model_name = os.path.basename(self.config['whisper']['model_dir'])
        logger.info(f"Using Whisper model: {model_name}")

        # Error recovery
        self.restart_count = 0
        self.max_restarts = self.config['error_recovery']['max_restart_attempts']

        self._initialize_whisper()
        self._initialize_tts()
        self._initialize_wake_word()

        self.command_map = {
            "joke": self._skill_tell_joke,
            "time": self._skill_tell_time,
            "date": self._skill_tell_time,
            "stop": self._skill_exit,
            "exit": self._skill_exit,
            "goodbye": self._skill_exit,
            "sleep": self._skill_sleep,
        }

        self.audio_q = queue.Queue()
        self.keep_running = True
        self.sample_rate = self.config['audio']['sample_rate']

        logger.info("Voice Assistant initialized successfully")

    def _initialize_whisper(self):
        try:
            if not os.path.isdir(WHISPER_MODEL_DIR) or not os.path.exists(
                    os.path.join(WHISPER_MODEL_DIR, "model.bin")
            ):
                raise FileNotFoundError(
                    f"Local Whisper model files not found at '{WHISPER_MODEL_DIR}'"
                )

            logger.info(f"Loading Whisper model from: {WHISPER_MODEL_DIR}")
            self.model = WhisperModel(
                WHISPER_MODEL_DIR,
                device=self.config['whisper']['device'],
                compute_type=self.config['whisper']['compute_type']
            )
            logger.info("Whisper model loaded successfully")

        except Exception as e:
            logger.critical(f"Failed to initialize Whisper: {e}", exc_info=True)
            raise

    def _initialize_tts(self):
        try:
            model_file = self.config['piper']['model_file']
            model_path = os.path.join(os.path.dirname(__file__), model_file)

            if not os.path.exists(model_path):
                raise FileNotFoundError(f"Piper model not found: {model_path}")

            self.tts = PiperTTS(model_path)

        except Exception as e:
            logger.critical(f"Failed to initialize TTS: {e}", exc_info=True)
            raise

    def _initialize_wake_word(self):
        self.wake_word_detector = WakeWordDetector(
            WAKE_WORD,
            threshold=self.config['wake_word']['threshold']
        )

    # --- Skills ---
    def _skill_tell_joke(self):
        try:
            joke = pyjokes.get_joke()
            logger.info(f"Telling joke: {joke}")
            self.tts.speak(joke)
        except Exception as e:
            logger.error(f"Error telling joke: {e}", exc_info=True)
            self.tts.speak("Sorry, I couldn't think of a joke right now.")

    def _skill_tell_time(self):
        try:
            now = datetime.datetime.now()
            time_str = now.strftime("It is %I:%M %p, on %A, %B %d.")
            logger.info(f"Telling time: {time_str}")
            self.tts.speak(time_str)
        except Exception as e:
            logger.error(f"Error telling time: {e}", exc_info=True)
            self.tts.speak("Sorry, I couldn't get the current time.")

    def _skill_sleep(self):
        self.wake_word_detector.reset()
        self.tts.speak(f"Going to sleep. Say {WAKE_WORD} to wake me up.")
        logger.info("Assistant going to sleep")

    def _skill_exit(self):
        logger.info("Exit command received")
        self.tts.speak("Goodbye! Shutting down now.")
        self.tts.wait_until_done()
        self.keep_running = False

    # --- Core Logic ---
    def callback(self, indata, frames, time_info, status):
        if status:
            logger.warning(f"Audio callback status: {status}")
        self.audio_q.put(indata.copy())

    def handle_command(self, text: str):
        text = text.lower().strip()
        if not text:
            return

        logger.info(f"Recognized: '{text}'")

        if not self.wake_word_detector.check(text):
            logger.debug("Wake word not detected, ignoring command")
            return

        command_text = text.replace(WAKE_WORD, "").strip()
        if not command_text and text != WAKE_WORD:
            return

        if not command_text or command_text == WAKE_WORD:
            self.tts.speak("Yes? I'm listening.")
            return

        for trigger, skill_func in self.command_map.items():
            if trigger in command_text:
                logger.info(f"Executing skill: {trigger}")
                try:
                    skill_func()
                except Exception as e:
                    logger.error(f"Error executing skill '{trigger}': {e}", exc_info=True)
                    self.tts.speak("Sorry, something went wrong.")
                return

        logger.debug(f"No matching command for: {command_text}")
        self.tts.speak(f"I heard you say {command_text}, but I don't know what to do with that yet.")

    def transcribe_audio(self, audio_buffer: np.ndarray) -> list:
        """Transcribe audio using config-based settings"""
        try:
            vad_config = self.config['whisper']['vad']
            trans_config = self.config['whisper']['transcription']

            segments, info = self.model.transcribe(
                audio_buffer,

                # VAD settings from config
                vad_filter=vad_config['enabled'],
                vad_parameters={
                    "threshold": vad_config['threshold'],
                    "min_speech_duration_ms": vad_config['min_speech_duration_ms'],
                    "max_speech_duration_s": vad_config['max_speech_duration_s'],
                    "min_silence_duration_ms": vad_config['min_silence_duration_ms'],
                    "speech_pad_ms": vad_config['speech_pad_ms'],
                },

                # Transcription settings from config
                language=trans_config['language'],
                beam_size=trans_config['beam_size'],
                best_of=trans_config['best_of'],
                temperature=trans_config['temperature'],
                compression_ratio_threshold=trans_config['compression_ratio_threshold'],
                log_prob_threshold=trans_config['log_prob_threshold'],
                no_speech_threshold=trans_config['no_speech_threshold'],
                condition_on_previous_text=False,

                # Accent prompt from config
                initial_prompt=self.config['whisper'].get('accent_prompt', ''),

                # Performance settings
                word_timestamps=False,
            )

            return list(segments)

        except Exception as e:
            logger.error(f"Transcription error: {e}", exc_info=True)
            return []

    def listen(self):
        try:
            # Get model and voice info for display
            model_name = os.path.basename(self.config['whisper']['model_dir'])
            voice_name = os.path.basename(self.config['piper']['model_file']).replace('.onnx', '')

            self.tts.speak(f"Assistant initialized. Say {WAKE_WORD} to activate me.")
            logger.info("Assistant listening started")

            print(f"\n{'=' * 60}")
            print(f"Voice Assistant Active - Say '{WAKE_WORD}' to activate")
            print(f"Commands: joke, time, date, sleep, exit")
            print(f"Whisper Model: {model_name}")
            print(f"Voice: {voice_name}")
            print(f"VAD Threshold: {self.config['whisper']['vad']['threshold']}")
            print(f"{'=' * 60}\n")

            with sd.InputStream(
                    samplerate=self.sample_rate,
                    blocksize=self.config['audio']['blocksize'],
                    dtype="float32",
                    channels=self.config['audio']['channels'],
                    callback=self.callback,
            ):
                audio_buffer = np.array([], dtype=np.float32)
                chunk_duration = self.config['audio']['chunk_duration_seconds']
                CHUNK_SIZE_SAMPLES = self.sample_rate * chunk_duration

                while self.keep_running:
                    try:
                        data = self.audio_q.get(timeout=0.5)
                        audio_buffer = np.concatenate((audio_buffer, data.flatten()))

                        if len(audio_buffer) >= CHUNK_SIZE_SAMPLES:
                            # Check if audio contains significant sound
                            if not is_significant_audio(audio_buffer):
                                logger.debug("No significant audio detected, skipping")
                                audio_buffer = np.array([], dtype=np.float32)
                                continue

                            # Apply noise gate
                            audio_buffer = noise_gate(audio_buffer)

                            # Only transcribe if not currently speaking
                            if not self.tts.is_speaking.is_set():
                                logger.debug("Transcribing audio chunk...")
                                segments = self.transcribe_audio(audio_buffer)

                                for segment in segments:
                                    text = segment.text.strip()
                                    if text:
                                        self.handle_command(text)
                            else:
                                logger.debug("TTS is speaking, skipping transcription")

                            # Clear buffer
                            audio_buffer = np.array([], dtype=np.float32)

                    except queue.Empty:
                        continue

                    except Exception as e:
                        logger.error(f"Error in listen loop: {e}", exc_info=True)
                        if self.restart_count < self.max_restarts:
                            self.restart_count += 1
                            restart_delay = self.config['error_recovery']['restart_delay_seconds']
                            logger.warning(f"Attempting recovery ({self.restart_count}/{self.max_restarts})")
                            time.sleep(restart_delay)
                            continue
                        else:
                            logger.critical("Max restart attempts reached, shutting down")
                            raise

        except KeyboardInterrupt:
            logger.info("Keyboard interrupt received")
            self.keep_running = False

        except Exception as e:
            logger.critical(f"Fatal error in listen loop: {e}", exc_info=True)
            raise

        finally:
            self._cleanup()

    def _cleanup(self):
        logger.info("Cleaning up resources...")
        try:
            self.tts.shutdown()
        except Exception as e:
            logger.error(f"Error during cleanup: {e}", exc_info=True)
        logger.info("Shutdown complete")


if __name__ == "__main__":
    try:
        assistant = VoiceAssistant()
        assistant.listen()
    except Exception as e:
        logger.critical(f"Failed to start assistant: {e}", exc_info=True)
        raise