import pandas as pd
from PySide6.QtCore import QAbstractItemModel, Qt


def tablemodel_to_dataframe(
    model: QAbstractItemModel, role: int, postprocess: callable = lambda x: x
) -> pd.DataFrame:
    """Converts a QAbstractItemModel to a pandas DataFrame.

    Args:
        model (QAbstractItemModel): Source QAbstractItemModel.
        role (int): Role to extract from the model.
        postprocess (callable, optional): Function to apply to each element. Defaults to lambda x: x.
    Returns:
        pd.DataFrame: Pandas DataFrame containing the model's data.
    """
    data_pd = pd.DataFrame(
        columns=[
            model.headerData(c, Qt.Orientation.Horizontal)
            for c in range(model.columnCount())
        ]
    )
    for r in range(model.rowCount()):
        new_row = pd.Series(
            {
                model.headerData(c, Qt.Orientation.Horizontal): postprocess(
                    model.index(r, c).data(role=role)
                )
                for c in range(model.columnCount())
            }
        )
        data_pd.loc[model.headerData(r, Qt.Orientation.Vertical)] = new_row

    return data_pd
