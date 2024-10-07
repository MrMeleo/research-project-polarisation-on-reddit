# This script is based on the to_csv by https://github.com/Watchful1/PushshiftDumps/tree/master
# It is modified to work with the data dump containing all comment and submission data 2005-2022
# Key differences is an improved parsing logic, as well as cleaning strings so that they are compatible with 
# DBMS such as PostgreSQL. This is done by using the .get() function, as well as removing newlines, quotes and 
# other symbols that may be confusing to JSON and / or PostgreSQL. It also has better support for testing via a max_lines
# variable.
# Be aware that fields may contain SQL injections, either by accident or malicious intent. To preserve accuracy, this script
# does not handle this, and should be considered when importing to a database.
# Be careful about memory usage when opening the resulting csv file, as it may be quite large.
# Standard fields are 	["author", "subreddit","title","score","id","created","link","selftext","retrieved"] for RS files
# and 					["author","score","created","link","body"] 											 for RC files
# If using the terminal, arguments are inputfile, outputfile, fields
# Call this as:
# python to_csv.py /path/to/input_file /path/to/output_file.csv field1,field2,field3,fieldN

from config import *
from pipeline.torrent_manager import *


def main():

    # Step 1: Initialize configurations (directories, fields, filters)
    zst_directory = directories["zst_directory"]
    
    submission_fields = parsing["submission_fields"]
    comment_fields = parsing["comment_fields"]
    filters = parsing["filters"]
    
    host = qbittorrent["host"]
    username = qbittorrent["username"]
    password = qbittorrent["password"]
    self = qbittorrent["self"]
    urls = qbittorrent["urls"]
    files_to_download = qbittorrent["torrent_files_to_download"]


    connect_to_web_ui(host, username, password)

    choose_torrents(self, urls, zst_directory, files_to_download)
    
    download_torrents(self, files_to_download, zst_directory, submission_fields, comment_fields, filters)


if __name__ == "__main__":
    main()