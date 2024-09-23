import zstandard
import json
import datetime
import logging.handlers
import os
import sys

log = logging.getLogger("bot")
log.setLevel(logging.DEBUG)


# Helping function for reading compressed ZST files
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
            buffer = ''	# Buffer in case the chunk cuts an object
            while True:
                chunk = read_and_decode(reader, 2**28, (2**29) * 2)
                if not chunk:
                    break
                lines = (buffer + chunk).split("\n")
                for line in lines[:-1]:
                    yield line 
                buffer = lines[-1]  # Keep the last incomplete line in the buffer					
            if buffer:	# Yield the last buffered line if it exists
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


# Add documentation here
def clean_value(value, file_lines, field, entry):
	# Certain fields are formated, otherwise cleaned to comply with PostgreSQL and prevent JSON injections
	if field == "created_utc":
		value = datetime.fromtimestamp(int(entry.get("created_utc", 0))).strftime("%Y-%m-%d %H:%M")
	elif field == "retrieved_on":
		value = datetime.fromtimestamp(int(entry.get("retrieved_on", 0))).strftime("%Y-%m-%d %H:%M")
	elif field == "link":
		if entry.get('permalink'):
			value = f"https://www.reddit.com{entry.get('permalink')}"
		else:
			value = f"https://www.reddit.com/r/{entry.get('subreddit', '')}/comments/{entry.get('id', '')}/"
	else:
		value = value.replace('\\', '\\\\')  						# Escape single backslashes for PostgreSQL
		value = value.replace('"', '""')    						# Escape double quotes
		value = value.replace("\n", " ").replace("\r", " ")			# Remove newlines
		try:
			parsed_value = json.loads(value)  						# Check if the field contains JSON formatted text by accident
			if isinstance(parsed_value, (list, dict)):
				value = json.dumps(parsed_value)	 				# If field contains JSON formatted text, it is turned into a string
				log.info (f"JSON found at line {file_lines,} in field {field}. Escaping.")
		except json.JSONDecodeError:
			pass 													# Not JSON, treat it as normal text
	return value

def submission_or_comment(input_filename, return_fields=False, submission_fields=None, comment_fields=None):
    is_submission = "RS" in input_filename
	
    if return_fields:
        if is_submission:
            fields = submission_fields	
        else:
            fields = comment_fields

        if not fields:
            raise ValueError ("Please enter at least one field!")
        
    return is_submission
