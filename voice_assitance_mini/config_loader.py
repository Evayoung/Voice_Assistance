"""
Configuration loader for Voice Assistant
Handles loading and validation of configuration files
"""
import os
import yaml
import logging
from typing import Dict, Any

logger = logging.getLogger(__name__)


class Config:
    """Configuration manager with defaults"""

    DEFAULT_CONFIG = {
        'wake_word': {
            'phrase': 'hey assistant',
            'timeout': 10,
            'threshold': 0.7
        },
        'whisper': {
            'model_dir': 'whisper_model',
            'device': 'cpu',
            'compute_type': 'int8',
            'vad': {
                'enabled': True,
                'threshold': 0.5,
                'min_speech_duration_ms': 250,
                'max_speech_duration_s': 30,
                'min_silence_duration_ms': 500,
                'speech_pad_ms': 400
            },
            'transcription': {
                'language': 'en',
                'beam_size': 5,
                'best_of': 5,
                'temperature': 0.0,
                'compression_ratio_threshold': 2.4,
                'log_prob_threshold': -1.0,
                'no_speech_threshold': 0.6
            }
        },
        'piper': {
            'model_file': 'en_GB-southern_english_female-low.onnx',
            'blocking_mode': False
        },
        'audio': {
            'sample_rate': 16000,
            'chunk_duration_seconds': 3,
            'blocksize': 4096,
            'channels': 1
        },
        'logging': {
            'level': 'INFO',
            'file': 'voice_assistant.log',
            'console': True,
            'format': '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        },
        'error_recovery': {
            'max_restart_attempts': 3,
            'restart_delay_seconds': 1
        },
        'commands': {
            'joke': ['joke', 'tell me a joke', 'make me laugh'],
            'time': ['time', 'what time is it', 'date'],
            'sleep': ['sleep', 'go to sleep', 'deactivate'],
            'exit': ['exit', 'goodbye', 'stop', 'quit']
        }
    }

    def __init__(self, config_file: str = 'config.yaml'):
        """
        Initialize configuration.

        Args:
            config_file: Path to YAML config file
        """
        self.config_file = config_file
        self.config = self.DEFAULT_CONFIG.copy()

        if os.path.exists(config_file):
            self.load(config_file)
        else:
            logger.warning(f"Config file '{config_file}' not found, using defaults")
            self.save(config_file)  # Save default config for reference

    def load(self, config_file: str):
        """Load configuration from YAML file"""
        try:
            with open(config_file, 'r') as f:
                user_config = yaml.safe_load(f)

            if user_config:
                self._merge_configs(self.config, user_config)
                logger.info(f"Configuration loaded from {config_file}")
            else:
                logger.warning(f"Empty config file: {config_file}")

        except Exception as e:
            logger.error(f"Failed to load config from {config_file}: {e}")
            logger.info("Using default configuration")

    def save(self, config_file: str):
        """Save current configuration to YAML file"""
        try:
            with open(config_file, 'w') as f:
                yaml.dump(self.config, f, default_flow_style=False, sort_keys=False)
            logger.info(f"Configuration saved to {config_file}")
        except Exception as e:
            logger.error(f"Failed to save config to {config_file}: {e}")

    def _merge_configs(self, base: Dict, update: Dict):
        """Recursively merge update dict into base dict"""
        for key, value in update.items():
            if key in base and isinstance(base[key], dict) and isinstance(value, dict):
                self._merge_configs(base[key], value)
            else:
                base[key] = value

    def get(self, key_path: str, default: Any = None) -> Any:
        """
        Get configuration value using dot notation.

        Args:
            key_path: Dot-separated path (e.g., 'whisper.vad.threshold')
            default: Default value if key not found

        Returns:
            Configuration value or default
        """
        keys = key_path.split('.')
        value = self.config

        for key in keys:
            if isinstance(value, dict) and key in value:
                value = value[key]
            else:
                return default

        return value

    def set(self, key_path: str, value: Any):
        """
        Set configuration value using dot notation.

        Args:
            key_path: Dot-separated path
            value: Value to set
        """
        keys = key_path.split('.')
        config = self.config

        for key in keys[:-1]:
            if key not in config:
                config[key] = {}
            config = config[key]

        config[keys[-1]] = value

    def __getitem__(self, key: str) -> Any:
        """Allow dict-like access"""
        return self.config[key]

    def __setitem__(self, key: str, value: Any):
        """Allow dict-like setting"""
        self.config[key] = value


# Global config instance
_config = None


def get_config(config_file: str = 'config.yaml') -> Config:
    """Get global configuration instance"""
    global _config
    if _config is None:
        _config = Config(config_file)
    return _config


if __name__ == "__main__":
    # Test configuration loader
    logging.basicConfig(level=logging.INFO)

    config = get_config()

    print("\n=== Configuration Test ===\n")
    print(f"Wake word: {config.get('wake_word.phrase')}")
    print(f"VAD threshold: {config.get('whisper.vad.threshold')}")
    print(f"Sample rate: {config.get('audio.sample_rate')}")

    # Test setting values
    config.set('wake_word.phrase', 'hello computer')
    print(f"\nUpdated wake word: {config.get('wake_word.phrase')}")

    # Save config
    config.save('config_test.yaml')
    print("\nConfiguration saved to config_test.yaml")