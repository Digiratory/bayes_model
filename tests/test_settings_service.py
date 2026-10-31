"""Tests for bn_modeller.utils.settings_service.SettingsService."""

import pytest
from PySide6.QtCore import QCoreApplication, QSettings, Qt
from PySide6.QtWidgets import QTreeView

from bn_modeller.utils import settings_service as settings_service_module
from bn_modeller.utils.settings_service import (
    SettingDefinition,
    SettingsService,
    register_setting,
)


@pytest.fixture
def service(qtbot, tmp_path):
    """Singleton service bound to an INI file inside tmp_path.

    setDefaultFormat/setPath are process-global, so every test must go through
    this fixture: it redirects QSettings to a per-test directory before the
    singleton is (re)created and drops the stale singleton afterwards so the
    next test cannot reuse settings bound to an old tmp_path.
    """
    QSettings.setDefaultFormat(QSettings.Format.IniFormat)
    QSettings.setPath(
        QSettings.Format.IniFormat, QSettings.Scope.UserScope, str(tmp_path)
    )
    QCoreApplication.setOrganizationName("Digiratory")
    QCoreApplication.setApplicationName("bn_modeller_tests")
    SettingsService.reset_for_testing()
    instance = SettingsService.instance()
    yield instance
    SettingsService.reset_for_testing()


def test_set_get_roundtrip(service, qtbot):
    """set_value stores a value and emits settingChanged with it."""
    with qtbot.waitSignal(service.settingChanged) as blocker:
        assert service.set_value("depTable/colormap", "viridis") is True
    assert blocker.args == ["depTable/colormap", "viridis"]
    assert service.get_value("depTable/colormap", value_type=str) == "viridis"


def test_get_value_nested_group(service):
    """Keys with several group levels round-trip through nested storage."""
    assert service.set_value("UI/windows/last_project_path", "C:/projects/a.sqlite")
    assert (
        service.get_value("UI/windows/last_project_path", value_type=str)
        == "C:/projects/a.sqlite"
    )


def test_get_value_default_fallback(service):
    """Unregistered missing keys fall back to the caller default (or None)."""
    assert service.get_value("missing/key") is None
    assert service.get_value("missing/key", "fallback") == "fallback"


def test_get_value_registered_default(service):
    """A registered key returns its registry default when absent."""
    assert service.get_value("depTable/colormap") == "coolwarm"


def test_get_value_type_coercion(service):
    """value_type coerces the value stored by the settings backend."""
    assert service.set_value("test/someFloat", 0.75)
    value = service.get_value("test/someFloat", value_type=float)
    assert isinstance(value, float)
    assert value == pytest.approx(0.75)


def test_contains(service):
    """contains reflects storage state of a key."""
    assert not service.contains("UI/windows/last_project_path")
    service.set_value("UI/windows/last_project_path", "x")
    assert service.contains("UI/windows/last_project_path")


def test_remove(service, qtbot):
    """remove deletes the key and emits the post-removal effective value."""
    service.set_value("depTable/colormap", "viridis")
    with qtbot.waitSignal(service.settingChanged) as blocker:
        assert service.remove("depTable/colormap") is True
    assert blocker.args == ["depTable/colormap", "coolwarm"]
    assert not service.contains("depTable/colormap")
    assert service.get_value("depTable/colormap", value_type=str) == "coolwarm"
    assert service.remove("depTable/colormap") is False


def test_sync(service):
    """sync flushes pending changes and reports success."""
    service.set_value("depTable/colormap", "viridis")
    assert service.sync() is True


def test_reset_to_defaults(service):
    """reset_to_defaults removes registered keys; unregistered keys survive."""
    service.set_value("depTable/colormap", "viridis")
    service.set_value("unregistered/custom", "keepme")
    service.reset_to_defaults()
    assert not service.contains("depTable/colormap")
    assert service.get_value("depTable/colormap", value_type=str) == "coolwarm"
    assert service.contains("unregistered/custom")
    assert service.get_value("unregistered/custom", value_type=str) == "keepme"


def test_reset_to_defaults_group_scoped(service):
    """reset_to_defaults with a group only clears that group's keys."""
    service.set_value("projectLoadWizard/lastProjectLocation", "a.sqlite")
    service.set_value("DataImportPage/lastSourceLocationDir", "C:/data")
    service.reset_to_defaults("projectLoadWizard")
    assert not service.contains("projectLoadWizard/lastProjectLocation")
    assert service.contains("DataImportPage/lastSourceLocationDir")


def test_settings_reset_signal(service, qtbot):
    """reset_to_defaults emits settingsReset."""
    with qtbot.waitSignal(service.settingsReset):
        service.reset_to_defaults()


def test_hierarchy_changed_on_new_key(service, qtbot):
    """Writing a key that is new to the tree emits hierarchyChanged."""
    with qtbot.waitSignal(service.hierarchyChanged) as blocker:
        service.set_value("UI/windows/last_project_path", "x")
    assert blocker.args == ["UI/windows"]


def test_no_setting_changed_on_identical_write(service):
    """Writing an identical stored value emits no settingChanged."""
    service.set_value("depTable/colormap", "viridis")
    received = []
    service.settingChanged.connect(lambda key, value: received.append((key, value)))
    assert service.set_value("depTable/colormap", "viridis") is True
    assert received == []


def test_persistence_across_singleton_reset(service):
    """Values survive reset_for_testing() plus a fresh instance()."""
    service.set_value("depTable/colormap", "viridis")
    SettingsService.reset_for_testing()
    fresh = SettingsService.instance()
    assert fresh is not service
    assert fresh.get_value("depTable/colormap", value_type=str) == "viridis"


def test_register_setting_extension(service, qtbot):
    """register_setting adds a key (with its default) and notifies the tree."""
    saved = dict(settings_service_module._registered_settings)
    try:
        definition = SettingDefinition(
            "custom/group/option", default="base", value_type=str
        )
        with qtbot.waitSignal(service.hierarchyChanged) as blocker:
            register_setting(definition)
        assert blocker.args == ["custom/group"]
        assert service.get_value("custom/group/option") == "base"
        assert service.contains("custom/group/option") is False
    finally:
        settings_service_module._registered_settings.clear()
        settings_service_module._registered_settings.update(saved)


def test_validator_rejection(service, qtbot):
    """A validator rejection refuses the write and stores nothing."""
    saved = dict(settings_service_module._registered_settings)
    try:
        definition = SettingDefinition(
            "custom/validated", value_type=int, validator=lambda v: v >= 0
        )
        with qtbot.waitSignal(service.hierarchyChanged):
            register_setting(definition)
        assert service.set_value("custom/validated", -1) is False
        assert not service.contains("custom/validated")
        assert service.get_value("custom/validated") is None
        with qtbot.waitSignal(service.settingChanged):
            assert service.set_value("custom/validated", 5) is True
        assert service.get_value("custom/validated", value_type=int) == 5
    finally:
        settings_service_module._registered_settings.clear()
        settings_service_module._registered_settings.update(saved)


def _find_index(service, name, parent=None):
    model = service
    if parent is None:
        parent = model.index(-1, -1)
    for row in range(model.rowCount(parent)):
        candidate = model.index(row, 0, parent)
        if candidate.data() == name:
            return candidate
    raise AssertionError(f"node {name!r} not found")


def test_model_tree_structure(service):
    """The model exposes a nested tree of groups and key leaves."""
    service.set_value("UI/windows/last_project_path", "p.sqlite")
    assert service.columnCount() == 2
    top_names = {service.index(row, 0).data() for row in range(service.rowCount())}
    assert {"UI", "depTable", "projectLoadWizard", "DataImportPage"} <= top_names

    ui = _find_index(service, "UI")
    assert service.parent(ui).isValid() is False
    assert service.rowCount(ui) == 1

    windows = service.index(0, 0, ui)
    assert windows.data() == "windows"
    assert service.parent(windows) == ui

    value = service.index(0, 1, windows)
    assert value.data() == "p.sqlite"
    assert service.parent(value) == windows
    assert service.rowCount(windows) == 1
    leaf = service.index(0, 0, windows)
    assert leaf.data() == "last_project_path"
    assert service.rowCount(leaf) == 0
    assert service.data(windows, Qt.ItemDataRole.DisplayRole) == "windows"
    assert service.data(ui, Qt.ItemDataRole.ToolTipRole) == "UI"
    assert (
        service.data(value, Qt.ItemDataRole.ToolTipRole)
        == "UI/windows/last_project_path = p.sqlite"
    )


def test_model_data_change_on_set(service, qtbot):
    """A value write through set_value updates the model value cell."""
    service.set_value("UI/windows/last_project_path", "old.sqlite")
    ui = _find_index(service, "UI")
    windows = service.index(0, 0, ui)
    value = service.index(0, 1, windows)
    assert value.data() == "old.sqlite"
    with qtbot.waitSignal(service.dataChanged):
        service.set_value("UI/windows/last_project_path", "new.sqlite")
    assert service.data(value) == "new.sqlite"


def test_model_set_data_routes_through_set_value(service, qtbot):
    """setData on a leaf value cell writes via set_value."""
    value_index = None
    for row in range(service.rowCount()):
        group = service.index(row, 0)
        if group.data() == "depTable":
            value_index = service.index(0, 1, group)
    assert value_index is not None
    with qtbot.waitSignal(service.settingChanged) as blocker:
        assert service.setData(value_index, "viridis", Qt.ItemDataRole.EditRole) is True
    assert blocker.args == ["depTable/colormap", "viridis"]
    assert service.get_value("depTable/colormap", value_type=str) == "viridis"
    assert service.data(value_index) == "viridis"


def test_model_flags_editable_value_cell(service):
    """Leaf value cells are editable; group nodes are not."""
    dep_table = None
    for row in range(service.rowCount()):
        group = service.index(row, 0)
        if group.data() == "depTable":
            dep_table = group
    value = service.index(0, 1, dep_table)
    assert service.flags(value) & Qt.ItemFlag.ItemIsEditable
    assert not service.flags(dep_table) & Qt.ItemFlag.ItemIsEditable


def test_model_tree_view_smoke(service, qtbot):
    """A QTreeView can display the service model."""
    service.set_value("UI/windows/last_project_path", "p.sqlite")
    view = QTreeView()
    qtbot.addWidget(view)
    view.setModel(service)
    view.expandAll()
    assert view.model() is service
