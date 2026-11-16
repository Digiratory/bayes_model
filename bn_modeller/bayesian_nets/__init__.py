def __getattr__(name):
    # correlations imports pingouin (which pulls matplotlib), so it is kept
    # lazy: importing lightweight submodules like feature_metrics must not
    # drag the whole scientific stack in.
    if name in ("CorrMatrix", "PartCorrMatrix"):
        from . import correlations

        return getattr(correlations, name)
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
