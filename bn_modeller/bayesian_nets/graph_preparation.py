import networkx as nx


def melt_matrix(matrix):
    """
    Преобразование из матрицы в таблицу
    :param matrix:
    :return:
    """
    matrix = matrix.stack().reset_index()
    matrix.columns = ["row", "column", "value"]
    # result = matrix[~(matrix['row'] == matrix['column'])]
    result = matrix
    return result


class GraphPreparation:
    def __init__(
        self,
        corr_matrix,
        table_connection,
        threshold,
        pvalue_matrix=None,
        pvalue_threshold=0.05,
    ):
        if pvalue_matrix is not None:
            assert (
                corr_matrix.shape == pvalue_matrix.shape
            ), "Correlation matrix and p-value matrix must have the same shape"

        self.threshold = threshold
        self.corr_matrix = corr_matrix
        self.table_connection = table_connection
        self.pvalue_matrix = pvalue_matrix
        self.code_columns = {num: i for i, num in enumerate(table_connection)}

        if pvalue_matrix is not None:
            self.corr_matrix = self.corr_matrix.mul(
                pvalue_matrix.map(lambda x: x < pvalue_threshold)
            )

        weight_matrix = self.corr_matrix * self.table_connection.map(
            lambda x: bool(x.value)
        )

        weight_matrix = weight_matrix.rename(self.code_columns, axis=0)
        weight_matrix = weight_matrix.rename(self.code_columns, axis=1)

        # подготовить матрицу к таблице
        self.N = melt_matrix(weight_matrix)
        self.N = self.N[(abs(self.N["value"]) > threshold)]
        self.N[["row", "column"]] = self.N[["row", "column"]].astype(int)

        # Создание взвешенного графа
        self.G = nx.DiGraph()

        e = [tuple([int(i[0]), int(i[1]), round(i[2], 3)]) for i in self.N.values]

        self.G.add_weighted_edges_from(e)

    def drop_cycle(self):
        while True:
            try:
                cycle_list = nx.find_cycle(self.G)
            except:
                break

            min_nodes = ()
            min_val = 10

            for i in cycle_list:
                weight = self.G.get_edge_data(*i)["weight"]
                if weight < min_val:
                    min_val = weight
                    min_nodes = i

            self.G.remove_edge(*min_nodes)

    def getNodeList(self):
        return self.G.nodes

    def getEdgeList(self):
        return self.G.edges

    def getGraph(self):
        return self.G

    def renaming(self):
        k = {val: key for key, val in self.code_columns.items()}

        return nx.relabel_nodes(self.G, k)
