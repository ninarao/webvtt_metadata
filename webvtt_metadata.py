#!/usr/bin/env python3

import os
import sys
import glob
from pathlib import Path
import csv
import platform
import datetime
import re
import argparse
import shutil
from itertools import zip_longest

sys.argv = [
#     'webvtt_metadata.py',
#     '/Users/nraogra/Desktop/iPres2025/WebVTT_metadata/webvtt_files',
#     '-c',
#     '/Users/nraogra/Desktop/iPres2025/WebVTT_metadata/webvtt_metadata.csv',
#     '-r',
#     '-e'
#     '-p', 
#     '/Users/nraogra/Desktop/Captioning/whisperdemo/vkttt_7min/data/output/parent',
    ]

def valid_directory(path_string):
    if not os.path.isdir(path_string):
        raise argparse.ArgumentTypeError(f"'{path_string}' is not a valid directory.")
    return path_string

def valid_csv(path_csv):
    if not os.path.isfile(path_csv):
        raise argparse.ArgumentTypeError(f"'{path_csv}' is not a valid csv file.")
    if not path_csv.endswith(".csv"):
        raise argparse.ArgumentTypeError(f"'{path_csv}' is not a valid csv file.")
    else:
        return path_csv
    
def setup(args_):
    parser = argparse.ArgumentParser()
    parser.add_argument("reviewed_dir", type=valid_directory, help="Directory of reviewed vtt files")
    parser.add_argument("-c", "--csv", type=valid_csv, help="Metadata CSV")
    parser.add_argument("-e", "--emorydefault", action="store_true", help="use Emory default metadata set for empty fields")
    parser.add_argument("-r", "--reviewed", action="store_true", help="creates/updates FADGI header for reviewed files")
    parser.add_argument("-p", "--parentfiles", type=valid_directory, help="Directory of parent vtt files")
    args = parser.parse_args(args_)
    return args

def ask_yes_no(question):
    '''
    Returns Y or N. The question variable is just a string.
    '''
    answer = ''
    print(' - \n', question, '\n', 'enter Y or N')
    while answer not in ('Y', 'y', 'N', 'n'):
        answer = input()
        if answer not in ('Y', 'y', 'N', 'n'):
            print(' - Incorrect input. Please enter Y or N')
        if answer in ('Y', 'y'):
            return 'Y'
        elif answer in ('N,' 'n'):
            return 'N'

def make_output_dir(reviewed_dir):
    outputDir = os.path.join(reviewed_dir, 'metadata_updated')
    print("checking for output folder...")
    if not os.path.exists(outputDir):
        os.mkdir(outputDir)
        print(f'\toutput folder created: \n\t{outputDir}')
    else:
        print(f'\toutput folder already exists: \n\t{outputDir}')
    return outputDir

def get_header_line_count(vttfile):
    pattern = r'(\d{2}:\d{2}.\d{3} --> )'
    count = 0
    try:
        with open(vttfile, 'r', encoding='UTF-8') as input:
            for line in input:
                count += 1
                if re.search(pattern, line):
                    count -= 1
                    input.close()
                    return count
    except Exception:
        print('line count error')
        return -1
    return -1

def find_match(m_csv, outputName):
    with open(m_csv, 'r', encoding='UTF-8') as metadataFile:
        metadataReader = csv.reader(metadataFile)
        for row_num, row in enumerate(metadataReader):
            if row[0] == outputName:
#                 print(f'csv match found for {outputName}')
                match_found = True
                match_row = row_num
                return match_row
            else:
                match_found = False
        if not match_found:
            match_row = -1
            return match_row

def get_csv_metadata(match_row, m_csv):
    with open(m_csv, 'r', encoding='UTF-8') as metadataFile:
        metadataReader = csv.reader(metadataFile)
        data = list(metadataReader)
        keys = data[0]
        values = data[match_row]
        zipped = zip_longest(keys, values, fillvalue='')
        csv_row_data = dict(zipped)
        if csv_row_data.get("Parent File"):
            parentfile = csv_row_data["Parent File"]
            return csv_row_data, parentfile
        else:
            parentfile = ''
            return csv_row_data, parentfile
        
def assess_parent_header(parentfile, parent_dir):
    if parent_dir is None:
        print('no directory for parent files')
        parent_head = None
        return parent_head
    vttfile = os.path.join(parent_dir, parentfile)
    if not os.path.isfile(vttfile):
        print(f'file does not exist: {vttfile}')
        parent_head = None
        return parent_head
    else:
        line_count = get_header_line_count(vttfile)
        if line_count == -1:
            print('timestamps not found in parent file')
            parent_head = None
            return parent_head
        elif line_count == 2:
            print('no FADGI header detected in parent file')
            parent_head = None
            return parent_head
        else:
            print('FADGI header found')
            with open(vttfile, 'r', encoding='UTF-8') as input:
                parent_head = [next(input) for _ in range(line_count)]
            input.close()
            return parent_head

def get_header_data(parent_head):
    keys_list = ["Header", "Type", "Language", "Responsible Party",
                 "Media Identifier", "Originating File", "File Creator",
                 "File Creation Date", "Title", "Origin History",
                 "Software Version", "Review History", "Reviewer",
                 "Editing Method", "Parent File"]
    parent_head = [x for x in parent_head if x != '\n']
    values_list = parent_head
    zipped = zip_longest(keys_list, values_list, fillvalue='')
    header_data = dict(zipped)
    old_version = '; Review history: unreviewed'
    for key, value in header_data.items():
        if isinstance(value, str):
            header_data[key] = value.replace(old_version, '')
            header_data.update({"Review History": "Local Usage Element: Review history: unreviewed"})
    return header_data

def build_combined_header(parent_header_data, csv_row_data, creation_date, reviewed, nodefault):
    default_head = default_header(creation_date)
    if reviewed == True:
        new_default = default_update(creation_date)
        default_head = default_head | new_default
    localkeys = r'^Local Usage Element \d+ Key'
    keymatches = {}
    localvals = r'^Local Usage Element \d+ Value'
    valmatches = {}
    for key, value in csv_row_data.items():
        if re.search(localkeys, key):
            keymatches[key] = value
            to_rem = " Key"
            newkeys = {key.replace(to_rem, ''): value for key, value in keymatches.items()}
    for key, value in csv_row_data.items():
        if re.search(localvals, key):
            valmatches[key] = value
            to_rem = " Value"
            newvals = {key.replace(to_rem, ''): value for key, value in valmatches.items()}
    if newkeys and newvals:
        locals = {newkeys[key]: newvals[key] for key in newkeys if key in newvals}
    if locals:
        for key, value in locals.items():
            locals[key] = "Local Usage Element: " + key + " " + value
    easy_keysie = ["Language", "Type", "Responsible Party", "Originating File",
                   "File Creator", "Title", "Origin History"]
    for key in easy_keysie:
        if key in csv_row_data:
            csv_row_data[key] = key + ": " + csv_row_data[key]
    if csv_row_data.get("Media Identifier") and csv_row_data.get("Media Identifier Type"):
        csv_row_data["Media Identifier"] = "Media Identifier: " + csv_row_data["Media Identifier"] + ", " + csv_row_data["Media Identifier Type"]
    elif csv_row_data.get("Media Identifier") and not csv_row_data.get("Media Identifier Type"):
        csv_row_data["Media Identifier"] = "Media Identifier: " + csv_row_data["Media Identifier"]
    if csv_row_data.get("File Creation Date"):
        csv_row_data["File Creation Date"] = "File Creation Date: " + csv_row_data["File Creation Date"]
    else:
        csv_row_data["File Creation Date"] = "File Creation Date: " + creation_date
    if csv_row_data.get("Software Version"):
        csv_row_data["Software Version"] = "Local Usage Element: Software version: " + csv_row_data["Software Version"]
    if csv_row_data.get("Review History"):
        csv_row_data["Review History"] = "Local Usage Element: Review history: " + csv_row_data["Review History"]
    elif reviewed == False and nodefault == False:
        csv_row_data["Review History"] = "Local Usage Element: Review history: unreviewed"
    elif reviewed == True and nodefault == False:
        csv_row_data["Review History"] = "Local Usage Element: Review history: human-reviewed"
    if csv_row_data.get("Reviewer"):
        csv_row_data["Reviewer"] = "Local Usage Element: Reviewer: " + csv_row_data["Reviewer"]
    if csv_row_data.get("Parent File"):
        csv_row_data["Parent File"] = "Local Usage Element: Parent File: " + csv_row_data["Parent File"]
    keys_to_keep = ["Language", "Type", "Responsible Party", "Media Identifier", 
                   "Originating File", "File Creator", "Title", "Origin History",
                    "File Creation Date", "Software Version", "Review History",
                    "Reviewer", "Parent File"]
    csv_keys_kept = {k:v for k, v in csv_row_data.items() if k in keys_to_keep}
    csv_filtered = {k:v for (k, v) in csv_keys_kept.items() if v}
    if locals:
        csv_filtered.update(locals)
    if nodefault == False:
        if parent_header_data != '':
            parent_filtered = {k:v for (k, v) in parent_header_data.items() if v}
            combined = default_head | parent_filtered
            combined = combined | csv_filtered
            return combined
        else:
            combined = default_head | csv_filtered
            return combined
    else:
        if parent_header_data != '':
            parent_filtered = {k:v for (k, v) in parent_header_data.items() if v}
            combined = parent_filtered | csv_filtered
            return combined
        else:
            combined = csv_filtered
            return combined

def update_fadgi_header(vtt_header_data, creation_date, nodefault):
    default_head = default_update(creation_date)
    vtt_filtered = {k:v for (k, v) in vtt_header_data.items() if v}
    if nodefault == False:
        combined = vtt_filtered | default_head
        return combined
    else:
        combined = vtt_filtered
        return combined

def default_header(creation_date):
    ELMP_header = {'Header': "WEBVTT\n", 'Type': "Type: caption", 'Language': "Language: eng",
                   'Responsible Party': "Responsible Party: US, Emory University",
                   'Media Identifier': "Media Identifier: unknown",
                   'Originating File': "Originating File: unknown",
                   'File Creator': "File Creator: Whisper",
                   'File Creation Date': f"File Creation Date: {creation_date}",
                   'Title': "Title: unknown",
                   'Origin History': "Origin History: Created by Emory Libraries Media Preservation",
                   'Software Version': "Local Usage Element: Software version: unknown",
                   'Review History': "Local Usage Element: Review history: unreviewed",
                   'Reviewer': 'Local Usage Element: Reviewer: none',
                   'Editing Method': 'Local Usage Element: Editing Method: none',
                   'Parent File': 'Local Usage Element: Parent File: none'
                   }
    return ELMP_header

def default_update(creation_date):
    ELMP_update = {'File Creation Date': f"File Creation Date: {creation_date}",
                   'Review History': "Local Usage Element: Review history: human-reviewed",
                   'Reviewer': 'Local Usage Element: Reviewer: unknown',
                   'Editing Method': 'Local Usage Element: Editing Method: unknown',
                   'Parent File': 'Local Usage Element: Parent File: unknown'
                   }
    return ELMP_update

def update_metadata(reviewed_dir, m_csv, outputDir, parent_dir, reviewed, nodefault):
    for newvtt in glob.glob(f'{reviewed_dir}/*.vtt'):
        justName = Path(newvtt).stem
        outputName = justName + ".vtt"
        print(f'\n{outputName}')
        if platform.system() == 'Windows':
            c_timestamp = os.path.getctime(newvtt)
            datestamp = datetime.datetime.fromtimestamp(c_timestamp)
        else:
            stat = os.stat(newvtt)
            try:
                timestamp = stat.st_birthtime
                datestamp = datetime.datetime.fromtimestamp(timestamp)
            except AttributeError:
                timestamp = stat.st_mtime
                datestamp = datetime.datetime.fromtimestamp(timestamp)
        creation_date = datestamp.strftime("%Y-%m-%d")
        line_count = get_header_line_count(newvtt)
        if line_count == -1:
            print('timestamps not found in file, skipping to next file\n')
            continue
        elif line_count == 2:
            print('no FADGI header detected')
            if m_csv != None:
                print('checking csv for match...')
                match_row = find_match(m_csv, outputName)
                if match_row == -1 and nodefault == False:
                    if reviewed == False:
                        print('no match found, applying default unreviewed metadata')
                        combined = default_header(creation_date)
                    else:
                        print('no match found, applying default reviewed metadata')
                        default_head = default_header(creation_date)
                        new_default = default_update(creation_date)
                        combined = default_head | new_default
                elif match_row == -1 and nodefault == True:
                    print('no match found and default metadata is not being applied, skipping to next file')
                    continue
                elif match_row != -1 and nodefault == False:
                    print(f'matching row found for {outputName}: row {match_row}; getting csv metadata...')
                    csv_row_data, parentfile = get_csv_metadata(match_row, m_csv)
                    if parentfile != '':
                        print(f'contains parent info: {parentfile}, getting parent file header...')
                        parent_head = assess_parent_header(parentfile, parent_dir)
                        if parent_head == None:
                            print('no parent file FADGI header')
                            parent_header_data = ''
                            combined = build_combined_header(parent_header_data, csv_row_data, creation_date, reviewed, nodefault)
                        else:
                            print('combining parent file header and metadata from csv...')
                            parent_header_data = get_header_data(parent_head)
                            combined = build_combined_header(parent_header_data, csv_row_data, creation_date, reviewed, nodefault)
                    else:
                        parent_header_data = ''
                        combined = build_combined_header(parent_header_data, csv_row_data, creation_date, reviewed, nodefault)
                else:
                    print(f'matching row found for {outputName}: row {match_row}; getting csv metadata...')
                    csv_row_data, parentfile = get_csv_metadata(match_row, m_csv)
                    if parentfile != '':
                        print(f'contains parent info: {parentfile}, getting parent file header...')
                        parent_head = assess_parent_header(parentfile, parent_dir)
                        if parent_head == None:
                            print('no parent file FADGI header')
                            parent_header_data = ''
                            combined = build_combined_header(parent_header_data, csv_row_data, creation_date, reviewed, nodefault)
                        else:
                            print('combining parent file header and metadata from csv...')
                            parent_header_data = get_header_data(parent_head)
                            combined = build_combined_header(parent_header_data, csv_row_data, creation_date, reviewed, nodefault)
                    else:
                        parent_header_data = ''
                        combined = build_combined_header(parent_header_data, csv_row_data, creation_date, reviewed, nodefault)
            else:
                if nodefault == False:
                    if reviewed == False:
                        print('no csv and no header, using default unreviewed metadata')
                        combined = default_header(creation_date)
                    else:
                        print('no csv and no header, using default reviewed metadata')
                        default_head = default_header(creation_date)
                        new_default = default_update(creation_date)
                        combined = default_head | new_default
                else:
                    print('no csv, no header, and default metadata is not being applied, skipping to next file')
                    continue
        else:
            print(f'FADGI header detected: {line_count} lines')
            if reviewed == False:
                print('no update, skipping to next file\n')
                continue
            else:
                print('changing review history to reviewed')
                vtt_head = assess_parent_header(newvtt, reviewed_dir)
                vtt_header_data = get_header_data(vtt_head)
                if m_csv != None:
                    print('checking csv for match...')
                    match_row = find_match(m_csv, outputName)
                    if nodefault == False:
                        if match_row == '':
                            print('no match found, applying default reviewed metadata')
                            combined = update_fadgi_header(vtt_header_data, creation_date, nodefault)
                        else:
                            print(f'matching row found for {outputName}: row {match_row}; getting csv metadata...')
                            csv_row_data, parentfile = get_csv_metadata(match_row, m_csv)
                            combined = build_combined_header(vtt_header_data, csv_row_data, creation_date, reviewed, nodefault)
                    else:
                        if match_row == '':
                            print('no match found and default metadata is not being applied, skipping to next file')
                            continue
                        else:
                            print(f'matching row found for {outputName}: row {match_row}; getting csv metadata...')
                            csv_row_data, parentfile = get_csv_metadata(match_row, m_csv)
                            combined = build_combined_header(vtt_header_data, csv_row_data, creation_date, reviewed, nodefault)
                elif m_csv == None and nodefault == False:
                    print('no csv, using default reviewed metadata')
                    combined = update_fadgi_header(vtt_header_data, creation_date, nodefault)
                else:
                    print('no csv and default metadata is not being applied, skipping to next file')
                    continue

        newfile = os.path.join(outputDir, outputName)
        removed_value = combined.pop('File', 'Key not found')
        newheader = list(combined.values())
        to_remove = "\n"
        newheader = [item.replace(to_remove, "") for item in newheader]
        to_add = "\n"
        newheader[0] = newheader[0] + to_add
        newheader[-1] = newheader[-1] + to_add
        with open(newvtt, 'r', encoding='UTF-8') as f_in, open(newfile, 'w', encoding='UTF-8') as f_out:
            for item in newheader:
                f_out.write(f'{item}\n')
            for _ in range(line_count):
                next(f_in, None)
            shutil.copyfileobj(f_in, f_out)
        f_in.close()
        f_out.close()

def main(args_):
    args = setup(args_)
    reviewed_dir = args.reviewed_dir
    parent_dir = args.parentfiles
    emorydefault = args.emorydefault
    reviewed = args.reviewed
    print('*** webvtt metadata - settings chosen: ***')
    print(f'reviewed vtt directory:\n\t{reviewed_dir}')
    if args.csv != None:
        m_csv = args.csv
        print(f'metadata csv:\n\t{m_csv}')
    else:
        m_csv = None
        print('no metadata csv')
    if parent_dir != None:
        print(f'directory of parent files:\n\t{parent_dir}')
    else:
        print(f'directory of parent files:\n\tno parent file directory provided')
    if reviewed == True:
        print(f'webvtt files are: reviewed\n\tscript will create/update reviewed FADGI headers')
    else:
        print(f'webvtt files are: unreviewed\n\tscript will create initial FADGI headers\n\tand skip files with existing FADGI headers')
    if emorydefault == True:
        print('default metadata:\n\tscript will use Emory default metadata set for empty fields')
        nodefault = False
    else:
        print('default metadata:\n\tscript will not use Emory default metadata set for empty fields')
        nodefault = True
    outputDir = make_output_dir(reviewed_dir)
    proceed = ask_yes_no('proceed with these settings?')
    if proceed =='Y':
        update_metadata(reviewed_dir, m_csv, outputDir, parent_dir, reviewed, nodefault)
    else:
        print('exiting. goodbye!')
        sys.exit()
        
if __name__ == '__main__':
    main(sys.argv[1:])
