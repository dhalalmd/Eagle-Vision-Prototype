from abc import ABC, abstractmethod
from shared.schemas import FrameContext

class BaseModule(ABC):
    name: str = ""                       # == folder name == config key
    stage: str = ""                      # "pre" | "ana" | "out"
    order: int = 0
    requires: tuple[str, ...] = ()       # names of modules that must be enabled

    def __init__(self, cfg: dict):
        self.cfg = cfg                   # this module's block from config.yaml

    def setup(self) -> None:             # heavy imports + model loading go HERE
        pass

    @abstractmethod
    def process(self, ctx: FrameContext) -> None:   # mutate ctx in place, return None
        ...

    def teardown(self) -> None:
        pass
