import threading
from dataclasses import dataclass

from PySide6.QtCore import QObject, Signal, Slot
from PySide6.QtSql import QSqlDatabase, QSqlQuery

from bn_modeller.utils.db_model_handler import (
    ImportCancelled,
    apply_value_map,
    collect_non_numeric_values,
    create_project_schema,
    import_dataframe_to_db,
    read_sheet_dataframe,
)

# Fraction of the overall import progress reached after the sheet file has
# been read. import_dataframe_to_db continues from 0.35 with its own phases.
PROGRESS_READ_END = 0.15


@dataclass
class ImportSpec:
    """Parameters of a single data import run."""

    sheet_file_path: str
    transposed: bool = False
    skip_rows: int = 0
    skip_cols: int = 0
    db_file_path: str = ""


def _apply_speed_pragmas(db: QSqlDatabase):
    for pragma in (
        "cache_size = 16384",
        "temp_store = MEMORY",
        "journal_mode = PERSIST",
        "locking_mode = EXCLUSIVE",
        # WARNING: IT IS NOT SAFE. It can cause a DB damage in case of a bad
        # termination (carried over from the previous synchronous import).
        "synchronous = OFF",
    ):
        query = QSqlQuery(db)
        query.exec(f"PRAGMA {pragma}")


class DataImportWorker(QObject):
    """Runs the data file import off the GUI thread.

    The worker creates its own named Qt SQL connection inside :meth:`run`
    (Qt SQL connections must only be used from the thread that created
    them) and removes it before returning. Cancellation is cooperative: a
    :class:`threading.Event` is polled while waiting for user-provided
    value fixes and between row inserts.

    The modal value-fix dialogs stay on the GUI thread: the worker emits
    :attr:`fixValuesRequested` and blocks until the GUI thread calls
    :meth:`provideFixedValues` (or the run is cancelled).
    """

    # A negative fraction denotes an indeterminate phase (e.g. Excel reading).
    progress = Signal(float, str)
    fixValuesRequested = Signal(list)
    finished = Signal(object)
    failed = Signal(str)
    cancelled = Signal()

    DB_CONNECTION_NAME = "bn_import_worker"

    def __init__(self, spec: ImportSpec, parent=None):
        super().__init__(parent)
        self._spec = spec
        self._cancel_event = threading.Event()
        self._fix_event = threading.Event()
        self._value_map: dict = {}

    def cancel(self):
        """Request cancellation; safe to call from any thread."""
        self._cancel_event.set()
        # Wake the worker if it is waiting for fixed values.
        self._fix_event.set()

    @Slot(dict)
    def provideFixedValues(self, value_map: dict):
        """Receive the GUI-resolved value mapping and resume the import."""
        self._value_map = dict(value_map)
        self._fix_event.set()

    @Slot()
    def run(self):
        db = None
        try:
            db = QSqlDatabase.addDatabase("QSQLITE", self.DB_CONNECTION_NAME)
            db.setDatabaseName(self._spec.db_file_path)
            if not db.open():
                raise RuntimeError(
                    f"Unable to open the project database: {db.lastError().text()}"
                )
            _apply_speed_pragmas(db)
            create_project_schema(db)

            self.progress.emit(-1.0, self.tr("Reading file..."))
            data_pd = read_sheet_dataframe(
                self._spec.sheet_file_path,
                self._spec.transposed,
                skip_rows=self._spec.skip_rows,
                skip_cols=self._spec.skip_cols,
            )

            self.progress.emit(PROGRESS_READ_END, self.tr("Normalizing values..."))
            non_numeric = collect_non_numeric_values(data_pd)
            if non_numeric:
                self._request_value_fixes(non_numeric)
            data_pd = apply_value_map(data_pd, self._value_map)

            stats = import_dataframe_to_db(
                db,
                data_pd,
                progress_callback=lambda fraction, message: self.progress.emit(
                    fraction, message
                ),
                cancel_check=self._cancel_event.is_set,
            )
            self.finished.emit(stats)
        except ImportCancelled:
            self.cancelled.emit()
        except Exception as e:
            if self._cancel_event.is_set():
                self.cancelled.emit()
            else:
                self.failed.emit(str(e))
        finally:
            if db is not None:
                db.close()
                db = None
                QSqlDatabase.removeDatabase(self.DB_CONNECTION_NAME)

    def _request_value_fixes(self, non_numeric_values: list):
        """Ask the GUI thread for replacements for non-numeric values.

        Blocks the worker on an event until the GUI provides the mapping or
        the run is cancelled.
        """
        self._value_map = {}
        self._fix_event.clear()
        self.fixValuesRequested.emit(list(non_numeric_values))
        while not self._fix_event.wait(timeout=0.1):
            if self._cancel_event.is_set():
                raise ImportCancelled()
        if self._cancel_event.is_set():
            raise ImportCancelled()
