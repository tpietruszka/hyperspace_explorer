from typing import *
import collections as cc
import functools

try:
    import pandas as pd
except ModuleNotFoundError:
    pd = None


def flatten(nested: Dict) -> Dict:
    """
    For a structure of nested dicts (and other values in them),
    return a flat dictionary, with inner dict keys prefixed with outer ones.

    :param nested: dictionary to transform
    :return: flat dictionary
    """
    flat = {}
    for k, v in nested.items():
        if isinstance(v, Dict):
            for inner_k, inner_v in flatten(v).items():
                full_key = ".".join([k, inner_k])
                flat[full_key] = inner_v
        else:
            flat[k] = v
    return flat


def unique_suffixes(keys: List[str], sep: str = ".") -> Dict[str, str]:
    """
    For a list of hierarchical, usually dot-separated keys,
    return their mapping to shortest possible suffixes that will be unique.

    Used e.g. on table headers to improve readability.

    :param keys: list of hierarchical keys
    :param sep: separator character
    :return: dictionary mapping original keys to shortened ones
    """
    mapping = {k: k.split(sep)[-1] for k in keys}
    parts_counts = {k: 1 for k in mapping.keys()}
    suf_counter = cc.Counter(mapping.values())
    while set(suf_counter.values()) != {1}:
        duplicated = {k for k, v in suf_counter.items() if v > 1}
        for k, v in mapping.items():
            if v in duplicated:
                parts_counts[k] += 1
                mapping[k] = sep.join(k.split(sep)[-parts_counts[k] :])
        suf_counter = cc.Counter(mapping.values())
    return mapping


def requires_analysis_extra(func):
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        if pd is None:
            raise ModuleNotFoundError(
                "Pandas module missing. Install it, or install "
                "hyperspace_explorer[analysis] extra dependency"
            )
        return func(*args, **kwargs)

    return wrapper


@requires_analysis_extra
def drop_constant_columns(df: "pd.DataFrame") -> "pd.DataFrame":
    to_keep = [c for c in df.columns if df[c].nunique(dropna=False) > 1]
    return df[to_keep]


@requires_analysis_extra
def lists_to_tuples(df: "pd.DataFrame") -> "pd.DataFrame":
    return df.applymap(lambda x: x if not isinstance(x, list) else tuple(x))
