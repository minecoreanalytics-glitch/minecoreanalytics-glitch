"""
Configuration loader for Morpheus platform.
Loads and validates YAML configuration files.
"""

import yaml
from pathlib import Path
from typing import Optional
from .schemas import MorpheusConfig


class ConfigLoader:
    """Loads and manages Morpheus configuration."""

    _config: Optional[MorpheusConfig] = None
    _config_path: Optional[Path] = None

    @classmethod
    def load(cls, config_path: str = None) -> MorpheusConfig:
        """
        Load configuration from YAML file.

        Args:
            config_path: Path to YAML config file. If None, loads default htv_config.yaml

        Returns:
            MorpheusConfig instance

        Raises:
            FileNotFoundError: If config file doesn't exist
            yaml.YAMLError: If YAML is invalid
            ValueError: If config validation fails
        """
        if config_path is None:
            # Default to htv_config.yaml in the same directory
            config_path = Path(__file__).parent / "htv_config.yaml"
        else:
            config_path = Path(config_path)

        if not config_path.exists():
            raise FileNotFoundError(f"Config file not found: {config_path}")

        # Load YAML
        with open(config_path, 'r') as f:
            raw_config = yaml.safe_load(f)

        # Validate with Pydantic
        config = MorpheusConfig(**raw_config)

        # Cache the loaded config
        cls._config = config
        cls._config_path = config_path

        return config

    @classmethod
    def get_config(cls) -> MorpheusConfig:
        """
        Get the currently loaded configuration.
        If no config is loaded, loads the default configuration.

        Returns:
            MorpheusConfig instance
        """
        if cls._config is None:
            cls.load()
        return cls._config

    @classmethod
    def reload(cls) -> MorpheusConfig:
        """
        Reload configuration from the last loaded path.

        Returns:
            MorpheusConfig instance
        """
        if cls._config_path is None:
            return cls.load()
        return cls.load(str(cls._config_path))


# Convenience function for quick access
def get_config() -> MorpheusConfig:
    """Get the current Morpheus configuration."""
    return ConfigLoader.get_config()
