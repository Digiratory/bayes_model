"""Tests for bn_modeller.models.pair_table_styled_proxy_model."""

import inspect

import matplotlib as mpl
import pandas as pd
import pytest
from PySide6.QtCore import QCoreApplication, QSettings, Qt
from PySide6.QtGui import QBrush, QColor
from PySide6.QtSql import QSqlDatabase

import bn_modeller.models.dependency_sqltable_model as dependency_sqltable_module
from bn_modeller.models import (
    DependencyManyToManySqlTableModel,
    PairTableSQLProxyModel,
    PairTableStyledProxyModel,
)
from bn_modeller.models.feature_sqltable_model import FeatureSqlTableModel
from bn_modeller.utils.db_model_handler import (
    create_project_schema,
    import_dataframe_to_db,
)
from bn_modeller.utils.settings_service import SettingsService


@pytest.fixture
def settings(qtbot, tmp_path):
    """Redirect QSettings to an INI file inside tmp_path.

    setDefaultFormat/setPath are process-global, so the redirect must happen
    before the singleton (and any styled model reading the colormap setting)
    is created; the stale singleton is dropped afterwards so the next test
    cannot reuse settings bound to an old tmp_path.
    """
    QSettings.setDefaultFormat(QSettings.Format.IniFormat)
    QSettings.setPath(
        QSettings.Format.IniFormat, QSettings.Scope.UserScope, str(tmp_path)
    )
    QCoreApplication.setOrganizationName("Digiratory")
    QCoreApplication.setApplicationName("bn_modeller_tests")
    SettingsService.reset_for_testing()
    yield
    SettingsService.reset_for_testing()


@pytest.fixture
def project_db(settings, qtbot, tmp_path):
    """Project database on the default Qt connection.

    FeatureSqlTableModel/DependencyManyToManySqlTableModel execute their
    CREATE TABLE statements on the default connection, so the fixture must
    register the sqlite connection without a connection name. Data has
    corr(A, B) = +1 and corr(A, C) = -1 (A = [1..4], B = 2*A, C = -A).
    """
    db = QSqlDatabase.addDatabase("QSQLITE")
    db.setDatabaseName(str(tmp_path / "project.sqlite"))
    assert db.open()
    create_project_schema(db)
    import_dataframe_to_db(
        db,
        pd.DataFrame(
            {
                "A": [1.0, 2.0, 3.0, 4.0],
                "B": [2.0, 4.0, 6.0, 8.0],
                "C": [-1.0, -2.0, -3.0, -4.0],
            },
            index=pd.Index(range(4), dtype=int),
        ),
    )
    # Creates the feature_dependency (pairs) table like _init_db does.
    DependencyManyToManySqlTableModel(db=db)
    yield db
    connection_name = db.connectionName()
    db.close()
    del db
    QSqlDatabase.removeDatabase(connection_name)


@pytest.fixture
def pair_model(project_db):
    """Pair correlation model over an in-memory-cached feature model."""
    feature_model = FeatureSqlTableModel(db=project_db)
    feature_model.select()
    while feature_model.canFetchMore():
        feature_model.fetchMore()
    return PairTableSQLProxyModel(feature_model, db=project_db)


def _brush_rgba(model, row: int, column: int):
    brush = model.data(model.index(row, column), Qt.ItemDataRole.BackgroundRole)
    assert isinstance(brush, QBrush)
    return brush.color().rgba()


def _colormap_rgba(name: str, position: float):
    color = mpl.colormaps[name](position, bytes=True)
    return QColor(color[0], color[1], color[2], color[3]).rgba()


def test_background_paints_correlations(settings, pair_model):
    """Off-diagonal cells are painted by correlation; diagonal stays clear."""
    styled = PairTableStyledProxyModel(pair_model)

    # The raw model no longer paints: the styling lives in the styled layer.
    assert (
        pair_model.data(pair_model.index(0, 1), Qt.ItemDataRole.BackgroundRole) is None
    )

    assert _brush_rgba(styled, 0, 1) == _colormap_rgba("coolwarm", 1.0)
    assert _brush_rgba(styled, 0, 2) == _colormap_rgba("coolwarm", 0.0)
    assert styled.data(styled.index(1, 1), Qt.ItemDataRole.BackgroundRole) is None


def test_colormap_setting_change_recolors(settings, qtbot, pair_model):
    """A depTable/colormap write emits dataChanged and repaints with it."""
    styled = PairTableStyledProxyModel(pair_model)
    assert _brush_rgba(styled, 0, 1) == _colormap_rgba("coolwarm", 1.0)

    with qtbot.waitSignal(styled.dataChanged):
        assert SettingsService.instance().set_value(
            PairTableStyledProxyModel.colormapSettingKey, "viridis"
        )

    assert _brush_rgba(styled, 0, 1) == _colormap_rgba("viridis", 1.0)
    assert _brush_rgba(styled, 0, 2) == _colormap_rgba("viridis", 0.0)
    assert _colormap_rgba("viridis", 1.0) != _colormap_rgba("coolwarm", 1.0)


def test_invalid_colormap_falls_back(settings, qtbot, pair_model):
    """An invalid stored name keeps the default colormap."""
    styled = PairTableStyledProxyModel(pair_model)

    with qtbot.waitSignal(styled.dataChanged):
        assert SettingsService.instance().set_value(
            PairTableStyledProxyModel.colormapSettingKey, "not-a-colormap"
        )

    assert _brush_rgba(styled, 0, 1) == _colormap_rgba("coolwarm", 1.0)


def test_invalid_colormap_before_construction(settings, pair_model):
    """A model constructed with an invalid stored name resolves coolwarm."""
    assert SettingsService.instance().set_value(
        PairTableStyledProxyModel.colormapSettingKey, "also-not-a-colormap"
    )

    styled = PairTableStyledProxyModel(pair_model)

    assert _brush_rgba(styled, 0, 1) == _colormap_rgba("coolwarm", 1.0)


def test_other_roles_pass_through(settings, pair_model):
    """Statistics, check state, headers and role names survive the layer."""
    styled = PairTableStyledProxyModel(pair_model)

    assert styled.data(
        styled.index(0, 1), PairTableSQLProxyModel.PearsonCorrRole
    ) == pytest.approx(1.0)
    assert styled.data(
        styled.index(0, 2), PairTableSQLProxyModel.PearsonCorrRole
    ) == pytest.approx(-1.0)

    assert (
        styled.data(styled.index(0, 1), Qt.ItemDataRole.CheckStateRole)
        == Qt.CheckState.Unchecked
    )
    assert (
        styled.headerData(0, Qt.Orientation.Horizontal, Qt.ItemDataRole.DisplayRole)
        == "A"
    )

    assert styled.getFeatureSqlTableModel() is pair_model.getFeatureSqlTableModel()
    samples = styled.getSamplesDataFrame()
    assert list(samples.columns) == ["A", "B", "C"]
    assert samples["B"].tolist() == [2.0, 4.0, 6.0, 8.0]

    role_names = styled.roleNames()
    assert bytes(role_names[Qt.ItemDataRole.BackgroundRole]) == b"background"
    assert bytes(role_names[PairTableSQLProxyModel.PearsonCorrRole]) == b"PearsonCorr"


def test_data_layer_module_has_no_styling_dependencies():
    """The data model module must not depend on matplotlib or settings."""
    source = inspect.getsource(dependency_sqltable_module)
    assert "matplotlib" not in source
    assert "settings_service" not in source
