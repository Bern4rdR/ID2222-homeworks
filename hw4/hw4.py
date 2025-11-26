import numpy as np

from scipy.sparse import coo_matrix, csgraph
from scipy.sparse.linalg import eigsh
from numpy.linalg import eig
import matplotlib.pyplot  as plt;
from sklearn import cluster

def dat_to_adj(filename):
    E = np.loadtxt(filename, delimiter=",")

    # Extract columns
    col1 = E[:, 0].astype(int)
    col2 = E[:, 1].astype(int)

    # Find maximum node id
    max_ids = int(max(col1.max(), col2.max()))

    # --- Build sparse adjacency matrix ---
    As = coo_matrix((np.ones(len(col1)), (col1 - 1, col2 - 1)),  # if ids start at 1
                    shape=(max_ids, max_ids))
    return As

def spectral_cluster(As, num_clusters):
    L = csgraph.laplacian(As, normed=False) # per the document, not the class notes, but either is fine
    evals, X = eigsh(L, k=num_clusters, which='SM') # get num_clusters eigenvalues, the paper says normed=True and k largest, but class says normed=False and k smallest, and class works
    row_norms = np.linalg.norm(X, axis=1, keepdims=True)
    Y = X / row_norms
    km = cluster.KMeans(n_clusters=num_clusters)
    km.fit(Y)
    clusters = km.labels_
    return clusters

if __name__ == "__main__":
    print("starting")
    As = dat_to_adj(filename="example1.dat")
    clusters = spectral_cluster(As, num_clusters=4)
    A = As.toarray()
    print("Got clusters")
    # Assume clusters is a 1D array of cluster assignments for each node
    # clusters = kmeans.labels_

    num_clusters = len(np.unique(clusters))
    colors = plt.cm.get_cmap('tab10', num_clusters)  # discrete colormap

    # Create a colored version of adjacency matrix
    colored_A = np.zeros(A.shape + (4,))  # RGBA array

    for i in range(A.shape[0]):
        for j in range(A.shape[1]):
            if A[i, j] != 0:  # there is an edge
                colored_A[i, j] = colors(clusters[i])  # color by row node's cluster
            else:
                colored_A[i, j] = [1, 1, 1, 1]  # white for no edge

    plt.figure(figsize=(6, 6))
    plt.imshow(colored_A)
    plt.title("Adjacency Matrix with Cluster Colors")
    plt.xlabel("Node j")
    plt.ylabel("Node i")
    plt.show()