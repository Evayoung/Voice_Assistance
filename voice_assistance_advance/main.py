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
    assistant = None

    try:
        logger.info("=" * 60)
        logger.info("Voice Assistant Starting...")
        logger.info("=" * 60)

        assistant = VoiceAssistant()
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
"""

from bytez import Bytez

key = "PASTE_YOUR_KEY_HERE"

def main():
    # load the sdk with your key
    sdk = Bytez(key)

    # pick a model
    model = sdk.model("anthropic/claude-haiku-4-5")
    # model = sdk.model("google/gemini-2.5-flash")
    # model = sdk.model("openai/gpt-5-nano")
    # model = sdk.model("cohere/command-r-08-2024")
    # model = sdk.model("mistral/mistral-small-2409")

    # run the model
    result = model.run([
        {"role": "system", "content": "You're a chatbot that talks like a pirate"},
        {"role": "user",   "content": "Tell me a joke"},
    ])

    # inspect results
    print("error", result.error)
    print("output", result.output)
    print("provider", result.provider)


# module exports
# ignore the stuff below
from js import globalThis

globalThis.key = key
globalThis.main = main
"""