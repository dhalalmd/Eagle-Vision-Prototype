import importlib
import pkgutil
from pathlib import Path
from typing import Dict, List, Type, Optional
from shared.logger import logger
from shared.config import load_config
from modules.base import BaseModule

class ModuleRegistry:
    def __init__(self, config_path: str = "config.yaml"):
        self.config_path = config_path
        self.modules: Dict[str, BaseModule] = {}
        self.failures: Dict[str, int] = {}
        self.status: Dict[str, str] = {} # "active", "disabled", "failed"
        self.load_modules()

    def discover_modules() -> Dict[str, Type[BaseModule]]:
        discovered = {}
        modules_dir = Path("modules")
        if not modules_dir.exists():
            return discovered

        for item in modules_dir.iterdir():
            if item.is_dir() and (item / "module.py").exists():
                mod_name = item.name
                try:
                    module_path = f"modules.{mod_name}.module"
                    imported = importlib.import_module(module_path)
                    mod_cls = getattr(imported, "Module", None)
                    if mod_cls and issubclass(mod_cls, BaseModule):
                        discovered[mod_name] = mod_cls
                except Exception as e:
                    logger.error(f"Error discovering module {mod_name}: {e}")
        return discovered

    def load_modules(self):
        cfg = load_config(self.config_path)
        mod_configs = cfg.get("modules", {})
        discovered = ModuleRegistry.discover_modules()

        loaded: Dict[str, BaseModule] = {}
        for mod_name, mod_cls in discovered.items():
            m_cfg = mod_configs.get(mod_name, {})
            is_enabled = m_cfg.get("enabled", False)
            if is_enabled:
                try:
                    instance = mod_cls(m_cfg)
                    instance.setup()
                    loaded[mod_name] = instance
                    self.status[mod_name] = "active"
                    self.failures[mod_name] = 0
                    logger.info(f"Loaded module: {mod_name}")
                except Exception as e:
                    logger.error(f"Failed to setup module {mod_name}: {e}")
                    self.status[mod_name] = "failed"
                    self.failures[mod_name] = 5
            else:
                self.status[mod_name] = "disabled"

        # Sort loaded modules by `order`
        sorted_modules = dict(sorted(loaded.items(), key=lambda item: item[1].order))
        self.modules = sorted_modules

    def get_active_modules(self) -> List[BaseModule]:
        return list(self.modules.values())

    def record_failure(self, name: str):
        self.failures[name] = self.failures.get(name, 0) + 1
        if self.failures[name] >= 5:
            logger.error(f"Module {name} failed 5 consecutive times. Disabling...")
            self.status[name] = "failed"
            if name in self.modules:
                try:
                    self.modules[name].teardown()
                except Exception:
                    pass
                del self.modules[name]

    def record_success(self, name: str):
        self.failures[name] = 0

    def list_modules_info(self) -> List[dict]:
        cfg = load_config(self.config_path)
        mod_configs = cfg.get("modules", {})
        discovered = ModuleRegistry.discover_modules()
        all_names = set(discovered.keys()) | set(mod_configs.keys())
        
        info_list = []
        for name in sorted(all_names):
            m_cfg = mod_configs.get(name, {})
            enabled = m_cfg.get("enabled", False)
            stat = self.status.get(name, "disabled" if not enabled else "active")
            fails = self.failures.get(name, 0)
            info_list.append({
                "name": name,
                "enabled": enabled,
                "status": stat,
                "failures": fails
            })
        return info_list
