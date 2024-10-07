import qbittorrentapi as qbt
import time
from pipeline.conversion_manager import *


torrent_hash = None

def connect_to_web_ui(host, username, password):
    try:
        qbt.Client(host=host,username=username,password=password)
        print("Logged in to Web UI.")
    except qbt.LoginFailed as error:
        print (f"Failed to log in to Web UI: {error}")


def choose_torrents(self, urls, zst_directory, files_to_download, max_wait_time=60):
    qbt.Client.torrents_add(self,urls=urls, save_path=zst_directory,content_layout="NoSubFolder", seeding_time_limit=0,
                            stop_condition="FilesChecked", use_auto_torrent_management=False, is_sequential_download=True)
    print ("Starting to load files.")
    start_time = time.time()
    while True:
        torrents = qbt.Client.torrents_info(self)
        if torrents:
            global torrent_hash
            torrent_hash = torrents[0].hash
            files = qbt.Client.torrents_files(self, torrent_hash=torrent_hash)
            if files:
                print ("Files loaded!")
                break
        if time.time()-start_time > max_wait_time:
            raise TimeoutError("File data took too long to load.")
        time.sleep(2)

    for file_index in range(len(files)):
        priority = 1 if file_index in files_to_download else 0
        qbt.Client.torrents_file_priority(self, torrent_hash=torrent_hash, file_ids=[file_index], priority=priority)
    
    print ("Setting download priorities...")
    while True:
        current_file_priority = [file["priority"] for file in qbt.Client.torrents_files(self, torrent_hash=torrent_hash)]
        expected_file_priority = [1 if file in files_to_download else 0 for file in range(len(files))]
        if current_file_priority == expected_file_priority:
            break
        if time.time()-start_time > max_wait_time:
            raise TimeoutError("File priorities took too long to apply.")
        time.sleep(2)

    return torrent_hash


def download_torrents(self, files_to_download, zst_directory, submission_fields, comment_fields, filters):
    global torrent_hash
    print ("Now downloading files.")
    qbt.Client.torrents_resume(self, torrent_hashes=torrent_hash)
  
    while qbt.Client.torrents_count(self) > 0:
        files_info = qbt.Client.torrents_files(self, torrent_hash=torrent_hash)

        if all(files_info[file_index]["progress"] == 1.0 for file_index in files_to_download):
            print ("All files downloaded.")
            time.sleep(2)
    
            if process_downloaded_file(zst_directory, submission_fields, comment_fields, filters):
                try:
                    qbt.Client.torrents_delete(self, delete_files=True, torrent_hashes="all")
                    time.sleep(3)
                    print("All files successfully converted and deleted.")

                except Exception as e:
                     # Handle any exceptions that occur during conversion or deletion
                    print(f"Error deleting file: {e}")
            else:
                print ("No succesfull conversions.")
            break
        else:
            print("Files still downloading...")
            time.sleep(5)
