def __getattr__(name):
    # Lazy loading of the heavy subpackages.
    if name in ("CorrMatrix", "PartCorrMatrix"):
        from . import correlations

        return getattr(correlations, name)
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
