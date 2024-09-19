# This script is based on the to_csv by https://github.com/Watchful1/PushshiftDumps/tree/master
# It is modified to work with the data dump containing all comment and submission data 2005-2022
# Key differences is an improved parsing logic, as well as cleaning strings so that they are compatible with 
# DBMS such as PostgreSQL. This is done by using the .get() function, as well as removing newlines, quotes and 
# other symbols that may be confusing to JSON and / or PostgreSQL. It also has better support for testing via a max_lines
# variable.
# The list of fields in the dataset is as follows:
# Be careful about memory usage when opening the resulting csv file, as it may be quite large.

# If using the terminal, arguments are inputfile, outputfile, fields
# Call this as:
# python to_csv.py /path/to/input_file /path/to/output_file.csv field1,field2,field3,fieldN

import zstandard
import json
import sys
import csv
from datetime import datetime
import logging.handlers
		

# If using the program manually, write arguments here:
input_file_path = r"/Users/MrMeleo/Desktop/untitled folder/RS_2013-01.zst"
output_file_path = r"/Users/MrMeleo/Desktop/untitled folder/RS_2013-01_03.csv"

# Determines if a file contains comments or submissions
is_submission = "RS" in input_file_path
if is_submission:
	fields = ["author", "subreddit","title","score","created","link","text","url"]	
else:
	fields = ["author","score","created","link","body"]
# How many lines should be read, lower number for faster and smaller dataset	
max_lines = 10000


log = logging.getLogger("bot")
log.setLevel(logging.DEBUG)
log.addHandler(logging.StreamHandler())


def read_and_decode(reader, chunk_size, max_window_size, previous_chunk=None, bytes_read=0):
	chunk = reader.read(chunk_size)
	bytes_read += chunk_size
	if previous_chunk is not None:
		chunk = previous_chunk + chunk
	try:
		return chunk.decode()
	except UnicodeDecodeError:
		if bytes_read > max_window_size:
			raise UnicodeError(f"Unable to decode frame after reading {bytes_read:,} bytes")
		return read_and_decode(reader, chunk_size, max_window_size, chunk, bytes_read)

# Function to read ZST files
def read_lines_zst(file_name):
    try:    
        with open(file_name, 'rb') as file_handle:
            reader = zstandard.ZstdDecompressor(max_window_size=2**31).stream_reader(file_handle)
            buffer = ''
            while True:
                chunk = read_and_decode(reader, 2**27, (2**29) * 2)
                if not chunk:
                    break
                lines = (buffer + chunk).split("\n")

                for line in lines[:-1]:
                    yield line  # Yield only the line

                buffer = lines[-1]  # Keep the last incomplete line in the buffer

            # Yield the last buffered line if it exists
            if buffer:
                yield buffer
    except Exception as e:
        log.error(f"Error reading zst file: {e}")




# Function to read text files 
def read_lines_txt(file_name):
	try:
		with open(file_name, 'r', encoding='utf-8') as file_handle:
			for line in file_handle:
				yield line.strip()
	except Exception as e:
		log.error(f"Error reading text file: {e}")


def remove_newlines(value):
	return value.replace("\n"," ").replace("\r"," ")


def fix_existing_quotes(value):
	if isinstance(value, str):
		value = value.replace('"','""')
		if '\n' in value or '\r' in value:
			value = f'"{value}"'
	return value


# Function to convert text file or zst file to csv
def convert_to_csv(input_file, output_file, fields):
	file_lines, bad_lines = 0, 0

	try:
		with open(output_file, "w", encoding="utf-8", newline='') as output_file:
			writer = csv.writer(output_file)
			writer.writerow(fields)

			if input_file.endswith(".zst"):
				read_function = read_lines_zst
			else:
				read_function = read_lines_txt
			for line in read_function(input_file):
				if file_lines >= max_lines:
					break

				try:
					object = json.loads(line)
					output_object = {}

					for field in fields:
						if field == "created":
							value = datetime.fromtimestamp(int(object.get("created_utc", 0))).strftime("%Y-%m-%d %H:%M")
						elif field == "link":
							if "permalink" in object:
								value = f"https://www.reddit.com{object['permalink']}"
							else:
								value = f"https://www.reddit.com/r/{object.get('subreddit', '')}/comments/{object.get('id', '')}/"
						elif field == "author":
							value = f"u/{object.get('author', '[deleted]')}"
						elif field == "text":
							value = remove_newlines(object.get('selftext', ""))
						elif field == "title":
							value = remove_newlines(object.get('title', ''))
						elif field == "score":
							value = object.get('score', 0)
						elif field == "subreddit":
							value = object.get('subreddit', "")
						elif field == "url":
							value = remove_newlines(object.get('url', ""))
						else: 
							value = object.get(field, "")

						output_object[field] = value

					for key, value in object.items():
						if key not in output_object:
							output_object[key] = value

					row = [output_object.get(field, "") for field in fields]
					writer.writerow(row)

					file_lines += 1


				except json.JSONDecodeError as e:
					log.error(f"JSONDecodeError: {e} at line: {line}")
					bad_lines += 1
				except KeyError as e:
					log.error(f"KeyError: {e} at line: {line}")
					bad_lines += 1


				if file_lines % 100000 == 0:
					log.info(f"Progress: {file_lines} lines read, {bad_lines} bad lines")

	except Exception as err:
		log.info(f"Error converting text to CSV: {err}")

	log.info(f"Complete: Processed {file_lines} lines, with {bad_lines} bad lines")


if __name__ == "__main__":
	if len(sys.argv) >= 3:
		input_file_path = sys.argv[1]
		output_file_path = sys.argv[2]
		fields = sys.argv[3].split(",") if len(sys.argv) > 3 else []
	else:
		input_file_path = input_file_path
		output_file_path = output_file_path
		fields = fields

	convert_to_csv(input_file_path, output_file_path, fields)
