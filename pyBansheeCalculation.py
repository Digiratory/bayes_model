from py_banshee.rankcorr import bn_rankcorr
from py_banshee.bn_plot import bn_visualize
from py_banshee.prediction import inference, conditional_margins_hist


class BansheeCalc:
    def __init__(self, nodeList, edgeList, df):
        ParentCell = [None] * (max(nodeList) + 1)
        ParentCell = [[] for i in ParentCell]
        for v1, v2 in edgeList:
            ParentCell[v2].append(v1)
        print(ParentCell)

        columns_data = df.columns

        self.df = df
        self.R = bn_rankcorr(ParentCell, df,
                             var_names=columns_data,
                             is_data=True, plot=False)


    def getRankCorr(self):
        return self.R

    def getInference(self, len_input_list):
        nodes = list(range(len_input_list))  # all variables except for value of interest
        values = self.df.iloc[:, nodes].to_numpy() # data for predictions
        output = 'mean'  # show only mean of the uncertainty distribution
        sampleSize = 10000  # draw 10,000 samples when conditionalizing the BN
        interp = 'next'  # use the 'next' method to interpolate the empirical
        interp = 'linear'

        print(len_input_list)

        F = inference(Nodes=nodes,
                      Values=values,
                      R=self.R,
                      DATA=self.df,
                      Output=output,
                      SampleSize=sampleSize,
                      Interp=interp)
        return F
