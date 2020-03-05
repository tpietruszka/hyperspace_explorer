import abc
from typing import *
from collections import defaultdict
from hyperspace_explorer.configurables import Configurable, RegisteredAbstractMeta


class Scenario(Configurable, metaclass=RegisteredAbstractMeta, is_registry=True):
    @abc.abstractmethod
    def single_run(self, params) -> Tuple[float, Dict, Any]:
        pass

    @classmethod
    def get_default_config(cls) -> Dict:
        return {}

    def __init__(self):
        self._run = None
        self._metrics = defaultdict(dict)
        self.info = dict()  # logged. Store all diagnostic info here

    def log_scalar(self, name: str, value: float, step: Optional[int] = None):
        """
        Store a single value of metric named `name`, at step `step` (or
        auto-increment).

        If running with sacred, use Metrics API - `log_scalar`.
        Otherwise log within the class, in `self._metrics`.
        """
        if self._run:
            self._run.log_scalar(name, value, step)
            return
        metric_dict = self._metrics[name]
        if step is None:
            if len(metric_dict.keys()) == 0:
                step = 0
            else:
                step = max(metric_dict.keys()) + 1
        metric_dict[step] = value

    def setup_sacred(self, run):
        self._run = run
        self.info = run.info
