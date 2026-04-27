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
    'webvtt_metadata.py',
    '/Users/nraogra/Desktop/txt-test',
    '-c',
    '/Users/nraogra/Desktop/txt-test/webvtt_metadata.csv',
#     '-r',
#     '-e',
    '-p', 
    '/Users/nraogra/Desktop/txt-test',
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

def get_header_line_count(vttfile, pattern):
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
        parentkey = [k for k, v in csv_row_data.items() if v.casefold() == "parent file".casefold()]
        parentval = [item.replace("Key", "Value") for item in parentkey]
        del parentval[1:]
        pval_str = ''.join(parentval)
        parentfile = csv_row_data.get(pval_str, "")
        return csv_row_data, parentfile
        
def assess_parent_header(parentfile, parent_dir, pattern):
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
        line_count = get_header_line_count(vttfile, pattern)
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
    parent_head = [x for x in parent_head if x != '\n']
    values_list = parent_head
    if parent_head[0] == 'WEBVTT\n':
        parent_head[0] = 'Header: WEBVTT\n'
    indices = [i for i, s in enumerate(parent_head) if "Local Usage Element" in s]
    if indices:
        locals = []
        for i in indices:
            locals.append(parent_head[i])
            new_locals = [item.replace("Local Usage Element: ", "") for item in locals]
        string = '; '.join(new_locals)
        new_string = string.replace("\n", "")
        new_string = new_string.replace("Software version:", "[software version]")
        new_string = new_string.replace("Review History:", "[review history]")
        header_locals = new_string.replace("Review history:", "[review history]")
        local_string = "Local Usage Element: " + header_locals
        for index in sorted(indices, reverse=True):
            del parent_head[index]
    else:
        header_locals = ""
    header_keys = dict(item.split(':', 1) for item in parent_head)
    header_keys = list({k.strip(): v.strip() for k, v in header_keys.items()})
    header_data = dict(zip(header_keys, values_list))
    header_data["Local Usage Element"] = local_string
    header_data.update({'Header': 'WEBVTT\n'})
    return header_data, header_locals

def build_combined_header(parent_header_data, header_locals, csv_row_data, creation_date, reviewed, nodefault):
    keys = ['Header', 'Type', 'Language', 'Responsible Party', 'Media Identifier',
            'Originating File', 'File Creator', 'File Creation Date', 'Title',
            'Origin History', 'Local Usage Element']
    base_dict = dict.fromkeys(keys, "")
    default_head = default_header(creation_date)
    if reviewed == True:
        new_default = default_update()
        default_head = default_head | new_default
    csv_row_data = {k:v for k, v in csv_row_data.items() if v != ''}
    localkeys = r'^Local Usage Element \d+ Key'
    keymatches = {}
    localvals = r'^Local Usage Element \d+ Value'
    valmatches = {}
    for key, value in csv_row_data.items():
        if re.search(localkeys, key):
            keymatches[key] = value
    for key, value in csv_row_data.items():
        if re.search(localvals, key):
            valmatches[key] = value
    if keymatches and valmatches:
        keyslist = list(keymatches.values())
        keyslist_formatted = ["[" + item + "]" for item in keyslist]
        valslist = list(valmatches.values())
        locals = dict(zip(keyslist_formatted, valslist))
        local_list = [f"{k} {v}" for k, v in locals.items()]
        local_string = "; ".join(map(str, local_list))
        locals = True
    else:
        locals = False
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
    keys_to_keep = ["Language", "Type", "Responsible Party", "Media Identifier", 
                   "Originating File", "File Creator", "Title", "Origin History",
                    "File Creation Date"]
    csv_keys_kept = {k:v for k, v in csv_row_data.items() if k in keys_to_keep}
    csv_filtered = {k:v for (k, v) in csv_keys_kept.items() if v}
    if header_locals != "" and locals == True:
        csv_filtered["Local Usage Element"] = "Local Usage Element: " + header_locals + "; " + local_string
    elif header_locals == "" and locals == True:
        csv_filtered["Local Usage Element"] = "Local Usage Element: " + local_string
    elif header_locals != "" and locals == False:
        csv_filtered["Local Usage Element"] = "Local Usage Element: " + header_locals
    if creation_date == "no_update":
        csv_filtered.pop("File Creation Date", None)
    if nodefault == False:
        default = base_dict | default_head
        if parent_header_data != '':
            parent_filtered = {k:v for (k, v) in parent_header_data.items() if v}
            combined = default | parent_filtered
            combined = combined | csv_filtered
            return combined
        else:
            combined = default | csv_filtered
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
    keys = ['Header', 'Type', 'Language', 'Responsible Party', 'Media Identifier',
            'Originating File', 'File Creator', 'File Creation Date', 'Title',
            'Origin History', 'Local Usage Element']
    base_dict = dict.fromkeys(keys, "")
    default_hed = default_header(creation_date)
    if creation_date == "no_update":
        default_hed.pop("File Creation Date", None)
    default_up = default_update()
    default_head = default_hed | default_up
    vtt_filtered = {k:v for (k, v) in vtt_header_data.items() if v}
    vtt_filtered.update({'Header': 'WEBVTT\n'})
    vtt_filtered['Local Usage Element'] = vtt_filtered['Local Usage Element'].replace("unreviewed", "human-reviewed")
    if nodefault == False:
        default = base_dict | default_head
        combined = default | vtt_filtered
        return combined
    else:
        combined = vtt_filtered
        return combined

def change_reviewed(vtt_header_data):
    local = vtt_header_data.get("Local Usage Element", "")
    review = "review history"
    if review.casefold() in local.casefold():
        new_local = local.replace("unreviewed", "human-reviewed")
        vtt_header_data['Local Usage Element'] = new_local
    return vtt_header_data

def default_header(creation_date):
    ELMP_header = {'Header': "WEBVTT\n", 'Type': "Type: caption", 'Language': "Language: eng",
                   'Responsible Party': "Responsible Party: US, Emory University",
                   'Media Identifier': "Media Identifier: unknown",
                   'Originating File': "Originating File: unknown",
                   'File Creator': "File Creator: Whisper",
                   'File Creation Date': f"File Creation Date: {creation_date}",
                   'Title': "Title: unknown",
                   'Origin History': "Origin History: Created by Emory Libraries Media Preservation",
                   'Local Usage Element': "Local Usage Element: [review history] unreviewed; [parent file] none"
                   }
    return ELMP_header

def default_update():
    ELMP_update = {
                   'Local Usage Element': "Local Usage Element: [review history] human-reviewed; [reviewer] unknown; " \
                   "[editing method] unknown; [parent file] unknown"
                   }
    return ELMP_update

def write_new_header(combined, outputDir, outputName, newvtt, line_count):
    if 'Header' not in combined:
        combined = {**{'Header': 'WEBVTT\n'}, **combined}
    newfile = os.path.join(outputDir, outputName)
    removed_value = combined.pop('File', 'Key not found')
    newheader = list(combined.values())
    newheader = [x for x in newheader if x != '']
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

def copy_metadata_to_txt(outputName, txtfile, m_csv, parent_dir, outputDir):
    print(f'\n{outputName}')
    pattern = r'^Type:'
    line_count = get_header_line_count(txtfile, pattern)
    if line_count == -1:
        print('header not found in file, checking for csv match')
        match_row = find_match(m_csv, outputName)
        if match_row == -1:
            print('no match found, skipping to next file')
        else:
            print(f'matching row found for {outputName}: row {match_row}; checking for parent file...')
            csv_row_data, parentfile = get_csv_metadata(match_row, m_csv)
            if parentfile != '':
                print(f'parent file: {parentfile}, checking for parent file header...')
                pattern = r'(\d{2}:\d{2}.\d{3} --> )'
                parent_head = assess_parent_header(parentfile, parent_dir, pattern)
                if parent_head == None:
                    print('no parent file FADGI header, skipping to next file')
                else:
                    print('getting parent file header metadata')
                    header_locals = ''
                    parent_header_data, header_locals = get_header_data(parent_head)
                    parent_header_data["Type"] = "Type: transcript\n"
                    write_new_header(parent_header_data, outputDir, outputName, txtfile, line_count)
            else:
                print('no parent file, skipping to next file')
    else:
        print('header detected in file, skipping to next file')

def update_metadata(reviewed_dir, m_csv, outputDir, parent_dir, reviewed, nodefault):
    ext = ['.vtt', '.txt']
    for newvtt in glob.glob(f'{reviewed_dir}/*{ext}'):
        if os.path.isfile(newvtt):
            justName = Path(newvtt).stem
            fileExt = Path(newvtt).suffix
            if fileExt == '.vtt':
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
                pattern = r'(\d{2}:\d{2}.\d{3} --> )'
                line_count = get_header_line_count(newvtt, pattern)
                if line_count == -1:
                    print('timestamps not found in file, skipping to next file')
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
                                new_default = default_update()
                                combined = default_head | new_default
                        elif match_row == -1 and nodefault == True:
                            print('no match found and default metadata is not being applied, skipping to next file')
                            continue
                        elif match_row != -1 and nodefault == False:
                            print(f'matching row found for {outputName}: row {match_row}; getting csv metadata...')
                            csv_row_data, parentfile = get_csv_metadata(match_row, m_csv)
                            if parentfile != '':
                                print(f'contains parent info: {parentfile}, getting parent file header...')
                                parent_head = assess_parent_header(parentfile, parent_dir, pattern)
                                if parent_head == None:
                                    print('no parent file FADGI header')
                                    parent_header_data = ''
                                    header_locals = ''
                                    combined = build_combined_header(parent_header_data, header_locals, csv_row_data, creation_date, reviewed, nodefault)
                                else:
                                    print('combining parent file header and metadata from csv...')
                                    parent_header_data, header_locals = get_header_data(parent_head)
                                    combined = build_combined_header(parent_header_data, header_locals, csv_row_data, creation_date, reviewed, nodefault)
                                    if reviewed == True:
                                        combined = change_reviewed(combined)
                            else:
                                parent_header_data = ''
                                header_locals = ''
                                combined = build_combined_header(parent_header_data, header_locals, csv_row_data, creation_date, reviewed, nodefault)
                        else:
                            print(f'matching row found for {outputName}: row {match_row}; getting csv metadata...')
                            csv_row_data, parentfile = get_csv_metadata(match_row, m_csv)
                            if parentfile != '':
                                print(f'contains parent info: {parentfile}, getting parent file header...')
                                parent_head = assess_parent_header(parentfile, parent_dir, pattern)
                                if parent_head == None:
                                    print('no parent file FADGI header')
                                    parent_header_data = ''
                                    header_locals = ''
                                    combined = build_combined_header(parent_header_data, header_locals, csv_row_data, creation_date, reviewed, nodefault)
                                else:
                                    print('combining parent file header and metadata from csv...')
                                    header_locals = ''
                                    parent_header_data, header_locals = get_header_data(parent_head)
                                    combined = build_combined_header(parent_header_data, header_locals, csv_row_data, creation_date, reviewed, nodefault)
                                    if reviewed == True:
                                        combined = change_reviewed(combined)
                            else:
                                parent_header_data = ''
                                header_locals = ''
                                combined = build_combined_header(parent_header_data, header_locals, csv_row_data, creation_date, reviewed, nodefault)
                    else:
                        if nodefault == False:
                            if reviewed == False:
                                print('no csv and no header, using default unreviewed metadata')
                                combined = default_header(creation_date)
                            else:
                                print('no csv and no header, using default reviewed metadata')
                                default_head = default_header(creation_date)
                                new_default = default_update()
                                combined = default_head | new_default
                        else:
                            print('no csv, no header, and default metadata is not being applied, skipping to next file')
                            continue
                else:
                    print(f'FADGI header detected: {line_count} lines')
                    vtt_head = assess_parent_header(newvtt, reviewed_dir, pattern)
                    vtt_header_data, header_locals = get_header_data(vtt_head)
                    if reviewed == False:
                        if m_csv != None:
                            print('checking csv for match...')
                            match_row = find_match(m_csv, outputName)
                            if nodefault == True:
                                if match_row == -1:
                                    print('no match found and default metadata is not being applied, skipping to next file')
                                    continue
                                else:
                                    print(f'matching row found for {outputName}: row {match_row}; getting csv metadata...')
                                    csv_row_data, parentfile = get_csv_metadata(match_row, m_csv)
                                    creation_date = "no_update"
                                    combined = build_combined_header(vtt_header_data, header_locals, csv_row_data, creation_date, reviewed, nodefault)
                            else:
                                if match_row == -1:
                                    print('no match found, applying default unreviewed metadata')
                                    default_head = default_header(creation_date)
                                    combined = default_head | vtt_header_data
                                else:
                                    print(f'matching row found for {outputName}: row {match_row}; getting csv metadata...')
                                    csv_row_data, parentfile = get_csv_metadata(match_row, m_csv)
                                    combined = build_combined_header(vtt_header_data, header_locals, csv_row_data, creation_date, reviewed, nodefault)
                        else:
                            if nodefault == True:
                                print('no csv and default metadata is not being applied, skipping to next file')
                                continue
                            else:
                                print('no csv, using default unreviewed metadata')
                                default_head = default_header(creation_date)
                                combined = default_head | vtt_header_data
                    else:
                        print('changing review history to reviewed')
                        if m_csv != None:
                            print('checking csv for match...')
                            match_row = find_match(m_csv, outputName)
                            if nodefault == False:
                                if match_row == -1:
                                    print('no match found, applying default reviewed metadata')
                                    combined = update_fadgi_header(vtt_header_data, creation_date, nodefault)
                                else:
                                    print(f'matching row found for {outputName}: row {match_row}; getting csv metadata...')
                                    csv_row_data, parentfile = get_csv_metadata(match_row, m_csv)
                                    combined = build_combined_header(vtt_header_data, header_locals, csv_row_data, creation_date, reviewed, nodefault)
                                    combined = change_reviewed(combined)
                            else:
                                if match_row == -1:
                                    print('no match found and default metadata is not being applied, only updating review history')
                                    combined = change_reviewed(vtt_header_data)
                                else:
                                    print(f'matching row found for {outputName}: row {match_row}; getting csv metadata...')
                                    csv_row_data, parentfile = get_csv_metadata(match_row, m_csv)
                                    combined = build_combined_header(vtt_header_data, header_locals, csv_row_data, creation_date, reviewed, nodefault)
                                    combined = change_reviewed(combined)
                        elif m_csv == None and nodefault == False:
                            print('no csv, using default reviewed metadata')
                            creation_date = "no_update"
                            combined = update_fadgi_header(vtt_header_data, creation_date, nodefault)
                        else:
                            print('no csv and default metadata is not being applied, only updating review history')
                            combined = change_reviewed(vtt_header_data)
                write_new_header(combined, outputDir, outputName, newvtt, line_count)
            elif fileExt == '.txt' and m_csv != None:
                outputName = justName + ".txt"
                copy_metadata_to_txt(outputName, newvtt, m_csv, parent_dir, outputDir)
            else:
                continue

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
        print('directory of parent files:\n\tno parent file directory provided')
    if reviewed == True:
        print('webvtt files are: reviewed\n\tscript will create/update reviewed FADGI headers\n\t(will update "review history" to "human-reviewed"\n\tor create this element if it doesn\'t exist)')
    else:
        print('webvtt files are: unreviewed\n\tscript will create initial FADGI headers\n\tand skip files with existing FADGI headers')
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
