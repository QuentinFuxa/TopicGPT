import numpy as np
import umap
import hdbscan
import matplotlib.pyplot as plt
import pandas as pd
import plotly.express as px
import umap.plot
from copy import deepcopy
from sklearn.cluster import AgglomerativeClustering

class Clustering_and_DimRed():

    """
    Class to perform dimensionality reduction with UMAP followed by clustering with HDBSCAN.
    """


    def __init__(self,
                 n_dims_umap:int = 5,
                 n_neighbors_umap:int = 15,
                 min_dist_umap:float = 0,
                 metric_umap:str = "cosine",
                 min_cluster_size_hdbscan:int = 15,
                 metric_hdbscan:str = "euclidean",
                 cluster_selection_method_hdbscan:str = "eom",
                 number_clusters_hdbscan:int = None,
                 random_state:int = 42,
                 verbose:bool = True,
                 UMAP_hyperparams:dict = {},
                 HDBSCAN_hyperparams:dict = {}) -> None:
        """
        params: 
            n_dims_umap: int, number of dimensions to reduce to
            n_neighbors_umap: int, number of neighbors for UMAP
            min_dist_umap: float, minimal distance for UMAP
            metric_umap: str, metric for UMAP
            min_cluster_size_hdbscan: int, minimal cluster size for HDBSCAN
            metric_hdbscan: str, metric for HDBSCAN
            cluster_selection_method_hdbscan: str, cluster selection method for HDBSCAN
            number_clusters_hdbscan: int, number of clusters for HDBSCAN. If None, HDBSCAN will determine the number of clusters automatically. Make sure that min_cluster_size is not too big to find enough clusters.
            random_state: int, random state for UMAP and HDBSCAN
            verbose: bool, whether to print progress
            UMAP_hyperparams: dict, further hyperparameters for UMAP
            HDBSCAN_hyperparams: dict, further hyperparameters for HDBSCAN
        """

        self.random_state = random_state
        self.verbose = verbose
        self.UMAP_hyperparams = UMAP_hyperparams
        self.HDBSCAN_hyperparams = HDBSCAN_hyperparams

        # update hyperparameters for UMAP
        self.UMAP_hyperparams["n_components"] = n_dims_umap
        self.UMAP_hyperparams["n_neighbors"] = n_neighbors_umap
        self.UMAP_hyperparams["min_dist"] = min_dist_umap
        self.UMAP_hyperparams["metric"] = metric_umap
        self.UMAP_hyperparams["random_state"] = random_state
        self.UMAP_hyperparams["verbose"] = verbose
        self.umap = umap.UMAP(**self.UMAP_hyperparams)

        self.HDBSCAN_hyperparams["min_cluster_size"] = min_cluster_size_hdbscan
        self.HDBSCAN_hyperparams["metric"] = metric_hdbscan
        self.HDBSCAN_hyperparams["cluster_selection_method"] = cluster_selection_method_hdbscan
        self.number_clusters_hdbscan = number_clusters_hdbscan
        self.hdbscan = hdbscan.HDBSCAN(**self.HDBSCAN_hyperparams)

    
    def reduce_dimensions_umap(self, embeddings: np.ndarray) -> np.ndarray:
        """
        Reduce dimensions with UMAP.
        params:
            embeddings: np.ndarray, embeddings to reduce
        returns:
            np.ndarray, reduced embeddings
            umap.UMAP, UMAP mapper to transform new embeddings, especially embeddings of the vocabulary (MAKE SURE TO NORMALIZE EMBEDDINGS AFTER USING THE MAPPER)
        """
        mapper = umap.UMAP(**self.UMAP_hyperparams).fit(embeddings)
        dim_red_embeddings = mapper.transform(embeddings)
        dim_red_embeddings = dim_red_embeddings/np.linalg.norm(dim_red_embeddings, axis=1).reshape(-1,1)
        return dim_red_embeddings, mapper
    
    def cluster_hdbscan(self, embeddings: np.ndarray) -> np.ndarray:
        """
        Cluster embeddings with HDBSCAN.
        If self.number_clusters_hdbscan is not None, further clusters the data with AgglomerativeClustering to achieve a fixed number of clusters.
        params:
            embeddings: np.ndarray, embeddings to cluster
        returns:
            np.ndarray, cluster labels
        """
        labels = self.hdbscan.fit_predict(embeddings)
        outliers = np.where(labels == -1)[0]

        if self.number_clusters_hdbscan is not None:
            clusterer = AgglomerativeClustering(n_clusters=self.number_clusters_hdbscan)
            labels = clusterer.fit_predict(embeddings)
            labels[outliers] = -1

        return labels
    
    def cluster_and_reduce(self, embeddings: np.ndarray) -> tuple[np.ndarray, np.ndarray, umap.UMAP]:
        """
        Cluster embeddings with HDBSCAN and reduce dimensions with UMAP.
        params:
            embeddings: np.ndarray, embeddings to cluster and reduce
        returns:
            np.ndarray, reduced embeddings
            np.ndarray, cluster labels
            umap.UMAP, UMAP mapper to transform new embeddings, especially embeddings of the vocabulary (MAKE SURE TO NORMALIZE EMBEDDINGS AFTER USING THE MAPPER)
        """
        dim_red_embeddings, umap_mapper = self.reduce_dimensions_umap(embeddings)
        clusters = self.cluster_hdbscan(dim_red_embeddings)
        return dim_red_embeddings, clusters, umap_mapper
    
    def visualize_clusters_static(self, embeddings: np.ndarray, labels: np.ndarray):
        """
        reduce dimensionality with UMAP to two dimensions and plot the clusters
        params:
            embeddings: np.ndarray, whose clustering to plot
            labels: np.ndarray, cluster labels
        """

        # Reduce dimensionality with UMAP
        reducer = umap.UMAP(n_components=2, random_state = self.random_state, n_neighbors=30, metric="cosine", min_dist=0)
        embeddings_2d = reducer.fit_transform(embeddings)


        # Create a color palette, then map the labels to the colors.
        # We add one to the number of unique labels to account for the noise points labelled as -1.
        palette = plt.cm.get_cmap("tab20", len(np.unique(labels)) + 1)
        
        # Create a new figure
        fig, ax = plt.subplots(figsize=(10, 8))

        outlier_shown_in_legend = False

        # Iterate through all unique labels (clusters and outliers)
        for label in np.unique(labels):
            # Find the embeddings that are part of this cluster
            cluster_points = embeddings_2d[labels == label]
            
            # If label is -1, these are outliers. We want to display them in grey.
            if label == -1:
                color = 'grey'
                if not outlier_shown_in_legend:
                    ax.scatter(cluster_points[:, 0], cluster_points[:, 1], c=color, label='outlier', s = 0.1)
                    outlier_shown_in_legend = True
                else:
                    ax.scatter(cluster_points[:, 0], cluster_points[:, 1], c=color, s = 0.1)
            else:
                color = palette(label)
                # Plot the points in this cluster without a label to prevent them from showing up in the legend
                ax.scatter(cluster_points[:, 0], cluster_points[:, 1], c=color, s = 0.1)
            
        # Add a legend
        ax.legend()

        # Show the plot
        plt.show()


    def visualize_clusters_dynamic(self, embeddings: np.ndarray, labels: np.ndarray, texts: list[str]):
        """
        visualize clusters with plotly and allow to hover over clusters to see the beginning of the texts of the documents
        params:
            embeddings: np.ndarray, embeddings whose clustering to plot
            labels: np.ndarray, cluster labels
            texts: list[str], texts of the documents
        """

        # Reduce dimensionality with UMAP
        reducer = umap.UMAP(n_components=2, random_state = self.random_state, n_neighbors=30, metric="cosine", min_dist=0)
        embeddings_2d = reducer.fit_transform(embeddings)

        df = pd.DataFrame(embeddings_2d, columns=['x', 'y'])
        df['text'] = [text[:100] for text in texts] 
        df["class"] = labels

        # Create a color palette, then map the labels to the colors.
        # Exclude the outlier (-1) label from color palette assignment
        unique_labels = [label for label in np.unique(labels) if label != -1]
        palette = plt.cm.get_cmap("tab20", len(unique_labels))

        # Create color map
        color_discrete_map = {label: 'rgb'+str(tuple(int(val*255) for val in palette(i)[:3])) if label != -1 else 'grey' for i, label in enumerate(unique_labels)}
        color_discrete_map[-1] = 'grey'
        
        # plot data points where the color represents the class
        fig = px.scatter(df, x='x', y='y', hover_data=['text', 'class'], color='class', color_discrete_map=color_discrete_map)
        
        fig.update_traces(mode='markers', marker=dict(size=3))  # Optional: Increase the marker size

        

    
        # make plot quadratic
        fig.update_layout(
        autosize=False,
        width=1500,
        height=1500,
        margin=dict(
            l=50,   
            r=50,
            b=100,
            t=100,
            pad=4
        )
    )
        # set title 
        fig.update_layout(title_text='UMAP projection of the document embeddings', title_x=0.5)

        
        # show plot
        fig.show()


    def umap_diagnostics(self, embeddings, hammer_edges = False):
        """
        Fit UMAP on the provided embeddings and generate diagnostic plots.
        
        Params:
        ------
        embeddings : array-like
            The high-dimensional data for UMAP to reduce and visualize.
        hammer_edges : bool, default False. Is computationally expensive.
            
        """
        new_hyperparams = deepcopy(self.UMAP_hyperparams)
        new_hyperparams["n_components"] = 2
        mapper = umap.UMAP(**new_hyperparams).fit(embeddings)

        # 1. Connectivity plot with points
        print("UMAP Connectivity Plot with Points")
        umap.plot.connectivity(mapper, show_points=True)
        plt.show()

        if hammer_edges:
            # 2. Connectivity plot with edge bundling
            print("UMAP Connectivity Plot with Hammer Edge Bundling")
            umap.plot.connectivity(mapper, edge_bundling='hammer')
            plt.show()

        # 3. PCA diagnostic plot
        print("UMAP PCA Diagnostic Plot")
        umap.plot.diagnostic(mapper, diagnostic_type='pca')
        plt.show()

        # 4. Local dimension diagnostic plot
        print("UMAP Local Dimension Diagnostic Plot")
        umap.plot.diagnostic(mapper, diagnostic_type='local_dim')
        plt.show()