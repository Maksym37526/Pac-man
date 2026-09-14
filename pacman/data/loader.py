from pacman.errors import ConfigError


def read_config(path: str) -> str:
    """Read the configuration file and return its contents.

    Args:
        path: Path to the configuration file."""
    try:
        with open(path, "r", encoding="utf-8") as f:
            return f.read()
    except OSError as e:
        raise ConfigError(f"Cannot read config file '{path}': {e.strerror}")
    except UnicodeDecodeError as e:
        raise ConfigError(f"Cannot decode config file '{path}': {e.reason}")
