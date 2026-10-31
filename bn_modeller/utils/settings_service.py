"""Centralized application settings on top of QSettings.

The service is a singleton that owns a plain ``QSettings()`` instance (the
organization and application names are taken from ``QCoreApplication``, so no
names are hardcoded here) and exposes it through:

* typed accessors (:meth:`SettingsService.get_value` / :meth:`SettingsService.set_value`)
* a central registry of known keys (:class:`SettingDefinition`)
* change-notification signals (:attr:`SettingsService.settingChanged`,
  :attr:`SettingsService.settingsReset`, :attr:`SettingsService.hierarchyChanged`)
* a ``QAbstractItemModel`` tree interface for settings dialogs.

Thread-safety: the service targets the GUI thread. ``QSettings`` itself is
reentrant, but a single ``SettingsService`` instance (and its underlying
``QSettings`` object) is not safe for concurrent use from multiple threads.
"""

from dataclasses import dataclass
from typing import Any, Callable

from PySide6.QtCore import (
    QAbstractItemModel,
    QModelIndex,
    QSettings,
    Qt,
    Signal,
    Slot,
)


@dataclass(frozen=True)
class SettingDefinition:
    """Declaration of one known settings key.

    Attributes:
        key: Full settings path in QSettings group syntax,
            e.g. ``"depTable/colormap"``.
        default: Value returned by ``get_value`` when the key is absent.
        value_type: Type used to coerce the stored value on read. Native
            settings backends degrade types to strings, so registered keys
            should declare this.
        validator: Optional predicate; ``set_value`` refuses (and does not
            store) values for which it returns ``False``.
    """

    key: str
    default: Any = None
    value_type: type | None = None
    validator: Callable[[Any], bool] | None = None


SETTING_DEFINITIONS: tuple[SettingDefinition, ...] = (
    SettingDefinition("depTable/colormap", default="coolwarm", value_type=str),
    SettingDefinition("projectLoadWizard/lastProjectLocation", value_type=str),
    SettingDefinition("projectLoadWizard/lastProjectLocationDir", value_type=str),
    SettingDefinition("DataImportPage/lastSourceLocationDir", value_type=str),
)

_registered_settings: dict[str, SettingDefinition] = {
    definition.key: definition for definition in SETTING_DEFINITIONS
}


def register_setting(definition: SettingDefinition) -> None:
    """Extend the central registry with a new (or updated) key definition.

    If the singleton service already exists, its model tree is rebuilt and
    ``hierarchyChanged`` is emitted for the definition's group, so live views
    pick up the new branch.

    Args:
        definition: The setting to register.
    """
    _registered_settings[definition.key] = definition
    service = SettingsService._instance
    if service is not None:
        service._rebuildTree()
        service.hierarchyChanged.emit(_group_path(definition.key))


def _group_path(key: str) -> str:
    """Return the parent group path of a settings key ("" for top-level)."""
    return key.rsplit("/", 1)[0] if "/" in key else ""


class _Node:
    """Internal tree node: a settings group or a single key."""

    __slots__ = ("name", "parent", "children", "key")

    def __init__(self, name: str, parent: "_Node | None" = None):
        self.name = name
        self.parent = parent
        self.children: dict[str, "_Node"] = {}
        self.key: str | None = None


class SettingsService(QAbstractItemModel):
    """Singleton settings store, change notifier and tree model.

    Obtain the shared instance via :meth:`instance`. The model exposes two
    columns (Name, Value); leaf value cells are editable and routed through
    :meth:`set_value`.

    Signals:
        settingChanged(key, new_value): A setting was written or removed.
        settingsReset(): ``reset_to_defaults`` removed registered keys.
        hierarchyChanged(group_path): The tree structure of a group changed.
    """

    settingChanged = Signal(str, object)
    settingsReset = Signal()
    hierarchyChanged = Signal(str)

    _instance: "SettingsService | None" = None

    def __init__(self, parent: Any = None):
        """Use :meth:`instance` instead of constructing the service directly."""
        super().__init__(parent)
        self._settings = QSettings()
        self._root = _Node("")
        self._rebuildTree()
        self.settingChanged.connect(self._onSettingChanged)

    @classmethod
    def instance(cls) -> "SettingsService":
        """Return the lazily created singleton instance."""
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    @classmethod
    def reset_for_testing(cls) -> None:
        """Drop the singleton; the next ``instance()`` call re-creates it."""
        cls._instance = None

    def get_value(
        self,
        key: str,
        default: Any = None,
        value_type: type | None = None,
    ) -> Any:
        """Read a setting, applying registry defaults and type coercion.

        Args:
            key: Full settings key, e.g. ``"depTable/colormap"``.
            default: Fallback when the key is absent. When omitted, the
                registry default of a registered key is used.
            value_type: Type used to coerce the stored value. When omitted,
                the registered ``value_type`` is used; pass it explicitly for
                unregistered keys.

        Returns:
            The stored (coerced) value or the effective default.
        """
        definition = _registered_settings.get(key)
        if not self.contains(key):
            if default is None and definition is not None:
                return definition.default
            return default
        if default is None and definition is not None:
            default = definition.default
        if value_type is None and definition is not None:
            value_type = definition.value_type
        if value_type is not None:
            return self._settings.value(key, default, type=value_type)
        return self._settings.value(key, default)

    def set_value(self, key: str, value: Any) -> bool:
        """Validate and store a setting.

        The value is stored and ``settingChanged(key, value)`` is emitted only
        when the stored value actually changes (or the key is new); writing an
        identical value is a no-op. A first-time key also rebuilds the model
        tree and emits ``hierarchyChanged``.

        Args:
            key: Full settings key.
            value: Value to store.

        Returns:
            bool: ``True`` when the value is stored (or was already equal),
            ``False`` when a registered validator rejected the value.
        """
        definition = _registered_settings.get(key)
        if (
            definition is not None
            and definition.validator is not None
            and not definition.validator(value)
        ):
            return False
        node = self._findNode(key)
        if node is not None and self.contains(key) and self.get_value(key) == value:
            return True
        self._settings.setValue(key, value)
        if node is None:
            self._rebuildTree()
            self.hierarchyChanged.emit(_group_path(key))
        self.settingChanged.emit(key, value)
        return True

    def remove(self, key: str) -> bool:
        """Remove a key from storage.

        Emits ``settingChanged(key, <post-removal effective value>)`` so
        subscribers fall back to the registry default, and rebuilds the model
        tree with a ``hierarchyChanged`` notification.

        Args:
            key: Full settings key.

        Returns:
            bool: ``True`` if the key existed and was removed.
        """
        if not self.contains(key):
            return False
        self._settings.remove(key)
        effective_value = self.get_value(key)
        self._rebuildTree()
        self.settingChanged.emit(key, effective_value)
        self.hierarchyChanged.emit(_group_path(key))
        return True

    def contains(self, key: str) -> bool:
        """Return ``True`` when the key is present in storage."""
        return key in self._settings.allKeys()

    def sync(self) -> bool:
        """Flush pending changes to permanent storage."""
        self._settings.sync()
        return True

    def reset_to_defaults(self, group: str | None = None) -> None:
        """Remove registered keys from storage so defaults apply again.

        Unregistered keys are untouched. Values lazily fall back to their
        registry defaults on the next read. Emits ``settingsReset()``.

        Args:
            group: Optional group prefix (e.g. ``"projectLoadWizard"``) to
                restrict the reset to; ``None`` resets all registered keys.
        """
        prefix = "" if group is None else group.rstrip("/") + "/"
        for key in [key for key in _registered_settings if key.startswith(prefix)]:
            self._settings.remove(key)
        self._rebuildTree()
        self.settingsReset.emit()

    def index(
        self, row: int, column: int, parent: QModelIndex = QModelIndex()
    ) -> QModelIndex:
        parent_node = self._nodeForIndex(parent)
        if row < 0 or column < 0 or column > 1 or row >= len(parent_node.children):
            return QModelIndex()
        node = list(parent_node.children.values())[row]
        return self.createIndex(row, column, node)

    def parent(self, child: QModelIndex = QModelIndex()) -> QModelIndex:
        if not child.isValid():
            return QModelIndex()
        node = child.internalPointer()
        parent_node = node.parent
        if parent_node is None or parent_node is self._root:
            return QModelIndex()
        row = list(parent_node.parent.children).index(parent_node.name)
        return self.createIndex(row, 0, parent_node)

    def rowCount(self, parent: QModelIndex = QModelIndex()) -> int:
        return len(self._nodeForIndex(parent).children)

    def columnCount(self, parent: QModelIndex = QModelIndex()) -> int:
        return 2

    def data(self, index: QModelIndex, role: int = Qt.ItemDataRole.DisplayRole) -> Any:
        if not index.isValid():
            return None
        node = index.internalPointer()
        if role == Qt.ItemDataRole.ToolTipRole:
            if index.column() == 0:
                return self._nodePath(node)
            if node.key is not None:
                return f"{node.key} = {self.get_value(node.key)}"
            return None
        if role not in (Qt.ItemDataRole.DisplayRole, Qt.ItemDataRole.EditRole):
            return None
        if index.column() == 0:
            return node.name
        if node.key is None:
            return None
        return self.get_value(node.key)

    def setData(
        self,
        index: QModelIndex,
        value: Any,
        role: int = Qt.ItemDataRole.EditRole,
    ) -> bool:
        if role not in (Qt.ItemDataRole.DisplayRole, Qt.ItemDataRole.EditRole):
            return False
        if not index.isValid() or index.column() != 1:
            return False
        node = index.internalPointer()
        if node.key is None:
            return False
        return self.set_value(node.key, value)

    def flags(self, index: QModelIndex = QModelIndex()) -> Qt.ItemFlag:
        if not index.isValid():
            return Qt.ItemFlag.ItemIsEnabled
        node = index.internalPointer()
        item_flags = Qt.ItemFlag.ItemIsEnabled | Qt.ItemFlag.ItemIsSelectable
        if index.column() == 1 and node.key is not None:
            item_flags |= Qt.ItemFlag.ItemIsEditable
        return item_flags

    def headerData(
        self,
        section: int,
        orientation: Qt.Orientation,
        role: int = Qt.ItemDataRole.DisplayRole,
    ) -> Any:
        if role != Qt.ItemDataRole.DisplayRole:
            return None
        if orientation != Qt.Orientation.Horizontal:
            return None
        if section == 0:
            return "Name"
        if section == 1:
            return "Value"
        return None

    @Slot(str, object)
    def _onSettingChanged(self, key: str, value: Any) -> None:
        node = self._findNode(key)
        if node is None or node.parent is None:
            return
        row = list(node.parent.children).index(node.name)
        self.dataChanged.emit(
            self.createIndex(row, 1, node), self.createIndex(row, 1, node)
        )

    def _rebuildTree(self) -> None:
        self.beginResetModel()
        self._root = self._buildTree()
        self.endResetModel()

    def _buildTree(self) -> _Node:
        root = _Node("")
        keys = set(self._settings.allKeys()) | set(_registered_settings)
        for key in sorted(keys):
            node = root
            for part in key.split("/"):
                child = node.children.get(part)
                if child is None:
                    child = _Node(part, node)
                    node.children[part] = child
                node = child
            node.key = key
        return root

    def _findNode(self, key: str) -> "_Node | None":
        node = self._root
        for part in key.split("/"):
            node = node.children.get(part)
            if node is None:
                return None
        return node

    def _nodeForIndex(self, index: QModelIndex) -> _Node:
        if index.isValid():
            return index.internalPointer()
        return self._root

    def _nodePath(self, node: _Node) -> str:
        parts = []
        while node is not None and node.parent is not None:
            parts.append(node.name)
            node = node.parent
        return "/".join(reversed(parts))
