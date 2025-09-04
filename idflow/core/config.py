#!/usr/bin/env python3
"""
Configuration management for idflow.
Loads settings from config/idflow.yml and environment variables.
"""

import os
from pathlib import Path
from typing import Optional
import yaml


class Config:
    """Configuration manager for idflow."""

    def __init__(self):
        self._config = {}
        self._load_config()

    def _load_config(self):
        """Load configuration from file and environment variables."""
        # Default configuration
        self._config = {
            "base_dir": "data",
            "config_dir": "config",
            "document_implementation": "fs_markdown",
            "conductor": {
                "server_url": "http://localhost:8080",
                "api_key_env_var": "CONDUCTOR_API_KEY"
            }
        }

        # Try to load from config file (either default or from IDFLOW_CONFIG env var)
        config_file = self._find_config_file()
        if config_file and config_file.exists():
            try:
                with open(config_file, 'r', encoding='utf-8') as f:
                    file_config = yaml.safe_load(f) or {}
                    self._config.update(file_config)
            except Exception as e:
                # Log warning but continue with defaults
                pass

        # Environment variable overrides (only for config file path, not direct values)
        # IDFLOW_CONFIG points to a specific config file
        if os.getenv("IDFLOW_CONFIG"):
            config_path = Path(os.getenv("IDFLOW_CONFIG"))
            if config_path.exists():
                try:
                    with open(config_path, 'r', encoding='utf-8') as f:
                        env_config = yaml.safe_load(f) or {}
                        self._config.update(env_config)
                except Exception as e:
                    # Log warning but continue with current config
                    pass

        # Direct environment variable overrides for testing
        if os.getenv("IDFLOW_BASE_DIR"):
            self._config["base_dir"] = os.getenv("IDFLOW_BASE_DIR")
        if os.getenv("IDFLOW_CONFIG_DIR"):
            self._config["config_dir"] = os.getenv("IDFLOW_CONFIG_DIR")
        if os.getenv("IDFLOW_DOCUMENT_IMPL"):
            self._config["document_implementation"] = os.getenv("IDFLOW_DOCUMENT_IMPL")

    def reload(self):
        """Reload configuration from files and environment variables."""
        self._load_config()

    def _find_config_file(self) -> Optional[Path]:
        """Find the configuration file by looking in current directory and parents."""
        # First check if IDFLOW_CONFIG is set
        if os.getenv("IDFLOW_CONFIG"):
            config_path = Path(os.getenv("IDFLOW_CONFIG"))
            if config_path.exists():
                return config_path

        # Otherwise look for config/idflow.yml in current directory and parents
        current = Path.cwd()

        while current != current.parent:
            config_file = current / "config" / "idflow.yml"
            if config_file.exists():
                return config_file
            current = current.parent

        return None

    @property
    def base_dir(self) -> Path:
        """Get the base directory for documents."""
        return Path(self._config["base_dir"])

    @property
    def config_dir(self) -> Path:
        """Get the configuration directory."""
        return Path(self._config["config_dir"])

    @property
    def document_implementation(self) -> str:
        """Get the document implementation to use."""
        return self._config["document_implementation"]

    @property
    def conductor_server_url(self) -> str:
        """Get the Conductor server URL."""
        return self._config.get("conductor", {}).get("server_url")

    @property
    def conductor_api_key_env_var(self) -> str:
        """Get the environment variable name for the Conductor API key."""
        return self._config.get("conductor", {}).get("api_key_env_var")

    def get(self, key: str, default=None):
        """Get a configuration value."""
        return self._config.get(key, default)


# Global configuration instance
config = Config()
