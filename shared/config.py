from pathlib import Path
import yaml
from shared.logger import logger

def load_config(config_path: str = "config.yaml") -> dict:
    path = Path(config_path)
    if not path.exists():
        logger.warning(f"Config file {config_path} not found. Using empty defaults.")
        return {"cameras": [], "modules": {}}
    
    try:
        with open(path, "r", encoding="utf-8") as f:
            cfg = yaml.safe_load(f) or {}
            return cfg
    except Exception as e:
        logger.error(f"Error reading config file {config_path}: {e}")
        return {"cameras": [], "modules": {}}
