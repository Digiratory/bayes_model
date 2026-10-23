import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from py_banshee.bn_plot import bn_visualize
from py_banshee.prediction import conditional_margins_hist, inference
from py_banshee.rankcorr import bn_rankcorr


class BansheeCalc:
    def __init__(self, nodeList, edgeList, df):

        self.ParentCell = [None] * (max(nodeList) + 1)
        self.ParentCell = [[] for i in self.ParentCell]
        for v1, v2 in edgeList:
            self.ParentCell[v2].append(v1)

        self.df = df
        self.columns_data = list(df.columns)

        self.df = df
        self.R = None
        self.F = None
        self.calcRankCorr()

    def calcRankCorr(self):
        try:  # можно ли как-то избежать try/except, для случая когда много пропусков и функция не работает
            self.R = bn_rankcorr(
                self.ParentCell,
                self.df,
                var_names=self.columns_data,
                is_data=True,
                plot=False,
            )
        except:
            self.R = None

    def saveGraph(self):
        plt.close()
        plt.cla()
        plt.clf()

        fig_name = "graph"

        columns_with_com = list(map(lambda x: f'"{x}"', self.columns_data))

        bn_visualize(self.ParentCell, self.R, columns_with_com, fig_name=fig_name)

    def getRankCorr(self):
        return self.R

    def getTargetFeatures(self, input_features: list[str]) -> list[str]:
        """Return the features to predict: dataset columns minus the inputs."""
        return [column for column in self.columns_data if column not in input_features]

    def getInference(self, input_features: list[str], values) -> pd.DataFrame:
        """Predict the target features for the given input samples.

        Args:
            input_features: Names of the conditioning (input) features.
            values: Array-like with one row of input values per sample.

        Returns:
            pd.DataFrame: Mean predictions, one column per target feature,
            in dataset column order.
        """
        missing = [name for name in input_features if name not in self.columns_data]
        if missing:
            raise ValueError(f"Input features not present in the dataset: {missing}")

        nodes = [self.columns_data.index(name) for name in input_features]
        target_features = self.getTargetFeatures(input_features)

        values = np.asarray(values, dtype=float)
        if values.ndim == 1:
            values = values.reshape(1, -1)
        if values.shape[1] != len(input_features):
            raise ValueError(
                f"Expected {len(input_features)} value columns "
                f"for {list(input_features)}, got {values.shape[1]}"
            )

        output = "mean"  # show only mean of the uncertainty distribution
        sampleSize = 10000  # draw 10,000 samples when conditionalizing the BN
        interp = "linear"

        F = inference(
            Nodes=nodes,
            Values=values,
            R=self.R,
            DATA=self.df,
            Output=output,
            SampleSize=sampleSize,
            Interp=interp,
        )
        self.F = F
        return pd.DataFrame(F, columns=target_features)

    def plotHist(self, len_input_list):
        nodes = list(
            range(len_input_list)
        )  # all variables except for value of interest
        values = self.df.iloc[:, nodes].to_numpy()  # data for predictions

        conditional_margins_hist(
            F=self.F, DATA=self.df, names=self.df.columns, condition_nodes=nodes
        )
