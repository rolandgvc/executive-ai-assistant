import yaml
from pathlib import Path

_ROOT = Path(__file__).absolute().parent
_DEFAULT_CONFIG = yaml.safe_load(_ROOT.joinpath("config.yaml").read_text())


def get_config(config: dict):
    # This loads things either ALL from configurable, or
    # all from the config.yaml
    # This is done intentionally to enforce an "all or nothing" configuration
    if "email" in config["configurable"]:
        return config["configurable"]
    else:
        return _DEFAULT_CONFIG
