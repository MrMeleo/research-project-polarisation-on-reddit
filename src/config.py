import os
import qbittorrentapi as qbt

qbittorrent = {
    "host" : "127.0.0.1:8080",
    "username" : "admin",
    "password" : "password",
    "self" : qbt.Client('http://localhost:8080/'),
    "urls" : "magnet:?xt=urn:btih:7c0645c94321311bb05bd879ddee4d0eba08aaee&tr=https%3A%2F%2Facademictorrents.com%2Fannounce.php&tr=udp%3A%2F%2Ftracker.coppersurfer.tk%3A6969&tr=udp%3A%2F%2Ftracker.opentrackr.org%3A1337%2Fannounce",
    "torrent_files_to_download" : list(range(0,6)) + list(range(207,210))
}

directories = {
    "zst_directory" : "/Users/MrMeleo/Desktop/Reddit Data Files/zst files",
    "csv_directory" : "/Users/MrMeleo/Desktop/Reddit Data Files/csv files", # Removed formatting f, test if this solves the issue
    "figures_directory" : f"/Users/MrMeleo/Desktop/Reddit Data Files/figures"
}

parsing = {
    "submission_fields" : ["subreddit","author","id","link","url"],
    "comment_fields" : ["subreddit","author","id","parent_id","link_id"],
    "limit_lines_read" : float("inf"),
    "filters" : ['ShovelKnight'],
    "file_size" : float
}

analysis_and_visualisation = {
    "is_undirected" : False,
    "save_fig" : True,
    "min_degree" : int,
    "prune_threshold" : float
}




