import pandas as pd
import networkx as nx 
import plotly.graph_objects as go 
from collections import defaultdict
import matplotlib.pyplot as plt 
from helper_methods import submission_or_comment
import os
import glob

output_directory = r"/Users/MrMeleo/Desktop/Reddit Data Files/csv files"

def create_dataframes_from_csv(output_directory):
    
    path = output_directory
    csv_file_directory = glob.glob(os.path.join(path , "*.csv"))

    li_S = []
    li_C = []

    for csv_filename in csv_file_directory:
        is_submission = submission_or_comment(os.path.basename(csv_filename))
        if is_submission:
            li_S.append(pd.read_csv(csv_filename ,index_col=0, header=0))
        else:
            li_C.append(pd.read_csv(csv_filename, index_col=None, header=0))

    if li_S:
        df_submissions = pd.concat(li_S, axis=0, ignore_index=True)
    else: 
        df_submissions = pd.DataFrame()

    if li_C:
        df_comments = pd.concat(li_C, axis=0, ignore_index=True)
    else: 
        df_comments = pd.DataFrame()

    df_submissions = df_submissions.rename(columns={"id":"submission_id"})
    df_comments['comment_id'] = df_comments['link'].str[-8:-1]
    df_comments['parent_id'] = df_comments['parent_id'].apply(lambda x: x[-6:] if len(x)==9 else x[-7:])

    print (df_submissions.info())
    print (df_comments.info())

    return df_submissions, df_comments

df_submissions, df_comments = create_dataframes_from_csv(output_directory)


def create_interaction_network(df_submissions, df_comments):
    interaction_counts = defaultdict(int)

    # Filter out deleted users
    df_submissions = df_submissions[df_submissions['author'] != '[deleted]']
    df_comments = df_comments[df_comments['author'] != '[deleted]']

    total_submissions = len(df_submissions)
    total_comments = len(df_comments)
    
    print(f"Total Submissions: {total_submissions}")
    print(f"Total Comments: {total_comments}")
    print("Counting interactions")

    # Process submissions
    for index, submission_row in df_submissions.iterrows():
        submission_author = submission_row["author"]
        submission_id = submission_row["submission_id"]

        # Filter comments related to the current submission_id
        comment_authors = df_comments[df_comments["parent_id"] == submission_id]["author"]

        for comment_author in comment_authors:
            if submission_author != comment_author:
                interaction_counts[(submission_author, comment_author)] += 1
        
        # Progress update for submissions
        if (index + 1) % 1000 == 0 or (index + 1) == total_submissions:
            print(f"Processed {index + 1}/{total_submissions} submissions.")

    # Process comments
    for index, comment_row in df_comments.iterrows():
        comment_author = comment_row["author"]
        parent_id = comment_row["parent_id"]

        if len(parent_id) > 6:  # Check if it's a comment (not a submission)
            parent_comment_author = df_comments.loc[df_comments["comment_id"] == parent_id, "author"].values
            if parent_comment_author.size > 0:
                parent_comment_author = parent_comment_author[0]
                if comment_author != parent_comment_author:
                    interaction_counts[(comment_author, parent_comment_author)] += 1
        
        # Progress update for comments
        if (index + 1) % 1000 == 0 or (index + 1) == total_comments:
            print(f"Processed {index + 1}/{total_comments} comments.")

    # Convert interaction counts to DataFrame
    df_interactions = pd.DataFrame(interaction_counts.items(), columns=["user_pair", "count"])
    df_interactions[["user1", "user2"]] = pd.DataFrame(df_interactions["user_pair"].tolist(), index=df_interactions.index)
    df_interactions = df_interactions.drop(columns=["user_pair"])

    print("Counting interactions complete.")
    print(df_interactions.head())  # Display the first few interactions for verification
    return df_interactions


def create_tree(df_submissions, df_comments):
    tree = {}
    orphans = []
    nodes_added = 0
    amount_orphans = 0

    for submission_id in df_submissions['submission_id']:
            tree[submission_id] = []

    progress = True
    while progress:
        progress = False

        for _, row in df_comments.iterrows():
            comment_id = row['comment_id']
            parent_id = row['parent_id']
            if parent_id in tree:
                if comment_id not in tree[parent_id]:
                    tree[parent_id].append(comment_id)
                    nodes_added += 1
                    print (nodes_added," Node added to the tree!",end="\r")
                    # if nodes_added % 10000 == 0:
                    #     print ({nodes_added}, "nodes added to the tree!")
                    progress = True
    print ("While loop properly exited, progress: ", progress)
    for _, row in df_comments.iterrows():
        comment_id = row['comment_id']
        if comment_id not in tree:
            orphans.append(comment_id)
            amount_orphans += 1
            print (amount_orphans,"orphans added!",end="\r")

    return tree, orphans


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


def visualize_user_interaction_network(df_interactions):
    

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


df_interactions = create_interaction_network(df_submissions, df_comments)
visualize_user_interaction_network(df_interactions)



#tree, orphans = create_tree(df_submissions, df_comments)

#visualize_tree_hierarchical(tree)



