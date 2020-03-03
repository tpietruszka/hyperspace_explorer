import abc
from typing import *
from hyperspace_explorer.configurables import Configurable, RegisteredAbstractMeta


class Scenario(Configurable, metaclass=RegisteredAbstractMeta, is_registry=True):
    @staticmethod
    @abc.abstractmethod
    def single_run(params) -> Tuple[float, Dict, Any]:
        pass

    @classmethod
    def get_default_config(cls) -> Dict:
        return {}

    def __init__(self, **kwargs):
        """
        Allows construction with extra parameters, by `.from_config()`,
        but parameters are then used in `single_run()`
        """
        pass
