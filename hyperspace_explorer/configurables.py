from abc import ABCMeta, abstractmethod, ABC
from typing import *
from copy import copy, deepcopy
import dataclasses

factories = {}
CLASS_NAME_FIELD = 'className'


class RegisteredAbstractMeta(ABCMeta):
    """
    A class created by this metaclass and with `is_registry=True` will have a mapping of (name -> class) to all its
    subclasses in the `subclass_registry` class variable. Allows marking methods as abstract, as ABCMeta.

    Example:
    >>> class A(metaclass=RegisteredAbstractMeta, is_registry=True):
    ...     pass
    >>> class B(A):
    ...     def __init__(self, num):
    ...         self.num = num
    ...     def greet(self):
    ...         print(f'B-greet-{self.num}')
    >>> b_instance = A.factory('B', {'num':3})
    >>> b_instance.greet()
    B-greet-3
    """

    def __new__(mcs, name, bases, class_dct, **kwargs):
        x = super().__new__(mcs, name, bases, class_dct)
        if kwargs.get('is_registry', False):
            x.subclass_registry = {}
            x.factory = lambda cname, params: x.subclass_registry[cname](**params)
            if name in factories.keys():
                raise RuntimeError(f"Factory-class {name} defined more than once!")
            else:
                factories[name] = x
        else:
            x.subclass_registry[name] = x
        return x


class Configurable(ABC):
    """
    Base class for classes created with metaclass=RegisteredAbstractMeta
    Ensures that mappings of default values are provided in a consistent way and enables easy construction from
    a partial config
    """


    @classmethod
    @abstractmethod
    def get_default_config(cls) -> Dict:
        pass

    @classmethod
    @abstractmethod
    def factory(cls, cname, params) -> 'Configurable':
        pass

    @classmethod
    def from_config(cls, params) -> 'Configurable':
        params = deepcopy(params)
        cname = params[CLASS_NAME_FIELD]
        del params[CLASS_NAME_FIELD]

        full = cls.subclass_registry[cname].get_default_config()
        full.update(params)
        return cls.factory(cname, full)


@dataclasses.dataclass
class ConfigurableDataclass(Configurable):
    @classmethod
    def get_default_config(cls) -> Dict:
        res = {}
        for f in dataclasses.fields(cls):
            if not isinstance(f.default, dataclasses._MISSING_TYPE):
                res[f.name] = f.default
            if not isinstance(f.default_factory, dataclasses._MISSING_TYPE):
                res[f.name] = f.default_factory()
        return res


def fill_in_defaults(params: Dict, factory_name: Optional[str] = None) -> Dict:
    """
    Given a config dictionary, return a copy with filled in defaults.
    Recursive; if passing a full config (without `className` at top level,
    do not pass `factory_name`.
    """
    params = params.copy()
    if CLASS_NAME_FIELD in params.keys():
        cn = params[CLASS_NAME_FIELD]
        defaults = factories[factory_name].subclass_registry[cn].get_default_config()
        for k, v in defaults.items():
            if k not in params.keys():
                params[k] = v
                print(f'Setting {k}={v}')
    for k, v in params.items():
        if isinstance(v, Dict) and CLASS_NAME_FIELD in v.keys():
            params[k] = fill_in_defaults(v, k)
        # TODO: should we handle lists of Configurables? for now ignoring lists altogether
    return params
