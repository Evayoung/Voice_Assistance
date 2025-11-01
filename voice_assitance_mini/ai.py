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
from typing import Optional, Callable
import time

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

# --- Constants ---
WHISPER_MODEL_DIR = os.path.join(os.path.dirname(__file__), "whisper_model")
WAKE_WORD = "hey assistant"
WAKE_WORD_TIMEOUT = 10  # seconds to stay active after wake word


class PiperTTS:
    """Thread-safe Piper TTS class with non-blocking speech queue"""

    def __init__(self, model_path: str):
        logger.info("Loading Piper voice model...")
        if not os.path.exists(model_path):
            raise FileNotFoundError(f"Piper model not found at {model_path}")

        self.voice = PiperVoice.load(model_path)
        logger.info("Piper voice loaded successfully.")

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
                # Wait for speech request with timeout
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
        """
        Synthesize and speak text.

        Args:
            text: Text to speak
            blocking: If True, wait for speech to complete
        """
        if blocking:
            self._speak_blocking(text)
        else:
            self.speech_queue.put(text)

    def wait_until_done(self):
        """Wait until all queued speech is complete"""
        self.speech_queue.join()
        while self.is_speaking.is_set():
            time.sleep(0.1)

    def shutdown(self):
        """Gracefully shutdown TTS system"""
        logger.info("Shutting down TTS...")
        self.shutdown_flag.set()
        self.speech_queue.put(None)  # Signal to stop
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
        """
        Check if text contains wake word.

        Returns:
            True if wake word detected or system is awake
        """
        text_lower = text.lower().strip()

        # Check for exact match or substring
        if self.wake_word in text_lower:
            logger.info("Wake word detected!")
            self.is_awake = True
            self.last_wake_time = time.time()
            return True

        # If already awake, check if still within timeout
        if self.is_awake:
            if time.time() - self.last_wake_time < self.timeout:
                return True
            else:
                logger.info("Wake word timeout - going to sleep")
                self.is_awake = False
                return False

        return False

    def reset(self):
        """Reset wake state"""
        self.is_awake = False
        self.last_wake_time = 0


class VoiceAssistant:
    """Production-ready voice assistant with error recovery and logging"""

    def __init__(self):
        logger.info("Initializing Voice Assistant...")

        # Error recovery
        self.restart_count = 0
        self.max_restarts = 3

        # Initialize components with error handling
        self._initialize_whisper()
        self._initialize_tts()
        self._initialize_wake_word()

        # Command dispatcher
        self.command_map = {
            "joke": self._skill_tell_joke,
            "time": self._skill_tell_time,
            "date": self._skill_tell_time,
            "stop": self._skill_exit,
            "exit": self._skill_exit,
            "goodbye": self._skill_exit,
            "sleep": self._skill_sleep,
        }

        # Audio stream
        self.audio_q = queue.Queue()
        self.keep_running = True
        self.sample_rate = 16000

        logger.info("Voice Assistant initialized successfully")

    def _initialize_whisper(self):
        """Initialize Whisper with error handling"""
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
                device="cpu",
                compute_type="int8"
            )
            logger.info("Whisper model loaded successfully")

        except Exception as e:
            logger.critical(f"Failed to initialize Whisper: {e}", exc_info=True)
            raise

    def _initialize_tts(self):
        """Initialize TTS with error handling"""
        try:
            model_path = os.path.join(
                os.path.dirname(__file__),
                "en_GB-southern_english_female-low.onnx"
            )
            self.tts = PiperTTS(model_path)
        except Exception as e:
            logger.critical(f"Failed to initialize TTS: {e}", exc_info=True)
            raise

    def _initialize_wake_word(self):
        """Initialize wake word detector"""
        self.wake_word_detector = WakeWordDetector(WAKE_WORD)

    # --- Skill Methods ---
    def _skill_tell_joke(self):
        """Tell a programming joke"""
        try:
            joke = pyjokes.get_joke()
            logger.info(f"Telling joke: {joke}")
            self.tts.speak(joke)
        except Exception as e:
            logger.error(f"Error telling joke: {e}", exc_info=True)
            self.tts.speak("Sorry, I couldn't think of a joke right now.")

    def _skill_tell_time(self):
        """Tell current time and date"""
        try:
            now = datetime.datetime.now()
            time_str = now.strftime("It is %I:%M %p, on %A, %B %d.")
            logger.info(f"Telling time: {time_str}")
            self.tts.speak(time_str)
        except Exception as e:
            logger.error(f"Error telling time: {e}", exc_info=True)
            self.tts.speak("Sorry, I couldn't get the current time.")

    def _skill_sleep(self):
        """Put assistant to sleep (deactivate wake word)"""
        self.wake_word_detector.reset()
        self.tts.speak("Going to sleep. Say hey assistant to wake me up.")
        logger.info("Assistant going to sleep")

    def _skill_exit(self):
        """Gracefully exit the assistant"""
        logger.info("Exit command received")
        self.tts.speak("Goodbye! Shutting down now.")
        self.tts.wait_until_done()
        self.keep_running = False

    # --- Core Methods ---
    def callback(self, indata, frames, time_info, status):
        """Audio input callback"""
        if status:
            logger.warning(f"Audio callback status: {status}")
        self.audio_q.put(indata.copy())

    def handle_command(self, text: str):
        """Process recognized command"""
        text = text.lower().strip()
        if not text:
            return

        logger.info(f"Recognized: '{text}'")

        # Check wake word first
        if not self.wake_word_detector.check(text):
            logger.debug("Wake word not detected, ignoring command")
            return

        # Remove wake word from text if present
        command_text = text.replace(self.wake_word, "").strip()
        if not command_text and text != self.wake_word:
            return

        # If only wake word was said, acknowledge
        if not command_text or command_text == self.wake_word:
            self.tts.speak("Yes? I'm listening.")
            return

        # Check for matching command
        for trigger, skill_func in self.command_map.items():
            if trigger in command_text:
                logger.info(f"Executing skill: {trigger}")
                try:
                    skill_func()
                except Exception as e:
                    logger.error(f"Error executing skill '{trigger}': {e}", exc_info=True)
                    self.tts.speak("Sorry, something went wrong.")
                return

        # No matching command
        logger.debug(f"No matching command for: {command_text}")
        self.tts.speak(f"I heard you say {command_text}, but I don't know what to do with that yet.")

    def transcribe_audio(self, audio_buffer: np.ndarray) -> list:
        """
        Transcribe audio with improved VAD settings.

        Args:
            audio_buffer: Audio data to transcribe

        Returns:
            List of transcribed segments
        """
        try:
            # Improved VAD parameters for better noise rejection
            segments, info = self.model.transcribe(
                audio_buffer,
                vad_filter=True,
                vad_parameters={
                    "threshold": 0.5,  # Higher = more aggressive filtering (0.0-1.0)
                    "min_speech_duration_ms": 250,  # Minimum speech duration
                    "max_speech_duration_s": 30,  # Maximum speech duration
                    "min_silence_duration_ms": 500,  # Minimum silence to split
                    "speech_pad_ms": 400,  # Padding around speech
                },
                language="en",
                beam_size=5,  # Higher = more accurate but slower
                best_of=5,
                temperature=0.0,  # Deterministic output
                compression_ratio_threshold=2.4,
                log_prob_threshold=-1.0,
                no_speech_threshold=0.6,  # Higher = more aggressive filtering
                condition_on_previous_text=False,
            )

            return list(segments)

        except Exception as e:
            logger.error(f"Transcription error: {e}", exc_info=True)
            return []

    def listen(self):
        """Main listening loop with error recovery"""
        try:
            self.tts.speak("Assistant initialized. Say hey assistant to activate me.")
            logger.info("Assistant listening started")
            print(f"\n{'=' * 60}")
            print(f"Voice Assistant Active - Say '{WAKE_WORD}' to activate")
            print(f"Commands: joke, time, date, sleep, exit")
            print(f"{'=' * 60}\n")

            with sd.InputStream(
                    samplerate=self.sample_rate,
                    blocksize=4096,
                    dtype="float32",
                    channels=1,
                    callback=self.callback,
            ):
                audio_buffer = np.array([], dtype=np.float32)
                CHUNK_SIZE_SAMPLES = self.sample_rate * 3  # 3-second chunks

                while self.keep_running:
                    try:
                        # Get audio data with timeout
                        data = self.audio_q.get(timeout=0.5)
                        audio_buffer = np.concatenate((audio_buffer, data.flatten()))

                        # Process when buffer is large enough
                        if len(audio_buffer) >= CHUNK_SIZE_SAMPLES:
                            # Only transcribe if not currently speaking
                            if not self.tts.is_speaking.is_set():
                                segments = self.transcribe_audio(audio_buffer)

                                for segment in segments:
                                    text = segment.text.strip()
                                    if text:
                                        self.handle_command(text)

                            # Clear buffer
                            audio_buffer = np.array([], dtype=np.float32)

                    except queue.Empty:
                        continue

                    except Exception as e:
                        logger.error(f"Error in listen loop: {e}", exc_info=True)

                        # Attempt recovery
                        if self.restart_count < self.max_restarts:
                            self.restart_count += 1
                            logger.warning(f"Attempting recovery (attempt {self.restart_count}/{self.max_restarts})")
                            time.sleep(1)
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
        """Clean up resources"""
        logger.info("Cleaning up resources...")
        try:
            self.tts.shutdown()
        except Exception as e:
            logger.error(f"Error during cleanup: {e}", exc_info=True)
        logger.info("Shutdown complete")


if __name__ == "__main__":
    # This allows testing the module directly
    try:
        assistant = VoiceAssistant()
        assistant.listen()
    except Exception as e:
        logger.critical(f"Failed to start assistant: {e}", exc_info=True)
        raise