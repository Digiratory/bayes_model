---
layout: default
title: Settings Service
parent: Developer Guide
nav_order: 1
---

# Settings Service

All application settings are accessed through `bn_modeller.utils.settings_service.SettingsService`, a singleton built on top of Qt's `QSettings`. It provides typed accessors, change-notification signals, a central key registry, and a `QAbstractItemModel` tree interface for future settings dialogs.

The service never hardcodes organization or application names: it uses a plain `QSettings()` constructor, so the names set by `create_application()` in `bn_modeller/app.py` apply and existing user data (for example under `HKCU\Software\Digiratory\bn_modeller`) keeps working.

The singleton is created early in `create_application()` (after the `QCoreApplication.set*` calls, so `QSettings` resolves the correct storage location).

## Reading a setting in a widget

Call `SettingsService.instance()` wherever you would previously have constructed a `QSettings()`:

```python
from bn_modeller.utils.settings_service import SettingsService

colormap = SettingsService.instance().get_value("depTable/colormap", value_type=str)
```

For keys that are registered (see the registry below), the default and value type are taken from the registry automatically, so `get_value("depTable/colormap")` already returns `"coolwarm"` when nothing is stored. For unregistered keys, pass `default` and `value_type` explicitly — native settings backends degrade stored types to strings, so the type is needed to round-trip values like floats.

## Writing a setting

```python
SettingsService.instance().set_value("depTable/colormap", "viridis")
```

`set_value` validates the value against the registry (if a validator is declared), stores it, and emits `settingChanged(key, value)` — but only when the stored value actually changes (or the key is new). Writing an identical value is a no-op that still returns `True`; a rejected value returns `False` and stores nothing.

## Subscribing to changes

Connect a slot to `settingChanged` to react to any setting change while the application runs. Values come from user-editable settings, so validate them before use — for example, `depTable/colormap` has no registered validator and an invalid colormap name must fall back to a safe default:

```python
from PySide6.QtCore import Slot

@Slot(str, object)
def _onSettingChanged(self, key: str, value):
    if key != "depTable/colormap":
        return
    try:
        self._colormap = matplotlib.colormaps[value]
    except (KeyError, TypeError, ValueError):
        self._colormap = matplotlib.colormaps["coolwarm"]

SettingsService.instance().settingChanged.connect(self._onSettingChanged)
```

This mirrors `PairTableStyledProxyModel._onSettingChanged`, which resolves names through `_resolveColormap` and additionally emits `dataChanged` so the correlation heatmap repaints with the new colors.

Other signals: `settingsReset()` fires after `reset_to_defaults()` (which also emits per-key `settingChanged(key, <effective default>)` for every removed key, so subscribers refresh without connecting to `settingsReset`), and `hierarchyChanged(group_path)` fires when a new key (for example, via `register_setting`) changes the tree structure.

## Adding a new settings group

Register new keys at module level (they are automatically part of the settings tree and get defaults/type coercion), or extend the registry at runtime with `register_setting`:

```python
from bn_modeller.utils.settings_service import (
    SettingDefinition,
    register_setting,
)

register_setting(
    SettingDefinition(
        "myWidget/someOption",
        default=0.5,
        value_type=float,
        validator=lambda value: 0.0 <= value <= 1.0,
    )
)
```

If the singleton already exists, `register_setting` rebuilds the model tree and emits `hierarchyChanged` for the affected group.

## Testing code that uses the service

`QSettings.setDefaultFormat` and `QSettings.setPath` are process-global, so tests must redirect storage before the singleton is created and drop the singleton afterwards. Use this fixture shape (INI format inside `tmp_path` keeps tests off the real registry):

```python
import pytest
from PySide6.QtCore import QCoreApplication, QSettings

from bn_modeller.utils.settings_service import SettingsService

@pytest.fixture
def service(qtbot, tmp_path):
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
```

The teardown half matters: without `reset_for_testing()` the next test could reuse a stale singleton whose `QSettings` is bound to an old `tmp_path`. See `tests/test_settings_service.py` for full coverage examples, including signal tests via `qtbot.waitSignal`.

## Thread safety

The service targets the GUI thread. `QSettings` itself is reentrant, but a single `SettingsService` instance (and its underlying `QSettings` object) is not safe for concurrent use from multiple threads — read and write settings from the main thread only.
