import numpy as np
import pandas as pd
import pingouin as pg


class CorrMatrix:
    def __init__(self, df):
        """
        Нахождение полной корреляции
        :param df:
        """
        self.df = df
        self.corr = self.df.corr(method="spearman")

    def getCorrMatrix(self, roundOrder=2):
        # return self.corr.round(roundOrder)
        return self.corr

    def updateTable(self, df):
        self.df = df
        self.corr = self.df.corr(method="spearman")


class PartCorrMatrix:
    def __init__(self, df: pd.DataFrame = None):
        """
        Нахождение частных корреляции
        :param parent:
        :param input_df:
        """
        self.df: pd.DataFrame = df
        self.corr = self.find_part_cor()
        self.corr = self.corr.astype("float")

    def find_part_cor(self):
        columns_all = self.df.columns
        P = pd.DataFrame(columns=self.df.columns, index=self.df.columns)
        for column_name1 in self.df.columns:
            for column_name2 in self.df.columns:
                if column_name1 == column_name2:
                    P.loc[column_name1, column_name2] = 1
                elif (
                    len(
                        pd.crosstab(self.df[column_name1], self.df[column_name2]).values
                    )
                    < 4
                ):
                    P.loc[column_name1, column_name2] = np.nan
                else:
                    columns_select = columns_all.drop(column_name1)
                    columns_select = columns_select.drop(column_name2)

                    try:
                        result = pg.partial_corr(
                            data=self.df,
                            x=column_name1,
                            y=column_name2,
                            covar=list(columns_select),
                            method="spearman",
                        )
                        P.loc[column_name1, column_name2] = result["r"].values[0]
                    except:
                        result = np.nan
        return P

    def getCorrMatrix(self):
        return self.corr
