from bw2calc import LCA
from numpy import absolute, array, dot, ones, where


class ConvergenceError(Exception):
    pass


class PageRank:
    def __init__(self, database):
        self.database = database

    def calculate(self):
        self.lca = LCA({self.database.random(): 1})
        self.lca.lci()
        self.matrix = self.lca.technosphere_matrix.transpose()
        self.pr = [
            (x[0], self.lca.dicts.activity.reversed[x[1]])
            for x in self.page_rank(self.matrix)
        ]
        return self.pr

    def page_rank(self, technosphere, alpha=0.85, max_iter=100, tol=1e-6):
        """
        Return the PageRank of the nodes in the graph.

        Adapted from http://networkx.lanl.gov/svn/networkx/trunk/networkx/algorithms/link_analysis/pagerank_alg.py

        PageRank computes a ranking of the nodes in the graph G based on
        the structure of the incoming links. It was originally designed as
        an algorithm to rank web pages.

        The eigenvector calculation uses power iteration with a SciPy
        sparse matrix representation.

        Args:
            * *technosphere* (scipy sparse matrix): The technosphere matrix.
            * *alpha* (float, optional): Damping parameter for PageRank, default=0.85

        Returns:
            * Dictionary of nodes (activity codes) with value as PageRank


        References

        .. [1] A. Langville and C. Meyer,
           "A survey of eigenvector methods of web information retrieval."
           http://citeseer.ist.psu.edu/713792.html
        .. [2] Page, Lawrence; Brin, Sergey; Motwani, Rajeev and Winograd, Terry,
           The PageRank citation ranking: Bringing order to the Web. 1999
           http://dbpubs.stanford.edu:8090/pub/showDoc.Fulltext?lang=en&doc=1999-66&format=pdf
        """
        mat = technosphere.copy()
        (n, m) = mat.shape
        assert n == m  # should be square
        nodelist = range(n)

        # Drop diagonals, and only indicate adjacency
        mat.data[:] = 1
        for x in range(n):
            mat[x, x] = 0

        column_sum = array(mat.sum(axis=1)).flatten()
        index = where(column_sum != 0)[0]
        mat = mat.tolil()
        for i in index:
            # Workaround for lack of fancy indexing in CSR matrices
            mat[i, :] *= 1.0 / column_sum[i]

        mat = mat.tocsc()
        x = ones((n)) / n  # initial guess
        dangle = array(where(mat.sum(axis=1) == 0, 1.0 / n, 0)).flatten()
        i = 0

        while True:  # power iteration: make up to max_iter iterations
            xlast = x
            x = alpha * (x * mat + dot(dangle, xlast)) + (1 - alpha) * xlast.sum() / n
            # check convergence, l1 norm
            err = absolute(x - xlast).sum()
            if err < n * tol:
                break
            if i > max_iter:
                raise ConvergenceError(
                    "pagerank: power iteration "
                    "failed to converge in %d iterations." % (i + 1)
                )
            i += 1

        return sorted(zip(x, nodelist), reverse=True)
