import os
import json
from pathlib import Path

CONFIG_FILE = "app_config.json"
DEFAULT_SNIPPETS_DIR = str(Path.home() / "snippets")

DEFAULT_CONFIG = {
    "snippets_dir": DEFAULT_SNIPPETS_DIR,
    "per_page": 6
}

def load_config():
    if not os.path.exists(CONFIG_FILE):
        return DEFAULT_CONFIG
    try:
        with open(CONFIG_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return DEFAULT_CONFIG

def save_config(config):
    with open(CONFIG_FILE, "w", encoding="utf-8") as f:
        json.dump(config, f, indent=4)

def init_dir(directory):
    try:
        os.makedirs(directory, exist_ok=True)
    except Exception:
        pass
