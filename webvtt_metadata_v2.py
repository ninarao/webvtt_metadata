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
from itertools import zip_longest, islice, chain

match_row = 3
m_csv = '/Users/nraogra/Desktop/webvtt_v2/webvtt_metadata_locals.csv'
vttfile = '/Users/nraogra/Desktop/webvtt_v2/934_B21_005_SideA_rev.vtt'
parentfile = '/Users/nraogra/Desktop//webvtt_v2/934_B21_005_SideA.vtt'

# sys.argv = [
#    'webvtt_metadata.py',
#    '/Users/nraogra/Downloads/OneDrive_1_6-10-2026',
#    '-c',
#    '/Users/nraogra/Downloads/CaptionFiles-Captionfilerecords.csv',
#     '-r',
#     '-e',
#    '-p', 
#    '/Users/nraogra/Desktop/txt-test',
#    ]

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

def get_header_line_count(vttfile, pattern, fileExt):
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
    if fileExt == '.vtt':
        return -1
    elif fileExt == '.txt':
        return -2

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
        values = data[match_row - 1]
        zipped = list(zip_longest(keys, values, fillvalue=''))
        for key, value in zipped:
            if key.casefold() == "parent file".casefold():
                parentkey = key
                parentfile = value
            else:
                parentfile = ''
        csv_row_data = zipped
        return csv_row_data, parentfile

def assess_parent_header(parentfile, parent_dir):
    lines = -1
    if parent_dir is None:
        print('no directory for parent files')
        parent_head = None
        return parent_head, lines
    vttfile = os.path.join(parent_dir, parentfile)
    if not os.path.isfile(vttfile):
        print(f'file does not exist: {vttfile}')
        parent_head = None
        return parent_head, lines
    else:
        justName = Path(vttfile).stem
        fileExt = Path(vttfile).suffix
        if fileExt == '.vtt':
            outputName = justName + ".vtt"
            pattern = r'(\d{2}:\d{2}.\d{3} --> )'
        elif fileExt == '.txt':
            outputName = justName + ".txt"
            pattern = r'^Type:'
        else:
            print(f'parent file {justName}{fileExt} is not .vtt or .txt')
            parent_head = None
            return parent_head, lines
        lines = get_header_line_count(vttfile, pattern, fileExt)
        if fileExt == '.txt' and lines != -2:
            matches = []
            nl_str = '\n'
            with open(vttfile, 'r', encoding='UTF-8') as input:
                for line_num, line in enumerate(islice(input, lines, None)):
                    if line == nl_str:
                        matches.append(line_num)
                        if len(matches) == 1:
                            break
            if len(matches) == 1:
                lines = matches[0] + 1
        if lines == -1:
            print('timestamps not found in parent file')
            parent_head = None
            return parent_head, lines
        elif (lines == 2 and fileExt == '.vtt') or lines == -2:
            print('no FADGI header detected in parent file')
            parent_head = None
            return parent_head, lines
        else:
            print(f'FADGI header found: {lines} lines')
            with open(vttfile, 'r', encoding='UTF-8') as input:
                parent_head = [next(input) for _ in range(lines)]
            input.close()
            return parent_head, lines

def get_header_data(parent_head):
    parent_head = [x for x in parent_head if x != '\n']
    parent_head = [x.replace('\n', '') if x.endswith('\n') else x for x in parent_head]
    if parent_head[0] == 'WEBVTT':
        parent_head[0] = 'Header: WEBVTT'
    indices = [i for i, s in enumerate(parent_head) if "Local Usage Element" in s]
    lox = [i for i, s in enumerate(parent_head) if s.startswith("_")]
    if indices or lox:
        locals = []
        for i in chain(indices, lox):
            locals.append(parent_head[i])
        new_locals = [item.replace("Local Usage Element: ", "") for item in locals]
        string = [item.split('; ') for item in new_locals]
        flatlist = list(chain.from_iterable(string))
        flatlist = [x.replace('[', '_', 1) if x.startswith('[') else x for x in flatlist]
        flatlist = [x.replace(']', ':', 1) if ']' in x else x for x in flatlist]
        flatlist = [x.replace('software version', 'Software version', 1) if 'software version' in x else x for x in flatlist]
        header_locals = [x.replace('review history', 'Review history', 1) if 'review history' in x else x for x in flatlist]
        local_tuples = [tuple(x.split(': ')) for x in header_locals]
        for index in sorted(chain(indices, lox), reverse=True):
            del parent_head[index]
        parent_head.extend(header_locals)
    else:
        header_locals = ""
    for index, item in enumerate(parent_head):
        if ':' not in item:
            parent_head[index] = item + ': ' + item
    parent_head_tuples = [tuple(x.split(': ', 1)) for x in parent_head]
    header_data = parent_head_tuples
    return header_data, header_locals
    
def merge_headers(vtt_header_data, parent_header_data):
    if not any('File Creation Date' in t[0] for t in vtt_header_data):
        if any('File Creation Date' in t[0] for t in parent_header_data):
            parent_header_data = [t for t in parent_header_data if t[0] != 'File Creation Date']
    vtt_locals = list({t for t in vtt_header_data if t and t[0].startswith('_')})
    p_locals = {t for t in parent_header_data if t and t[0].startswith('_')}
    vtt_nonlocal = list({t for t in vtt_header_data if t and not t[0].startswith('_')})
    vtt_keys = {x[0] for x in vtt_header_data}
    loc_append = {'_Reviewer', '_Editing method'}
    p_unique = [x for x in parent_header_data if x[0] not in vtt_keys]
    p_uniq_nonlocal = list({t for t in p_unique if t and not t[0].startswith('_')})
    p_uniq_local = list({t for t in p_unique if t and t[0].startswith('_')})
    p_append = [x for x in p_locals if x[0] in loc_append]
    dedupe_append = list(set(p_uniq_local + p_append))
    merged_header_data = vtt_nonlocal + p_uniq_nonlocal + vtt_locals + dedupe_append
    merged_locals = vtt_locals + dedupe_append
    return merged_header_data, merged_locals

def build_combined_header(parent_header_data, header_locals, csv_row_data, creation_date, reviewed, nodefault):
    if csv_row_data != '':
        csv_row_data = [t for t in csv_row_data if t[1] != '']
        csv_locals = list({t for t in csv_row_data if t and t[0].startswith('_')})
        if csv_locals == []:
            locals = False
        else:
            locals = True
        if not any('File Creation Date' in t[0] for t in csv_row_data):
            if any('File Creation Date' in t[0] for t in parent_header_data):
                header_date = next((v for k, v in parent_header_data if k == 'File Creation Date'), '')
                csv_row_data.append(('File Creation Date', header_date))
        combined_header_data, combined_locals = merge_headers(csv_row_data, parent_header_data)
    else:
        combined_header_data = parent_header_data
        combined_locals = header_locals

    if nodefault == False:
        if not any('Type' in t[0] for t in combined_header_data):
            combined_header_data.append(('Type', 'caption'))
        if not any('Language' in t[0] for t in combined_header_data):
            combined_header_data.append(('Language', 'eng'))
        if not any('Responsible Party' in t[0] for t in combined_header_data):
            combined_header_data.append(('Responsible Party', 'US, Emory University'))
        if not any('Media Identifier' in t[0] for t in combined_header_data):
            combined_header_data.append(('Media Identifier', 'unknown'))
        if not any('Originating File' in t[0] for t in combined_header_data):
            combined_header_data.append(('Originating File', 'unknown'))
        if not any('File Creator' in t[0] for t in combined_header_data):
            combined_header_data.append(('File Creator', 'Whisper'))
        if not any('File Creation Date' in t[0] for t in combined_header_data):
            combined_header_data.append(('File Creation Date', creation_date))
        if not any('Title' in t[0] for t in combined_header_data):
            combined_header_data.append(('Title', 'unknown'))
        if not any('Origin History' in t[0] for t in combined_header_data):
            combined_header_data.append(('Origin History', 'Created by Emory Libraries Media Preservation'))
    if nodefault == False and reviewed == False:
        if not any('_Review history' in t[0] for t in combined_header_data):
            combined_header_data.append(('_Review history', 'unreviewed'))
            combined_locals.append(('_Review history', 'unreviewed'))
        if not any('_Parent File' in t[0] for t in combined_header_data):
            combined_header_data.append(('_Parent File', 'unknown'))
            combined_locals.append(('_Parent File', 'unknown'))
    if nodefault == False and reviewed == True:
        if not any('_Review history' in t[0] for t in combined_header_data):
            combined_header_data.append(('_Review history', 'human-reviewed'))
            combined_locals.append(('_Review history', 'human-reviewed'))
        if not any('_Reviewer' in t[0] for t in combined_header_data):
            combined_header_data.append(('_Reviewer', 'unknown'))
            combined_locals.append(('_Reviewer', 'unknown'))
        if not any('_Editing Method' in t[0] for t in combined_header_data):
            combined_header_data.append(('_Editing Method', 'unknown'))
            combined_locals.append(('_Editing Method', 'unknown'))
        if not any('_Parent File' in t[0] for t in combined_header_data):
            combined_header_data.append(('_Parent File', 'unknown'))
            combined_locals.append(('_Parent File', 'unknown'))
    if nodefault == True and reviewed == True:
        if any('_Review history' in t[0] for t in combined_header_data):
            combined_header_data = [(t[0], 'human-reviewed') if t[0] == '_Review history' else t for t in combined_header_data]
            combined_locals= [(t[0], 'human-reviewed') if t[0] == '_Review history' else t for t in combined_locals]
        else:
            combined_header_data.append(('_Review history', 'human-reviewed'))
            combined_locals.append(('_Review history', 'human-reviewed'))
        
    return combined_header_data

def check_conformance(vtt_head, fileExt):
    ref_list = ['Header', 'Note', 'Type', 'Language', 'Responsible Party',
            'Media Identifier', 'Originating File', 'File Creator',
            'File Creation Date', 'Title', 'Origin History']
    order_map = {key.lower(): index for index, key in enumerate(ref_list)}
    sorted_tupes = sorted(vtt_head, key=lambda x: (order_map.get(x[0].lower(), float('inf')), x[0].lower(), id(x)))
    
    webvtt_str = 'WEBVTT'
    note_str = 'NOTE'
    type_str = 'Type'
    
    if fileExt == '.vtt':
        webvtt_index = next((i for i, s in enumerate(sorted_tupes) if webvtt_str.casefold() in s[1].casefold()), -1)    
        if webvtt_index == -1:
            sorted_tupes.insert(0, ('', 'WEBVTT'))
        else:
            caps_webvtt = ('', sorted_tupes[webvtt_index][1].upper())
            sorted_tupes[webvtt_index] = caps_webvtt
            if webvtt_index != 0:
                item = sorted_tupes.pop(webvtt_index)
                sorted_tupes.insert(0, item)
        sorted_tupes.insert(1, ('', '\n'))
        note_index = next((i for i, s in enumerate(sorted_tupes) if note_str.casefold() in s[1].casefold()), -1)
        if note_index == -1:
            sorted_tupes.insert(2, ('', 'NOTE'))
        else:
            caps_note = ('', sorted_tupes[note_index][1].upper())
            sorted_tupes[note_index] = caps_note
            if note_index != 2:
                item = sorted_tupes.pop(note_index)
                sorted_tupes.insert(2, item)

    if fileExt == '.txt':
        sorted_tupes = [t for t in sorted_tupes if t[1] != webvtt_str]
        sorted_tupes = [t for t in sorted_tupes if t[1] != note_str]
        type_index = next((i for i, s in enumerate(sorted_tupes) if type_str.casefold() in s[0].casefold()), -1)
        if type_index == -1:
            sorted_tupes.insert(0, ('Type', 'transcript'))
        else:
            type_update = ('Type', 'transcript')
            sorted_tupes[type_index] = type_update
    
    sorted_tupes.append(('', '\n'))
    
#     Type (no)
#     Language (yes)
#     Responsible Party (yes)
#     Media Identifier (yes)
#     Originating File (no)
#     File Creator (yes)
#     File Creation Date (no)
#     Title (no)
#     Origin History (yes)
    
    return sorted_tupes

def write_new_header(final_header, outputDir, outputName, newvtt, line_count, fileExt, nodefault):

    newfile = os.path.join(outputDir, outputName)
    
    final_header = [t[1:] if (t and not t[0]) else t for t in final_header]
    final_header = [': '.join(map(str, t)) for t in final_header]
    print(f'final_header: {final_header}')

    if fileExt == '.vtt':
        type_str = 'Type: transcript'
        type_index = next((i for i, s in enumerate(newheader) if type_str in s), -1)
        if type_index != -1 and nodefault == True:
            newheader[type_index] = newheader[type_index].replace('transcript', '')
        elif type_index != -1 and nodefault == False:
            newheader[type_index] = newheader[type_index].replace('transcript', 'caption')
    
    newfile = os.path.join(outputDir, outputName)
    with open(newvtt, 'r', encoding='UTF-8') as f_in, open(newfile, 'w', encoding='UTF-8') as f_out:
        for item in final_header:
            f_out.write(f'{item}\n')
        for _ in range(line_count):
            next(f_in, None)
        shutil.copyfileobj(f_in, f_out)
    f_in.close()
    f_out.close()

def update_metadata(reviewed_dir, m_csv, outputDir, parent_dir, reviewed, nodefault, keys):
    ext = ['.vtt', '.txt']
    for newvtt in glob.glob(f'{reviewed_dir}/*{ext}'):
        if os.path.isfile(newvtt):
            justName = Path(newvtt).stem
            fileExt = Path(newvtt).suffix
            if fileExt == '.vtt':
                outputName = justName + ".vtt"
                print(f'\n{outputName}')
                pattern = r'(\d{2}:\d{2}.\d{3} --> )'
            elif fileExt == '.txt':
                outputName = justName + ".txt"
                print(f'\n{outputName}')
                pattern = r'^Type:'
            else:
                continue
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
            line_count = get_header_line_count(newvtt, pattern, fileExt)
            if line_count == -1:
                print('timestamps not found in file, skipping to next file')
                continue
            elif (line_count == 2 and fileExt == '.vtt') or line_count == -2:
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
                            parent_head, lines = assess_parent_header(parentfile, parent_dir)
                            if parent_head == None:
                                print('no parent file FADGI header')
                                parent_header_data = ''
                                header_locals = ''
                                combined = build_combined_header(parent_header_data, header_locals, csv_row_data, creation_date, reviewed, nodefault, keys)
                            else:
                                print('combining parent file header and metadata from csv...')
                                parent_header_data, header_locals = get_header_data(parent_head)
                                combined = build_combined_header(parent_header_data, header_locals, csv_row_data, creation_date, reviewed, nodefault, keys)
                                if reviewed == True:
                                    combined = change_reviewed(combined)
                        else:
                            parent_header_data = ''
                            header_locals = ''
                            combined = build_combined_header(parent_header_data, header_locals, csv_row_data, creation_date, reviewed, nodefault, keys)
                    else:
                        print(f'matching row found for {outputName}: row {match_row}; getting csv metadata...')
                        creation_date = "no_update"
                        csv_row_data, parentfile = get_csv_metadata(match_row, m_csv)
                        if parentfile != '':
                            print(f'contains parent info: {parentfile}, getting parent file header...')
                            parent_head, lines = assess_parent_header(parentfile, parent_dir)
                            if parent_head == None:
                                print('no parent file FADGI header')
                                parent_header_data = ''
                                header_locals = ''
                                combined = build_combined_header(parent_header_data, header_locals, csv_row_data, creation_date, reviewed, nodefault, keys)
                            else:
                                print('combining parent file header and metadata from csv...')
                                header_locals = ''
                                parent_header_data, header_locals = get_header_data(parent_head)
                                combined = build_combined_header(parent_header_data, header_locals, csv_row_data, creation_date, reviewed, nodefault, keys)
                                if reviewed == True:
                                    combined = change_reviewed(combined)
                        else:
                            parent_header_data = ''
                            header_locals = ''
                            combined = build_combined_header(parent_header_data, header_locals, csv_row_data, creation_date, reviewed, nodefault, keys)
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
                vtt_head, lines = assess_parent_header(newvtt, reviewed_dir)
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
                                if parentfile != '':
                                    print(f'contains parent info: {parentfile}, getting parent file header...')
                                    parent_head, lines = assess_parent_header(parentfile, parent_dir)
                                    if parent_head == None:
                                        print('no parent file FADGI header')
                                        combined = build_combined_header(vtt_header_data, header_locals, csv_row_data, creation_date, reviewed, nodefault, keys)
                                    else:
                                        print('combining source header, parent file header, and metadata from csv...')
#                                         header_locals = ''
                                        parent_header_data, p_header_locals = get_header_data(parent_head)
                                        merged_header_data, header_locals = merge_headers(vtt_header_data, header_locals, parent_header_data, p_header_locals, keys)
                                        combined = build_combined_header(merged_header_data, header_locals, csv_row_data, creation_date, reviewed, nodefault, keys)
                                else:
                                    combined = build_combined_header(vtt_header_data, header_locals, csv_row_data, creation_date, reviewed, nodefault, keys)
                        else:
                            if match_row == -1:
                                print('no match found, applying default unreviewed metadata')
                                default_head = default_header(creation_date)
                                combined = default_head | vtt_header_data
                            else:
                                print(f'matching row found for {outputName}: row {match_row}; getting csv metadata...')
                                csv_row_data, parentfile = get_csv_metadata(match_row, m_csv)
                                creation_date = "no_update"
                                if parentfile != '':
                                    print(f'contains parent info: {parentfile}, getting parent file header...')
                                    parent_head, lines = assess_parent_header(parentfile, parent_dir)
                                    if parent_head == None:
                                        print('no parent file FADGI header')
                                        combined = build_combined_header(vtt_header_data, header_locals, csv_row_data, creation_date, reviewed, nodefault, keys)
                                    else:
                                        print('combining source header, parent file header, and metadata from csv...')
                                        parent_header_data, p_header_locals = get_header_data(parent_head)
                                        merged_header_data, header_locals = merge_headers(vtt_header_data, header_locals, parent_header_data, p_header_locals, keys)
                                        combined = build_combined_header(merged_header_data, header_locals, csv_row_data, creation_date, reviewed, nodefault, keys)
                                else:
                                    combined = build_combined_header(vtt_header_data, header_locals, csv_row_data, creation_date, reviewed, nodefault, keys)
                    else:
                        if nodefault == True:
                            print('no csv and default metadata is not being applied, checking conformance only')
                            vtt_head_new, updated = check_conformance(line_count, vtt_head, fileExt)
                            if updated == True:
                                print('updating for FADGI conformance')
                                newfile = os.path.join(outputDir, outputName)
                                with open(newvtt, 'r', encoding='UTF-8') as f_in, open(newfile, 'w', encoding='UTF-8') as f_out:
                                    for item in vtt_head_new:
                                        f_out.write(f'{item}')
                                    if fileExt == '.vtt':
                                        for _ in range(line_count):
                                            next(f_in, None)
                                    if fileExt == '.txt':
                                        for _ in range(lines + 1):
                                            next(f_in, None)
                                    shutil.copyfileobj(f_in, f_out)
                                f_in.close()
                                f_out.close()
                                continue
                            else:
                                print('file conforms, skipping to next file')
                                continue
                        else:
                            print('no csv, using default unreviewed metadata')
                            creation_date = "no_update"
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
                                combined = update_fadgi_header(vtt_header_data, creation_date, nodefault, keys)
                            else:
                                print(f'matching row found for {outputName}: row {match_row}; getting csv metadata...')
                                csv_row_data, parentfile = get_csv_metadata(match_row, m_csv)
                                creation_date = "no_update"
                                if parentfile != '':
                                    print(f'contains parent info: {parentfile}, getting parent file header...')
                                    parent_head, lines = assess_parent_header(parentfile, parent_dir)
                                    if parent_head == None:
                                        print('no parent file FADGI header')
                                        combined = build_combined_header(vtt_header_data, header_locals, csv_row_data, creation_date, reviewed, nodefault, keys)
                                        combined = change_reviewed(combined)
                                    else:
                                        print('combining source header, parent file header, and metadata from csv...')
#                                         header_locals = ''
                                        parent_header_data, p_header_locals = get_header_data(parent_head)
                                        merged_header_data, header_locals = merge_headers(vtt_header_data, header_locals, parent_header_data, p_header_locals, keys)
                                        combined = build_combined_header(merged_header_data, header_locals, csv_row_data, creation_date, reviewed, nodefault, keys)
                                        combined = change_reviewed(combined)
                                else:
                                    combined = build_combined_header(vtt_header_data, header_locals, csv_row_data, creation_date, reviewed, nodefault, keys)
                                    combined = change_reviewed(combined)
                        else:
                            if match_row == -1:
                                print('no match found and default metadata is not being applied, only updating review history')
                                combined = change_reviewed(vtt_header_data)
                            else:
                                print(f'matching row found for {outputName}: row {match_row}; getting csv metadata...')
                                csv_row_data, parentfile = get_csv_metadata(match_row, m_csv)
                                creation_date = "no_update"
                                if parentfile != '':
                                    print(f'contains parent info: {parentfile}, getting parent file header...')
                                    parent_head, lines = assess_parent_header(parentfile, parent_dir)
                                    if parent_head == None:
                                        print('no parent file FADGI header')
                                        combined = build_combined_header(vtt_header_data, header_locals, csv_row_data, creation_date, reviewed, nodefault, keys)
                                        combined = change_reviewed(combined)
                                    else:
                                        print('combining source header, parent file header, and metadata from csv...')
#                                         header_locals = ''
                                        parent_header_data, p_header_locals = get_header_data(parent_head)
                                        merged_header_data, header_locals = merge_headers(vtt_header_data, header_locals, parent_header_data, p_header_locals, keys)
                                        combined = build_combined_header(merged_header_data, header_locals, csv_row_data, creation_date, reviewed, nodefault, keys)
                                        combined = change_reviewed(combined)
                                else:
                                    combined = build_combined_header(vtt_header_data, header_locals, csv_row_data, creation_date, reviewed, nodefault, keys)
                                    combined = change_reviewed(combined)
                    elif m_csv == None and nodefault == False:
                        print('no csv, using default reviewed metadata')
                        creation_date = "no_update"
                        combined = update_fadgi_header(vtt_header_data, creation_date, nodefault, keys)
                    else:
                        print('no csv and default metadata is not being applied, only updating review history')
                        combined = change_reviewed(vtt_header_data)
            if fileExt == '.txt' and line_count != -2:
                line_count = lines + 1
            write_new_header(combined, outputDir, outputName, newvtt, line_count, fileExt, nodefault)
        else:
            continue



with open(vttfile, 'r', encoding='UTF-8') as input:
    vtt_head = [next(input) for _ in range(15)]
    
with open(parentfile, 'r', encoding='UTF-8') as input:
    parent_head = [next(input) for _ in range(15)]

csv_row_data, parentfile = get_csv_metadata(match_row, m_csv)
# print(f'csv_row_data: {csv_row_data}')
# print(f'parentfile: {parentfile}')

vtt_header_data, header_locals = get_header_data(vtt_head)
parent_header_data, p_header_locals = get_header_data(parent_head)
# print(f'vtt_header_data: {vtt_header_data}')
# print(f'header_locals: {header_locals}')

merged_header_data, merged_locals = merge_headers(vtt_header_data, parent_header_data)

creation_date = 'today'
reviewed = False
nodefault = True
csv_row_data = ''
# merged_header_data = []
# merged_locals = []

combined = build_combined_header(merged_header_data, merged_locals, csv_row_data, creation_date, reviewed, nodefault)
# print(f'combined: {combined}')

vtt_head = combined
fileExt = '.vtt'

final_header = check_conformance(vtt_head, fileExt)
# print(f'final_header: {final_header}')

outputDir = 'directory'
outputName = 'newfilename'
newvtt = 'file'
line_count = 15

write_new_header(final_header, outputDir, outputName, newvtt, line_count, fileExt, nodefault)
    