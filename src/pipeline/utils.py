import json
from collections import Counter


def submission_or_comment(zst_file):
    is_submission = "RS" in zst_file
    return is_submission


def json_reader(input_file, check_field_appearance_count=True):
    if check_field_appearance_count:
        field_counter = Counter()
    else:
        distinct_fields = set()
    with open (input_file, "r", encoding="utf-8") as json_data:
        for line in enumerate(json_data,start=1):
            data = json.loads(line.strip())
            if isinstance (data, dict):
                if check_field_appearance_count:
                    field_counter.update(data.keys())
                else:
                    distinct_fields.update(data.keys())
    if check_field_appearance_count:
        print ("Field counts:")
        for field, count in field_counter.items():
            print (f"{field}: {count} occurences.")
    else:
        print ("Distinct fields: ", str(distinct_fields).replace("'",""))




