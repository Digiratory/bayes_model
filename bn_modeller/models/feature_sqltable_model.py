from PySide6.QtSql import QSqlRelationalTableModel, QSqlDatabase, QSqlRelation, QSqlQuery
from PySide6.QtCore import QObject


class FeatureSqlTableModel(QSqlRelationalTableModel):
    table_name = "feature"
    column_id = "id"
    column_name = "name"
    column_description = "description"
    column_is_active = "is_active"

    def __init__(self, parent: QObject = None, db: QSqlDatabase = None):
        super().__init__(parent, db)

        

        query = QSqlQuery(f"CREATE TABLE IF NOT EXISTS {FeatureSqlTableModel.table_name} (\
                          {FeatureSqlTableModel.column_id} INTEGER PRIMARY KEY AUTOINCREMENT, \
                          {FeatureSqlTableModel.column_name} TEXT, \
                          {FeatureSqlTableModel.column_description} TEXT, \
                          {FeatureSqlTableModel.column_is_active} INTEGER\
                          );\
                          ")
        
        if not query.exec():
            raise RuntimeError(f"Unable to connect to DB: {query.lastError()}")
        self.setTable(FeatureSqlTableModel.table_name)