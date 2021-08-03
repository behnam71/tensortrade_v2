import importlib

if importlib.util.find_spec("talib") is not None:
    from .talib_indicator import TAlibIndicator
