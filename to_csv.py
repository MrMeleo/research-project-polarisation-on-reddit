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

from helper_methods import *
import json
import csv
import os
import time
import logging.handlers
		

# If using the program manually, write arguments here:


# Determines if a file contains comments or submissions


# How many lines should be read, lower number for faster and smaller dataset	
max_lines = float("inf")
filter_subreddits = ['ShovelKnight']



log = logging.getLogger("bot")
log.setLevel(logging.DEBUG)
log.addHandler(logging.StreamHandler())

def process_files(file_list):
	for input_file_path in file_list:
		input_filename = os.path.basename(input_file_path)
		output_filename = input_filename.replace(".zst",".csv")
		output_file_path = os.path.join(output_directory, output_filename)

		convert_to_csv(input_file_path, output_file_path, fields, filter_subreddits)



# Function to convert text file or zst file to csv
def convert_to_csv(input_file, output_file, fields, filter_subreddits):
	file_lines, bad_lines, bytes_read = 0, 0, 0
	
	try:
		with open(output_file, "w", encoding="utf-8", newline='') as output_file:
			writer = csv.writer(output_file)
			writer.writerow(fields)

			if not os.path.exists(input_file):
				log.error("Input file does not exist.")
				return
			
			if input_file.endswith(".zst"):
				read_function = read_lines_zst
			else:
				read_function = read_lines_txt

			start = time.perf_counter()
			for line in read_function(input_file):
				bytes_read += len(line)
				file_lines += 1

				if file_lines % 100000 == 0:
					log.info(f"Progress: {file_lines} lines read, {bad_lines} bad lines") 	# Updates progress to begin with

				if file_lines % 1000000 == 0: # Turn this to separate function
					end = time.perf_counter()
					elapsed_time = end-start
					
					bytes_per_line = bytes_read / file_lines 								# Calculates average bytes per line read

					bytes_remaining = file_size - bytes_read 								# Estimating remaining bytes
					lines_remaining = round(bytes_remaining / bytes_per_line) 				# Estimating remaining lines
					
					time_remaining_seconds = (lines_remaining / file_lines)*elapsed_time	# Estimating remaining time 
					time_remaining_total = time.strftime("%H:%M:%S", time.gmtime(time_remaining_seconds))

					percent_complete = (bytes_read/file_size)*100

					log.info (f"{file_lines} lines processed in {elapsed_time:.2f} seconds, {bad_lines} bad lines found, estimating {percent_complete:.1f}% finished.\n" 
						f"{bytes_read/1000000000:.1f}GB read out of {file_size/1000000000:.1f}GB.\n"
						f"{lines_remaining:,} lines remaining, estimating {time_remaining_total} time remaining")

				if file_lines >= max_lines: # Limits how much of the file is read
					break

				try:
					entry = json.loads(line)
					if filter_subreddits and entry.get("subreddit") not in filter_subreddits:
						continue # Optional filtering, if the list is empty every subreddit is written

					row = [] # CSV expects a list, not a dictonary, and the order of fields is already given
					for field in fields:
						value = entry.get(field, "")
						value = clean_value(value, file_lines, field, entry)
						row.append(value)
							
					writer.writerow(row)

				except (json.JSONDecodeError, KeyError) as e:
					log.error(f"Error reading line {file_lines +1}: {e}")
					bad_lines += 1


	except Exception as err:
		log.info(f"Error converting text to CSV: {err}")

	log.info(f"Complete: Processed {file_lines} lines, with {bad_lines} bad lines")



if __name__ == "__main__":
	
	file_directory = r"/Users/MrMeleo/Desktop/Reddit Data Files/zst files"
	output_directory = r"/Users/MrMeleo/Desktop/Reddit Data Files/csv files"
	if not os.path.exists(output_directory):
		os.makedirs(output_directory)

	file_list = [os.path.join(file_directory, file) for file in os.listdir(file_directory) if file.endswith(".zst")]
	
	file_size = 0
	for file in file_list:
		file_size += os.path.getsize(file)
	file_size = file_size * 7.5

	for input_file_path in file_list:
		input_filename = os.path.basename(input_file_path)

		submission_fields = ["subreddit","author","id","link","url"]
		comment_fields = ["author","parent_id","link_id","link"]
		fields = submission_or_comment(input_filename, return_fields=True)
		
		process_files([input_file_path])
