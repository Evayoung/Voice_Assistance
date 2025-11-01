"""
Voice Assistant for Blind Students
Production Entry Point with Error Handling
"""
import sys
import logging
from ai import VoiceAssistant

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('voice_assistant.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


def main():
    """Main entry point with comprehensive error handling"""
    assistant = None

    try:
        logger.info("=" * 60)
        logger.info("Voice Assistant Starting...")
        logger.info("=" * 60)

        # Initialize assistant
        assistant = VoiceAssistant()

        # Start listening
        assistant.listen()

    except FileNotFoundError as e:
        logger.critical(f"FATAL: Required files not found: {e}")
        print("\n" + "=" * 60)
        print("STARTUP ERROR - Missing Required Files")
        print("=" * 60)
        print(f"\nError: {e}")
        print("\nPlease ensure:")
        print("1. 'whisper_model' folder exists with model files")
        print("2. Piper ONNX model file exists")
        print("\nExpected structure:")
        print("AI_Assistance/")
        print("├── ai.py")
        print("├── main.py")
        print("├── en_GB-southern_english_female-low.onnx")
        print("├── en_GB-southern_english_female-low.onnx.json")
        print("└── whisper_model/")
        print("    ├── config.json")
        print("    ├── model.bin")
        print("    ├── tokenizer.json")
        print("    └── vocabulary.txt")
        return 1

    except KeyboardInterrupt:
        logger.info("Keyboard interrupt received - shutting down gracefully")
        print("\n\nShutting down gracefully...")
        return 0

    except Exception as e:
        logger.critical(f"FATAL: Unrecoverable error: {e}", exc_info=True)
        print("\n" + "=" * 60)
        print("CRITICAL ERROR")
        print("=" * 60)
        print(f"\nAn unexpected error occurred: {e}")
        print("\nCheck 'voice_assistant.log' for detailed information")
        return 1

    finally:
        if assistant:
            try:
                assistant._cleanup()
            except Exception as e:
                logger.error(f"Error during cleanup: {e}")

        logger.info("Voice Assistant terminated")
        print("\nGoodbye!")


if __name__ == "__main__":
    sys.exit(main())