from pipeline.utils import submission_or_comment
from config import directories
import csv
import os
import time
import logging.handlers
from pipeline.parsing_manager import *
import glob


log = logging.getLogger("bot")
log.setLevel(logging.DEBUG)
log.addHandler(logging.StreamHandler())

def iteration_stats(file_lines, bad_lines, bytes_read, file_size, start): # Test if this method is broken, or simply not called at all
	if file_lines % 1000000 == 0:
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


def process_downloaded_file(zst_directory, submission_fields, comment_fields, filters):
	print ("Process_download_files initiated.")
	is_converted = False
	for zst_file_name in glob.glob(os.path.join(zst_directory,"**","*.zst"),recursive=True):
		if submission_or_comment(zst_file_name):
			fields = submission_fields
			print ("Fields set to submissions.")
		else:
			fields = comment_fields
			print ("Fields set to comments")
		if parse_and_convert_to_csv(zst_file_name, fields, filters):
			is_converted = True
			print ("Converted boolean set to true.")
		else:
			print (f"Conversion failed for {zst_file_name}.")
	print ("Returning conversion boolean")
	return is_converted


# Function to convert text file or zst file to csv
def parse_and_convert_to_csv(zst_file_name, fields, filters):
	print (f"Parse and convert method initialised for {zst_file_name}.")
	file_size, file_lines, bad_lines, bytes_read = 0, 0, 0, 0

	csv_file_name = os.path.basename(zst_file_name).replace(".zst",".csv")
	csv_directory = os.path.join(directories["csv_directory"],csv_file_name)

	try:
		with open(csv_directory, "w", encoding="utf-8", newline='') as csv_file:
			writer = csv.writer(csv_file)
			writer.writerow(fields)

			if not os.path.exists(zst_file_name):
				log.error("zst file not found..")
				return
			
			if zst_file_name.endswith(".zst"):
				read_function = read_lines_zst
			else:
				read_function = read_lines_txt
			
			start = time.perf_counter()
			for line in read_function(zst_file_name):
				bytes_read += len(line)
				file_lines += 1
				iteration_stats(file_lines, bad_lines, bytes_read, file_size, start)
			
				# if file_lines >= limit_lines_read: # Limits how much of the file is read
				# 	break
				
				if filter_subreddits(line, filters): # If a subreddit is not in the filter, it reads the next line instead
					continue

				row = [] # CSV expects a list, not a dictonary, and the order of fields is already given
				for field in fields:
					value = (field, "")
					value = clean_value(value, line, file_lines, field)
					row.append(value)
				writer.writerow(row)
			log.info(f"Conversion for {zst_file_name} complete: Processed {file_lines} lines, with {bad_lines} bad lines")
			return True
	except Exception as err:
		log.info(f"Error converting zst to csv: {err}")
		return False
		
	


