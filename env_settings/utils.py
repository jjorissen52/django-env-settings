import os

from types import SimpleNamespace


def string_to_bool(param):
    if not isinstance(param, str):
        return param
    if param.upper() in ["1", "TRUE", "T", "Y", "YES"]:
        return True
    elif param.upper() in ["0", "FALSE", "F", "N", "NO"]:
        return False
    else:
        return param


def string_to_list(param): return param if not isinstance(param, str) else [_.strip() for _ in param.split(',')]


def get_runtime_parameters(defaults):
    cleaned = {
        key: string_to_bool(os.environ.get(key, default)) if isinstance(default, str) else string_to_list(os.environ.get(key, default)) for key, default in defaults.items()
    }
    parameters = SimpleNamespace(**cleaned)
    return parameters
