import networkx as nx
import matplotlib.pyplot as plt


def melt_matrix(matrix):
    """
    Преобразование из матрицы в таблицу
    :param matrix:
    :return:
    """
    matrix = matrix.stack().reset_index()
    matrix.columns = ['row', 'column', 'value']
    # result = matrix[~(matrix['row'] == matrix['column'])]
    result = matrix
    return result


class GraphPreparation:
    def __init__(self, corr_matrix, table_connection):
        self.corr_matrix = corr_matrix
        self.table_connection = table_connection
        code_columns = {num: i for i, num in enumerate(table_connection)}

        weight_matrix = self.corr_matrix * self.table_connection

        weight_matrix = weight_matrix.rename(code_columns, axis=0)
        weight_matrix = weight_matrix.rename(code_columns, axis=1)

        # подготовить матрицу к таблице
        self.N = melt_matrix(weight_matrix)

        self.N[['row', 'column']] = self.N[['row', 'column']].astype(int)

        # Создание взвешенного графа
        self.G = nx.DiGraph()

        e = [tuple([int(i[0]), int(i[1]), round(i[2], 3)]) for i in self.N.values]

        self.G.add_weighted_edges_from(e)

    def plot_graph(self):
        plt.figure()
        nx.draw_networkx(self.G, arrows=True)
        plt.show()

    def drop_cycle(self):
        while True:
            try:
                cycle_list = nx.find_cycle(self.G)
            except:
                break

            min_nodes = ()
            min_val = 10

            for i in cycle_list:
                weight = self.G.get_edge_data(*i)['weight']
                if weight < min_val:
                    min_val = weight
                    min_nodes = i

            self.G.remove_edge(*min_nodes)

    def getNodeList(self):
        return self.G.nodes

    def getEdgeList(self):
        return self.G.edges
