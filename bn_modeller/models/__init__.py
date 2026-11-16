from .checkable_sort_filter_proxy_model import CheckableSortFilterProxyModel
from .dependency_sqltable_model import (
    CorrelationSQLProxyModel,
    DependencyManyToManySqlTableModel,
    FilterPairTableSQLProxyModel,
    PairTableSQLProxyModel,
)
from .feature_selection_model import (
    FeatureSelectionTableModel,
    InputFeaturesProxyModel,
    OutputFeaturesProxyModel,
)
from .relational_sort_filter_proxy_model import RelationalSortFilterProxyModel
from .sample_sqltable_model import SampleSqlTableModel


def __getattr__(name):
    # PairTableStyledProxyModel is loaded lazily so that importing the data
    # layer (e.g. PairTableSQLProxyModel for headless use) does not pull the
    # styling stack (matplotlib, SettingsService) through this package (#34).
    if name == "PairTableStyledProxyModel":
        from .pair_table_styled_proxy_model import PairTableStyledProxyModel

        return PairTableStyledProxyModel
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
