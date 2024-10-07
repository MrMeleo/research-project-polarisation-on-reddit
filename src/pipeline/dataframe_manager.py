import pandas as pd

from collections import defaultdict
import backboning as bb 
from utils import submission_or_comment
import os
import glob




# Method to create general use dataframes for submission and comment data, respectively
def create_dataframes_from_csv(output_directory):
    
    path = output_directory # Uses the output directory from the previous method ie. where the converted .zst files end up
    csv_file_directory = glob.glob(os.path.join(path , "*.csv")) 

    li_S = [] # List of submission data
    li_C = [] # List of comment data

    # For each .csv file, checks if it contains submission or comment data and appends it to the corresponding list
    for csv_filename in csv_file_directory:
        is_submission = submission_or_comment(os.path.basename(csv_filename))
        if is_submission:
            li_S.append(pd.read_csv(csv_filename ,index_col=0, header=0))
        else:
            li_C.append(pd.read_csv(csv_filename, index_col=None, header=0))


    if li_S:        # Adds the submission data in the list to a dataframe or creates one if does not exist.
        df_submissions = pd.concat(li_S, axis=0, ignore_index=True) 
    else:
        df_submissions = pd.DataFrame()       

    if li_C: # Adds the comment data in the list to a dataframe or creates one if does not exist.
        df_comments = pd.concat(li_C, axis=0, ignore_index=True)
    else:
        df_comments = pd.DataFrame()
        

    # Modifies dataframe columns for readability and easier parsing
    

    df_comments['comment_id'] = df_comments['link'].str[-8:-1] # Creates column comment_id from the last part of the comment_link. Not necessary if parsing id in the first place!
    df_comments['parent_id'] = df_comments['parent_id'].apply(lambda x: x[-6:] if len(x)==9 else x[-7:]) # Sees if parent is submission or comment

    df_combined = pd.concat([ # Removes the distinction between submission and comment id's
        df_submissions,
        df_comments.rename(columns={"comment_id":"id"})
        ],axis=0)
    
    df_submissions = df_submissions.rename(columns={"id":"submission_id"}) # Keeps the distinction
    
    return {"df_submissions":df_submissions,"df_comments": df_comments,"df_combined": df_combined}


def create_interaction_network_dataframe(df_combined, is_undirected):
    
    interaction_counts = defaultdict(lambda: defaultdict(int))

    # Filter out certain users
    df_combined = df_combined[df_combined['author'] != '[deleted]']
    # For consideration - bots?

    total_combined = len(df_combined)

    map_id_to_author = dict(zip(df_combined["id"],df_combined["author"]))

    for index, row in df_combined.iterrows():
        author = row["author"]
        parent_id = row["parent_id"]

        if parent_id in map_id_to_author:
            parent_author = map_id_to_author[parent_id]

            if author != parent_author:
                interaction_counts[author][parent_author] += 1
                interaction_counts[parent_author][author] += 0 # Makes sure a count exists even if interactions are not mutual
        
        # Progress update
        if (index + 1) % 1000 == 0 or (index + 1) == total_combined:
            print(f"Processed {index + 1}/{total_combined} submissions and comments.")

    interaction_counts_list = []

    for user1, user2_dict in interaction_counts.items():
        for user2, count in user2_dict.items():
            if interaction_counts[user2][user1] > 0 and count > 0:  # Only accepts mutual interactions
                interaction_counts_list.append((user1, user2, count))

    df_interactions = pd.DataFrame(interaction_counts_list, columns=["src", "trg", "nij"])

    
    if is_undirected:
        df_interactions = df_interactions.groupby(["src", "trg"], as_index=False)["nij"].sum()

    print("Dataframe for interactions completed.")
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

