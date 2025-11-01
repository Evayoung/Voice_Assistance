"""
Quick Tune - Interactive configuration tuner for Voice Assistant
Helps adjust VAD settings based on your environment
"""
import yaml
import os
import sys
from pathlib import Path


class QuickTune:
    """Interactive configuration tuner"""

    PRESETS = {
        'quiet': {
            'name': 'Quiet Room',
            'description': 'Library, office, bedroom',
            'settings': {
                'whisper.vad.threshold': 0.4,
                'whisper.vad.no_speech_threshold': 0.5,
                'whisper.transcription.no_speech_threshold': 0.5,
            }
        },
        'normal': {
            'name': 'Normal Environment',
            'description': 'Home, casual office',
            'settings': {
                'whisper.vad.threshold': 0.5,
                'whisper.vad.no_speech_threshold': 0.6,
                'whisper.transcription.no_speech_threshold': 0.6,
            }
        },
        'noisy': {
            'name': 'Noisy Environment',
            'description': 'Open office, cafe, with TV/radio',
            'settings': {
                'whisper.vad.threshold': 0.7,
                'whisper.vad.no_speech_threshold': 0.75,
                'whisper.transcription.no_speech_threshold': 0.7,
            }
        },
        'very_noisy': {
            'name': 'Very Noisy',
            'description': 'Street, construction, crowd',
            'settings': {
                'whisper.vad.threshold': 0.8,
                'whisper.vad.no_speech_threshold': 0.8,
                'whisper.transcription.no_speech_threshold': 0.75,
                'whisper.vad.min_speech_duration_ms': 350,
            }
        },
    }

    def __init__(self, config_file='config.yaml'):
        self.config_file = config_file
        self.config = self.load_config()

    def load_config(self):
        """Load existing configuration"""
        if not os.path.exists(self.config_file):
            print(f"Config file '{self.config_file}' not found.")
            print("Creating from default...")
            return self.create_default_config()

        with open(self.config_file, 'r') as f:
            return yaml.safe_load(f)

    def save_config(self):
        """Save configuration to file"""
        with open(self.config_file, 'w') as f:
            yaml.dump(self.config, f, default_flow_style=False, sort_keys=False)
        print(f"\n✓ Configuration saved to {self.config_file}")

    def create_default_config(self):
        """Create default configuration"""
        return {
            'wake_word': {
                'phrase': 'hey assistant',
                'timeout': 10,
                'threshold': 0.7
            },
            'whisper': {
                'vad': {
                    'threshold': 0.5,
                    'min_speech_duration_ms': 250,
                    'no_speech_threshold': 0.6,
                },
                'transcription': {
                    'no_speech_threshold': 0.6,
                    'beam_size': 5,
                }
            }
        }

    def set_value(self, key_path, value):
        """Set configuration value using dot notation"""
        keys = key_path.split('.')
        config = self.config

        for key in keys[:-1]:
            if key not in config:
                config[key] = {}
            config = config[key]

        config[keys[-1]] = value

    def get_value(self, key_path, default=None):
        """Get configuration value using dot notation"""
        keys = key_path.split('.')
        value = self.config

        for key in keys:
            if isinstance(value, dict) and key in value:
                value = value[key]
            else:
                return default

        return value

    def apply_preset(self, preset_key):
        """Apply a preset configuration"""
        if preset_key not in self.PRESETS:
            print(f"Unknown preset: {preset_key}")
            return False

        preset = self.PRESETS[preset_key]
        print(f"\nApplying preset: {preset['name']}")
        print(f"Description: {preset['description']}")

        for key, value in preset['settings'].items():
            self.set_value(key, value)
            print(f"  {key} = {value}")

        return True

    def interactive_menu(self):
        """Show interactive configuration menu"""
        while True:
            self.show_menu()
            choice = input("\nEnter your choice (1-7): ").strip()

            if choice == '1':
                self.select_preset()
            elif choice == '2':
                self.adjust_noise_sensitivity()
            elif choice == '3':
                self.adjust_speech_detection()
            elif choice == '4':
                self.adjust_wake_word()
            elif choice == '5':
                self.adjust_performance()
            elif choice == '6':
                self.view_current_settings()
            elif choice == '7':
                self.save_config()
                print("\nGoodbye!")
                break
            else:
                print("Invalid choice. Please try again.")

    def show_menu(self):
        """Display main menu"""
        print("\n" + "=" * 60)
        print("VOICE ASSISTANT - QUICK TUNE")
        print("=" * 60)
        print("\n1. Select Environment Preset")
        print("2. Adjust Noise Sensitivity")
        print("3. Adjust Speech Detection")
        print("4. Adjust Wake Word")
        print("5. Adjust Performance")
        print("6. View Current Settings")
        print("7. Save and Exit")

    def select_preset(self):
        """Select environment preset"""
        print("\n" + "-" * 60)
        print("ENVIRONMENT PRESETS")
        print("-" * 60)

        presets = list(self.PRESETS.items())
        for i, (key, preset) in enumerate(presets, 1):
            print(f"\n{i}. {preset['name']}")
            print(f"   {preset['description']}")

        choice = input(f"\nSelect preset (1-{len(presets)}) or 0 to cancel: ").strip()

        try:
            choice_num = int(choice)
            if choice_num == 0:
                return
            if 1 <= choice_num <= len(presets):
                preset_key = presets[choice_num - 1][0]
                self.apply_preset(preset_key)
                print("\n✓ Preset applied successfully")
            else:
                print("Invalid choice")
        except ValueError:
            print("Invalid input")

    def adjust_noise_sensitivity(self):
        """Adjust noise filtering"""
        print("\n" + "-" * 60)
        print("NOISE SENSITIVITY")
        print("-" * 60)

        current = self.get_value('whisper.vad.threshold', 0.5)
        print(f"\nCurrent VAD threshold: {current}")
        print("\nGuidelines:")
        print("  0.3-0.4: Very sensitive (picks up everything)")
        print("  0.5-0.6: Balanced (recommended)")
        print("  0.7-0.8: Strict (filters most noise)")
        print("  0.9+:    Very strict (may miss speech)")

        new_value = input(f"\nEnter new threshold (0.1-0.9) or press Enter to keep current: ").strip()

        if new_value:
            try:
                threshold = float(new_value)
                if 0.1 <= threshold <= 0.9:
                    self.set_value('whisper.vad.threshold', threshold)
                    self.set_value('whisper.vad.no_speech_threshold', threshold + 0.1)
                    self.set_value('whisper.transcription.no_speech_threshold', threshold + 0.1)
                    print(f"✓ Threshold set to {threshold}")
                else:
                    print("Value out of range")
            except ValueError:
                print("Invalid number")

    def adjust_speech_detection(self):
        """Adjust speech detection parameters"""
        print("\n" + "-" * 60)
        print("SPEECH DETECTION")
        print("-" * 60)

        print("\n1. Minimum speech duration")
        print("2. Speech padding")
        print("3. Silence duration (sentence splitting)")
        print("0. Back")

        choice = input("\nSelect option: ").strip()

        if choice == '1':
            current = self.get_value('whisper.vad.min_speech_duration_ms', 250)
            print(f"\nCurrent: {current}ms")
            print("Lower = catch shorter words (100-150ms)")
            print("Higher = ignore quick sounds (400-500ms)")

            new_value = input("\nEnter new value (ms): ").strip()
            if new_value:
                try:
                    value = int(new_value)
                    self.set_value('whisper.vad.min_speech_duration_ms', value)
                    print(f"✓ Set to {value}ms")
                except ValueError:
                    print("Invalid number")

        elif choice == '2':
            current = self.get_value('whisper.vad.speech_pad_ms', 400)
            print(f"\nCurrent: {current}ms")
            print("Extra audio added before/after speech")
            print("Increase if words get cut off (500-800ms)")

            new_value = input("\nEnter new value (ms): ").strip()
            if new_value:
                try:
                    value = int(new_value)
                    self.set_value('whisper.vad.speech_pad_ms', value)
                    print(f"✓ Set to {value}ms")
                except ValueError:
                    print("Invalid number")

        elif choice == '3':
            current = self.get_value('whisper.vad.min_silence_duration_ms', 500)
            print(f"\nCurrent: {current}ms")
            print("How long silence must be to split sentences")
            print("Lower = split faster (300-400ms)")
            print("Higher = keep sentences together (800-1000ms)")

            new_value = input("\nEnter new value (ms): ").strip()
            if new_value:
                try:
                    value = int(new_value)
                    self.set_value('whisper.vad.min_silence_duration_ms', value)
                    print(f"✓ Set to {value}ms")
                except ValueError:
                    print("Invalid number")

    def adjust_wake_word(self):
        """Adjust wake word settings"""
        print("\n" + "-" * 60)
        print("WAKE WORD SETTINGS")
        print("-" * 60)

        current_phrase = self.get_value('wake_word.phrase', 'hey assistant')
        current_timeout = self.get_value('wake_word.timeout', 10)

        print(f"\nCurrent phrase: '{current_phrase}'")
        print(f"Current timeout: {current_timeout}s")

        print("\n1. Change wake word phrase")
        print("2. Change timeout duration")
        print("0. Back")

        choice = input("\nSelect option: ").strip()

        if choice == '1':
            new_phrase = input("\nEnter new wake word phrase: ").strip()
            if new_phrase:
                self.set_value('wake_word.phrase', new_phrase.lower())
                print(f"✓ Wake word set to: '{new_phrase}'")

        elif choice == '2':
            print("\nHow long to stay active after wake word?")
            print("Shorter = more secure, need to say wake word more often")
            print("Longer = more convenient, stays active longer")

            new_timeout = input("\nEnter timeout (seconds): ").strip()
            if new_timeout:
                try:
                    timeout = int(new_timeout)
                    self.set_value('wake_word.timeout', timeout)
                    print(f"✓ Timeout set to {timeout}s")
                except ValueError:
                    print("Invalid number")

    def adjust_performance(self):
        """Adjust performance/quality tradeoff"""
        print("\n" + "-" * 60)
        print("PERFORMANCE TUNING")
        print("-" * 60)

        current_beam = self.get_value('whisper.transcription.beam_size', 5)
        print(f"\nCurrent beam size: {current_beam}")
        print("\nBeam size affects accuracy vs speed:")
        print("  1: Fastest, less accurate")
        print("  3: Balanced")
        print("  5: Most accurate, slower (recommended)")

        new_beam = input("\nEnter beam size (1-5): ").strip()

        if new_beam:
            try:
                beam = int(new_beam)
                if 1 <= beam <= 5:
                    self.set_value('whisper.transcription.beam_size', beam)
                    self.set_value('whisper.transcription.best_of', beam)
                    print(f"✓ Beam size set to {beam}")
                else:
                    print("Value out of range")
            except ValueError:
                print("Invalid number")

    def view_current_settings(self):
        """Display current configuration"""
        print("\n" + "-" * 60)
        print("CURRENT SETTINGS")
        print("-" * 60)

        settings = [
            ('Wake Word', 'wake_word.phrase'),
            ('Wake Timeout', 'wake_word.timeout'),
            ('VAD Threshold', 'whisper.vad.threshold'),
            ('No Speech Threshold', 'whisper.vad.no_speech_threshold'),
            ('Min Speech Duration', 'whisper.vad.min_speech_duration_ms'),
            ('Speech Padding', 'whisper.vad.speech_pad_ms'),
            ('Min Silence Duration', 'whisper.vad.min_silence_duration_ms'),
            ('Beam Size', 'whisper.transcription.beam_size'),
        ]

        for label, key in settings:
            value = self.get_value(key, 'N/A')
            print(f"{label:25s}: {value}")

        input("\nPress Enter to continue...")


def main():
    """Main entry point"""
    print("=" * 60)
    print("VOICE ASSISTANT - QUICK CONFIGURATION TUNER")
    print("=" * 60)
    print("\nThis tool helps you adjust settings for your environment.")
    print("All changes are saved to config.yaml")

    tuner = QuickTune()

    try:
        tuner.interactive_menu()
    except KeyboardInterrupt:
        print("\n\nInterrupted by user")
        save = input("Save changes before exiting? (y/n): ").strip().lower()
        if save == 'y':
            tuner.save_config()
    except Exception as e:
        print(f"\nError: {e}")
        import traceback
        traceback.print_exc()
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())