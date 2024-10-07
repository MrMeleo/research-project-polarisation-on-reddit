import networkx as nx 
import plotly.graph_objects as go 
import matplotlib.pyplot as plt
import os


def visualize_tree_hierarchical(tree):
    G = nx.DiGraph()  # Create a directed graph
    for parent, children in tree.items():
        for child in children:
            G.add_edge(parent, child)

    pos = nx.spring_layout(G)  # Use a layout function for positioning

    edges_x = []
    edges_y = []
    for edge in G.edges():
        x0, y0 = pos[edge[0]]
        x1, y1 = pos[edge[1]]
        edges_x.append(x0)
        edges_x.append(x1)
        edges_x.append(None)  # Break line
        edges_y.append(y0)
        edges_y.append(y1)
        edges_y.append(None)  # Break line

    edge_trace = go.Scatter(
        x=edges_x, y=edges_y,
        line=dict(width=0.5, color='gray'),
        hoverinfo='none',
        mode='lines'
    )

    node_x = []
    node_y = []
    node_color = []  # List to hold color information
    for node in G.nodes():
        x, y = pos[node]
        node_x.append(x)
        node_y.append(y)
        # Assign colors based on whether the node is a submission (root) or a comment
        if node in tree:  # Assuming `tree` keys are submissions (roots)
            node_color.append('blue')  # Color for submissions
        else:
            node_color.append('green')  # Color for comments

    node_trace = go.Scatter(
        x=node_x, y=node_y,
        mode='markers',
        hoverinfo='text',
        text=list(G.nodes()),
        textposition="top center",
        marker=dict(
            showscale=False,
            size=10,
            color=node_color,  # Assign colors here
            line=dict(width=2)
        )
    )

    fig = go.Figure(data=[edge_trace, node_trace],
                     layout=go.Layout(
                         title='Hierarchical Tree Layout',
                         titlefont_size=16,
                         showlegend=False,
                         hovermode='closest',
                         margin=dict(b=0, l=0, r=0, t=40),
                         xaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
                         yaxis=dict(showgrid=False, zeroline=False, showticklabels=False))
                    )
    fig.show()


def visualize_user_interaction_network_rainbow(df_interactions):
    

    # Create a graph from the interaction data (unweighted)
    G = nx.from_pandas_edgelist(df_interactions, 'user1', 'user2')

    total_nodes = G.number_of_nodes()
    print(f"Total number of nodes: {total_nodes}")

    # Calculate positions using spring layout
    pos = nx.spring_layout(G, k=0.5)  # Adjust 'k' to control spacing between nodes

    
    # Creating hover text for nodes and calculating total interactions
    hover_text = []
    total_interactions = {}
    for node in G.nodes():
        # Get the total interaction count for each user
        total_count = sum(df_interactions.loc[
            (df_interactions['user1'] == node) | (df_interactions['user2'] == node), 
            'count'
        ])
        total_interactions[node] = total_count
        hover_text.append(f"User: {node}<br>Total Interactions: {total_count}")

    def custom_scaling(interaction_count):
        """Custom scaling function for node sizes based on interaction counts."""
        if interaction_count == 1:
            return 1, 'red'  # Smallest size for 1 interaction
        elif interaction_count <= 5:
            return 3, 'orange'  # Size for 5 interactions
        elif interaction_count <= 10:
            return 8, 'yellow'  # Size for 10 interactions
        elif interaction_count <= 50:
            return 21, 'green'  # Size for 50 interactions
        elif interaction_count <= 100:
            return 55, 'blue'  # Size for 100 interactions
        else:
            return 84, 'purple'  # Size for more than 100 interactions

    # Calculate node sizes based on the custom scaling function
    node_sizes = []
    node_colors = []
    for node in G.nodes():
        size, color = custom_scaling(total_interactions[node])
        node_sizes.append(size)
        node_colors.append(color)
    
      # Adjust k for more spacing
    # Now use node_sizes in your Plotly visualization
    fig = go.Figure()

    edge_x = []
    edge_y = []
    for edge in G.edges():
        x0, y0 = pos[edge[0]]
        x1, y1 = pos[edge[1]]
        edge_x.append(x0)
        edge_x.append(x1)
        edge_x.append(None)  # None separates lines
        edge_y.append(y0)
        edge_y.append(y1)
        edge_y.append(None)

    # Create the figure for the unweighted network graph
    

    # Add edges
    fig.add_trace(go.Scatter(
        x=edge_x, y=edge_y,
        line=dict(width=0.5, color='gray'),
        hoverinfo='none',
        mode='lines'))

    # Add nodes
    fig.add_trace(go.Scatter(
        x=[pos[node][0] for node in G.nodes()],
        y=[pos[node][1] for node in G.nodes()],
        mode='markers',
        marker=dict(size=node_sizes, color=node_colors, line=dict(width=1)),
        text=[f"{node}<br>Interactions: {total_interactions[node]}" for node in G.nodes()],
        textposition="bottom center",
        hoverinfo='text'))

    # Update layout
    fig.update_layout(title='User Interaction Network (Unweighted)',
                    showlegend=True,
                    hovermode='closest',
                    margin=dict(l=0, r=0, t=50, b=0))

    # Show the figure
    fig.show()


def visualize_cluster_graph(noise_corrected_table, prune_threshold=None, save_fig=True, filter_degree=True, min_degree=2, save_dir='figures'):
    
    # Step 1: Create a graph from the DataFrame
    G = nx.from_pandas_edgelist(noise_corrected_table, 'src', 'trg', ['nij', 'score'])

    # Step 2: Prune edges based on the score threshold
    if prune_threshold is not None:
        edges_to_remove = [(u, v) for u, v, data in G.edges(data=True) if data['score'] < prune_threshold]
        G.remove_edges_from(edges_to_remove)
    
    if filter_degree:
        nodes_to_remove = [node for node, degree in dict(G.degree()).items() if degree < min_degree]
        G.remove_nodes_from(nodes_to_remove)

    # Step 3: Identify communities using greedy modularity
    communities = nx.community.greedy_modularity_communities(G,weight="score")

    # Step 4: Create a supergraph for community visualization
    supergraph = nx.cycle_graph(len(communities))
    superpos = nx.spring_layout(supergraph, scale=50, seed=429)

    # Step 5: Compute positions for each community
    pos = {}
    for center, comm in zip(superpos.values(), communities):
        comm_pos = nx.spring_layout(nx.subgraph(G, comm), center=center, seed=1430)
        pos.update(comm_pos)

    # Step 6: Draw the nodes colored by cluster
    # Generate a list of colors from the colormap
    num_communities = len(communities)
    colors = plt.cm.get_cmap('tab10', num_communities)  # Use 'tab10' colormap

    for i, nodes in enumerate(communities):
        node_color = colors(i)  # Get color for the i-th community
        nx.draw_networkx_nodes(G, pos=pos, nodelist=nodes, node_color=node_color, node_size=50)

    # Step 7: Draw the edges
    nx.draw_networkx_edges(G, pos=pos)

    # Step 8: Show the plot
    plt.title('Graph Visualization with Cluster Layout')
    plt.tight_layout()

    # Step 9: Save the figure if the option is enabled
    if save_fig:
        if not os.path.exists(save_dir):
            os.makedirs(save_dir)
        file_count = len(os.listdir(save_dir))
        plt.savefig(os.path.join(save_dir, f'graph_visualization_{file_count + 1}.png'))

    plt.show()




