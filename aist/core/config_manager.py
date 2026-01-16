# aist/core/config_manager.py
import yaml
import logging
import os
from typing import Any

log = logging.getLogger(__name__)

class ConfigManager:
    """
    A singleton class to manage loading and accessing configuration from config.yaml.
    It provides a simple way to get configuration values from anywhere in the application.
    """
    _instance = None
    _config = {}

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(ConfigManager, cls).__new__(cls)
            cls._instance._load_config()
        return cls._instance

    def _load_config(self):
        """Loads configuration from config.yaml."""
        config_path = 'config.yaml'
        if not os.path.exists(config_path):
            log.info(f"Attempting to load configuration from '{os.path.abspath(config_path)}'.")
            log.fatal(f"Configuration file '{config_path}' not found.")
            log.fatal("Please copy 'config.template.yaml' to 'config.yaml' and customize it.")
            # Proceed with an empty config, which will cause controlled failures downstream.
            self._config = {}
            return

        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                self._config = yaml.safe_load(f)
                log.info(f"Successfully loaded configuration from '{config_path}'.")
        except yaml.YAMLError as e:
            log.fatal(f"Error parsing YAML file '{config_path}': {e}")
            self._config = {}

    def get(self, key: str, default: Any = None) -> Any:
        """
        Retrieves a configuration value using a dot-separated key.
        Example: get('models.llm.path')
        """
        keys = key.split('.')
        value = self._config
        for k in keys:
            if not isinstance(value, dict) or k not in value:
                log.warning(f"Config key '{key}' not found. Using default value: {default}")
                return default
            value = value[k]
        return value

# Create a single, globally accessible instance of the config manager.
# Other modules can simply `from aist.core.config_manager import config`
config = ConfigManager()