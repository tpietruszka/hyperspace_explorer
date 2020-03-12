from hyperspace_explorer.utils import *


def test_flatten():
    n1 = {"a1": 123, "a2": {"b1": 234, "b2": 345}}
    f1 = {"a1": 123, "a2.b1": 234, "a2.b2": 345}
    assert flatten(n1) == f1


def test_unique_suffixes():
    full = ["a", "b.A", "b.B", "c.A"]
    short = {
        "a": "a",
        "b.A": "b.A",
        "c.A": "c.A",
        "b.B": "B",
    }
    assert unique_suffixes(full) == short

    # collision after shortening - cannot shorten b.B
    full = ["B", "b.A", "b.B", "c.A", "c.A.1"]
    short = {
        "B": "B",
        "b.B": "b.B",
        "b.A": "b.A",
        "c.A": "c.A",
        "c.A.1": "1",
    }
    assert unique_suffixes(full) == short


def test_drop_constant_columns():
    df = pd.DataFrame(
        {
            "A": [1, 2, 3, 4],
            "B": [1, 1, 1, 1],
            "C": [(), (), (), ()],
            "D": [(), (), (10,), (10,)],
            "E": [1, 1, None, None],
        }
    )
    r = drop_constant_columns(df)
    assert set(r.columns) == {"A", "D", "E"}
