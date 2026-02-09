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
    'whisper_vtt_reviewed.py',
    '/Users/nraogra/Desktop/Captioning/whisperdemo/vkttt_7min/data/output',
    '-c',
    '/Users/nraogra/Desktop/Captioning/whisperdemo/vkttt_7min/data/output/data.csv',
    '-d',
    '-p', 
    '/Users/nraogra/Desktop/Captioning/whisperdemo/vkttt_7min/data/output/parent',
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
    parser.add_argument("-d", "--default", action="store_true", help="apply default metadata if no csv match")
    parser.add_argument("-u", "--update", action="store_true", help="update reviewed status of existing headers")
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
    print("\nchecking for output folder...")
    if not os.path.exists(outputDir):
        os.mkdir(outputDir)
        print(f'output folder created: \n{outputDir}')
    else:
        print(f'output folder already exists: \n{outputDir}\n')
    return outputDir

def get_header_line_count(vttfile):
    pattern = r'(\d{2}:\d{2}.\d{3} --> \d{2}:\d{2}.\d{3})'
    count = 0
    try:
        with open(vttfile, 'r', encoding='UTF-8') as input:
            for line in input:
                count += 1
                if re.match(pattern, line):
                    count -= 1
                    input.close()
                    return count
    except Exception:
        print('error')
        return -1
    return -1

def find_match(m_csv, outputName):
    with open(m_csv, 'r', encoding='UTF-8') as metadataFile:
        metadataReader = csv.reader(metadataFile)
        for row_num, row in enumerate(metadataReader):
            if row[0] == outputName:
                print(f'CSV match found for {outputName}')
                match_found = True
                match_row = row_num
                return match_row
        if not match_found:
            match_row = ''
            return match_row

def get_csv_metadata(match_row, m_csv, parent_dir):
    with open(m_csv, 'r', encoding='UTF-8') as metadataFile:
        metadataReader = csv.reader(metadataFile)
        data = list(metadataReader)
        keys = data[0]
        values = data[match_row]
        zipped = zip_longest(keys, values, fillvalue='')
        row_data = dict(zipped)
        parent = row_data["Parent File"]
        if parent != '':
            print(f'contains info: {parent}')
            print('getting parent file header...\n')
            parent_head = get_parent_header(parent, parent_dir)
            if parent_head == None:
                print('parent file has no header, getting metadata from csv only')
                status = 'no_header'
                parent_head = None
                return status, parent_head
            else:
                status = 'get_header'
                parent_head = parent_head
                return status, parent_head
#                     build_combined_header(header_data, creation_date, parentfile)
        else:
            print('no parent file found, getting metadata from csv only')
            status = 'unknown'
            parent_head = None
            return status, parent_head

def get_parent_header(parentfile, parent_dir):
    vttfile = os.path.join(parent_dir, parentfile)
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
        print('parent header found')
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
    return header_data

def build_combined_header(header_data, creation_date, parentfile):
    csv_metadata = {
        "File Creation Date": f"File Creation Date: {creation_date}", 
        "Review History": f"Local Usage Element: Review history: human-reviewed {creation_date}",
        "Reviewer": "Local Usage Element: Reviewer: ",
        "Editing Method": "Local Usage Element: Editing Method: CADET",
        "Parent File": f"Local Usage Element: Parent File: {parentfile}"
        }
    new_header = {
        key: csv_metadata.get(key, value)
        for key, value in header_data.items()
        }
    print(new_header)
    
# def get_orig_header(vttfile, line_count):
#     with open(vttfile, 'r', encoding='UTF-8') as input:
#         orig_head = [next(input) for _ in range(line_count)]
#         for i, s in enumerate(orig_head):
#             if "File Creation Date" in s:
#                 fc_date = i
#             if "Review history" in s:
#                 rev_hist = i
#     input.close()
#     return orig_head, fc_date, rev_hist

def default_header(creation_date):
    ELMP_header = ["WEBVTT\n", "Type: caption", "Language: eng",
                   "Responsible Party: US, Emory University",
                   "Media Identifier: unknown", "Originating File: unknown",
                   "File Creator: Whisper", f"File Creation Date: {creation_date}",
                   "Title: unknown", "Origin History: Created by Emory Libraries Media Preservation",
                   "Local Usage Element: Software version: unknown; Review history: unknown\n"]
    return ELMP_header

def replace_metadata(line_count, orig_head, fc_date, rev_hist, creation_date, parentfile, reviewer):
    new_fc_date = "File Creation Date: " + creation_date + "\n"
    new_rev_hist = "Review history: human-reviewed " + creation_date
    reviewer_element = "Local Usage Element: Reviewer: " + reviewer + "\n"
    edit_method = "Local Usage Element: Editing Method: CADET\n"
    parent_element = "Local Usage Element: Parent File: " + parentfile + "\n"
    rev_index = line_count - 1
    parent_index = line_count + 1
    new_head = orig_head
    new_head[fc_date] = new_fc_date
    new_head[rev_hist] = new_head[rev_hist].replace("Review history: unreviewed", new_rev_hist)
    new_head.insert(rev_index, reviewer_element)
    new_head.insert(line_count, edit_method)
    new_head.insert(parent_index, parent_element)
    return new_head

def update_metadata(reviewed_dir, m_csv, outputDir, parent_dir):
    for newvtt in glob.glob(f'{reviewed_dir}/*.vtt'):
        justName = Path(newvtt).stem
        sourceFile = os.path.basename(newvtt)
        outputName = justName + ".vtt"
        print(outputName)
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
                if match_row == '':
                    print('no match found, applying default metadata')
                    new_head = default_header(creation_date)
                else:
                    print(f'matching row: row {match_row}; getting csv metadata...')
                    status, parent_head = get_csv_metadata(match_row, m_csv, parent_dir)
#                     status, parent_head = get_parentfile(match_row, m_csv, parent_dir, creation_date)
#                     if status == 'get_header':
#                         header_data = get_header_data(parent_head)
#                         build_combined_header(header_data, creation_date, parentfile)
#                     if status == 'unknown':
#                         new_mdata = get_csv_metadata(match_row, m_csv)
#                     elif status == 'no_header':
#                         print('no parent header')
                        
#                     try:
#                         parentfile = row[match_row][1]
#                         print(parentfile)
#                     except KeyError:
#                         parentfile = 'error'
#                     new_head = ''
            #if no csv, apply default metadata
            #if csv, look for match
        else:
            print(f'header is {line_count} lines, change reviewed status?\n')
            new_head = ''

#         if m_csv != None:
#             parentfile = get_parentfile(sourceFile, m_csv)
#             print(f'parent file: {parentfile}')
#             reviewer = get_reviewer(sourceFile, m_csv)
#             print(f'reviewer: {reviewer}')
#         else:
#             parentfile = 'unknown'
#             reviewer = 'unknown'
#             print('no csv; using Emory default metadata')
#             default_header(creation_date)
#         orig_head, fc_date, rev_hist = get_orig_header(newvtt, line_count)
#         new_head = replace_metadata(line_count, orig_head, fc_date, rev_hist, creation_date, parentfile, reviewer)
#         newfile = os.path.join(outputDir, outputName)
#         with open(newvtt, 'r', encoding='UTF-8') as f_in, open(newfile, 'w', encoding='UTF-8') as f_out:
#             for item in new_head:
#                 f_out.write(f'{item}\n')
#             for _ in range(line_count):
#                 next(f_in, None)
#             shutil.copyfileobj(f_in, f_out)
#         f_in.close()
#         f_out.close()

def main(args_):
    args = setup(args_)
    reviewed_dir = args.reviewed_dir
    parent_dir = args.parentfiles
    defaultYN = args.default
    updateYN = args.update
    print('reviewed vtt directory: ',reviewed_dir)
    if args.csv != None:
        m_csv = args.csv
        print('metadata csv: ',m_csv)
    else:
        m_csv = None
        print('no metadata csv')
    outputDir = make_output_dir(reviewed_dir)
    update_metadata(reviewed_dir, m_csv, outputDir, parent_dir)
        
if __name__ == '__main__':
    main(sys.argv[1:])