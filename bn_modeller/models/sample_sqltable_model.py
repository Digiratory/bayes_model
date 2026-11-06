from PySide6.QtCore import QObject
from PySide6.QtSql import (
    QSqlDatabase,
    QSqlQuery,
    QSqlRelation,
    QSqlRelationalTableModel,
)

from bn_modeller.models.feature_sqltable_model import FeatureSqlTableModel


class SampleSqlTableModel(QSqlRelationalTableModel):
    table_name = "sample"
    column_id = "id"
    column_sample_id = "sample_id"
    column_feature_id = "feature_id"
    column_value = "value"
    create_table_sql = f"CREATE TABLE IF NOT EXISTS {table_name} (\
                          {column_id} INTEGER PRIMARY KEY AUTOINCREMENT, \
                          {column_sample_id} INTEGER, \
                          {column_feature_id} INTEGER, \
                          {column_value} REAL,\
                          FOREIGN KEY({column_feature_id}) REFERENCES {FeatureSqlTableModel.table_name}({FeatureSqlTableModel.column_id})\
                          );\
                          "

    def __init__(self, parent: QObject = None, db: QSqlDatabase = None):
        super().__init__(parent, db)

        self.setRelation(
            2,
            QSqlRelation(
                aTableName=FeatureSqlTableModel.table_name,
                indexCol=SampleSqlTableModel.column_feature_id,
                displayCol=FeatureSqlTableModel.column_name,
            ),
        )
        self.setJoinMode(QSqlRelationalTableModel.JoinMode.LeftJoin)

        query = QSqlQuery(self.create_table_sql)

        if not query.exec():
            raise RuntimeError(f"Unable to connect to DB: {query.lastError()}")
        self.setTable(SampleSqlTableModel.table_name)

    def insertRowIntoTable(self, values):
        return super().insertRowIntoTable(values)
