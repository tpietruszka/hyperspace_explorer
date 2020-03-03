"""
Toy problem to explore possible options regarding default values, compositions, etc

In typical usage, we would have factory classes such as:
- Dataset, and children: DatasetA, DatasetB, ...
- Model, and children perhaps like RNNClassifier, CNNClassifier - each of them might directly
  implement methods such as .fit() and .predict(), or return 3rd party library objects that do,
  For more complex architectures, nested configurations might be useful.

Dataclasses are very convenient to avoid writing constructors, mostly useful for "thin" classes
that do not have much logic, but just construct objects from 3rd party libraries - or just
store configuration for any other reason.

Warning: in dataclasses, do not add default values to fields of parent classes - or their
children will be required to only have default-value fields. This is a limitation of dataclasses
themselves.
"""
from dataclasses import dataclass
from abc import abstractmethod
from typing import *
from hyperspace_explorer.configurables import Configurable, ConfigurableDataclass, RegisteredAbstractMeta, factories, \
    fill_in_defaults, update_config


class Vehicle(Configurable, metaclass=RegisteredAbstractMeta, is_registry=True):
    @abstractmethod
    def get_mpge(self) -> float:
        pass


class Car(Vehicle):
    def __init__(self, Engine: Dict, num_doors: int):
        """
        Typical Configurable, contains both parameters of simple types and other Configurables.
        For Configurable components, we can create instances right away, or when needed
        (see Truck.get_mpge).

        No default values in init! put them in get_default_config, not all have to be specified.
         """
        self.engine = factories['Engine'].from_config(Engine)
        self.num_doors = num_doors

    @classmethod
    def get_default_config(cls) -> Dict:
        return {
            'num_doors': 4
        }

    def get_mpge(self) -> float:
        return self.engine.get_efficiency() * 100


class Truck(Vehicle):
    def __init__(self, Engine: Dict, Trailer: Dict):
        """
        By convention, like in dataclasses, original values are stored in fields with names
        equal to param names. Instances of configurables - the same name, but lowercase.
        """
        self.engine = factories['Engine'].from_config(Engine)
        self.Trailer = Trailer

    @classmethod
    def get_default_config(cls) -> Dict:
        return {
            'Trailer': {
                'className': 'ContainerTrailer'
            }
        }

    def get_mpge(self) -> float:
        trailer = Trailer.from_config(self.Trailer)
        base = 10 - trailer.get_drag()
        return base * self.engine.get_efficiency()


class Engine(Configurable, metaclass=RegisteredAbstractMeta, is_registry=True):
    @abstractmethod
    def get_efficiency(self) -> float:
        pass


class ElectricMotor(Engine):
    @classmethod
    def get_default_config(cls) -> Dict:
        return {}

    def get_efficiency(self) -> float:
        return .9


class CombustionEngine(Engine):
    def __init__(self, displacement_liters: float, strokes_per_cycle: int):
        self.displacement_liters = displacement_liters
        self.strokes_per_cycle = strokes_per_cycle

    @classmethod
    def get_default_config(cls) -> Dict:
        return {
            'strokes_per_cycle': 4
        }

    def get_efficiency(self) -> float:
        return self.strokes_per_cycle / 10 - self.displacement_liters / 50


@dataclass
class Trailer(ConfigurableDataclass, metaclass=RegisteredAbstractMeta, is_registry=True):
    """If no custom constructor is necessary, it is easier to use a dataclass"""
    @abstractmethod
    def get_drag(self) -> float:
        pass


@dataclass
class ContainerTrailer(Trailer):
    height: float = 3.
    length: float = 10.

    def get_drag(self) -> float:
        return self.height * self.length / 10  # nonsense as usual


car1 = {
    'className': 'Car',
    'Engine': {
        'className': 'CombustionEngine',
        'displacement_liters': 2.
    }
}
car1full = {'Vehicle': car1}

car2 = {
    'className': 'Car',
    'num_doors': 2,
    'Engine': {
        'className': 'CombustionEngine',
        'displacement_liters': 2.,
        'strokes_per_cycle': 2,
    }
}

truck1 = {
    'className': 'Truck',
    'Engine': {
        'className': 'ElectricMotor',
    },
}

truck2 = {
    'className': 'Truck',
    'Engine': {
        'className': 'ElectricMotor',
    },
    'Trailer': {
        'className': 'ContainerTrailer',
        'length': 5.
    }
}


def test_construction():
    c1 = Car.from_config(car1)
    assert c1.get_mpge() is not None
    c2 = Car.from_config(car2)
    assert c2.get_mpge() is not None
    t1 = Car.from_config(truck1)
    assert t1.get_mpge() is not None
    t2 = Car.from_config(truck2)
    assert t2.get_mpge() is not None


def test_fill_in_defaults():
    car1_filled = fill_in_defaults(car1, 'Vehicle')
    assert car1_filled['num_doors'] == 4
    assert car1_filled['Engine']['strokes_per_cycle'] == 4

    car1full_filled = fill_in_defaults(car1full)
    assert car1full_filled['Vehicle']['num_doors'] == 4
    assert car1full_filled['Vehicle']['Engine']['strokes_per_cycle'] == 4

    car2_filled = fill_in_defaults(car2, 'Vehicle')
    assert car2_filled['num_doors'] == 2
    assert car2_filled['Engine']['strokes_per_cycle'] == 2

    truck1_filled = fill_in_defaults(truck1, 'Vehicle')
    assert truck1_filled['Trailer']['height'] == 3
    assert truck1_filled['Trailer']['length'] == 10

    truck2_filled = fill_in_defaults(truck2, 'Vehicle')
    assert truck2_filled['Trailer']['height'] == 3
    assert truck2_filled['Trailer']['length'] == 5


def test_update_config():
    c1u = {'num_doors': 2, 'Engine': {'displacement_liters': 3.}}
    c1 = update_config(car1, c1u)
    assert c1['num_doors'] == 2
    assert c1['Engine']['displacement_liters'] == 3.

    c2u = {'num_doors': 2, 'Engine': {'displacement_liters': 3.}}
    c2 = update_config(car2, c2u)
    assert c2['num_doors'] == 2
    assert c2['Engine']['strokes_per_cycle'] == 2

    c2u2 = {'num_doors': 2, 'Engine': {'className': 'CombustionEngine', 'displacement_liters': 3.}}
    c22 = update_config(car2, c2u2)
    assert c22['num_doors'] == 2
    assert c22['Engine']['strokes_per_cycle'] == 2

    t1u = {'Trailer': {'className': 'ContainerTrailer', 'length': 20}}
    t1 = update_config(truck1, t1u)
    assert t1['Trailer']['className'] == 'ContainerTrailer'
    assert t1['Trailer']['length'] == 20


def test_update_config_change_class():
    c1_to_electric = {'Engine': {'className': 'ElectricMotor'}}
    c1 = update_config(car1, c1_to_electric)
    assert c1['Engine'] == {'className': 'ElectricMotor'}

    t1_to_combustion = {'Engine': {'className': 'CombustionEngine', 'displacement_liters': 1.5}}
    t1 = update_config(truck1, t1_to_combustion)
    assert t1['Engine'] == {'className': 'CombustionEngine', 'displacement_liters': 1.5}
