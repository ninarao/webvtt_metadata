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

sys.argv = [
   '/Users/nraogra/Desktop/webvtt_v2/webvtt_metadata_v2.py',
   '/Users/nraogra/Desktop/webvtt_v2',
#    '-c',
#    '/Users/nraogra/Desktop/webvtt_v2/webvtt_metadata_locals.csv',
#     '-r',
#     '-e',
   '-p', 
   '/Users/nraogra/Desktop/webvtt_v2',
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
    parser.add_argument("reviewed_dir", type=valid_directory, help="Directory of vtt files")
    parser.add_argument("-c", "--csv", type=valid_csv, help="Metadata CSV")
    parser.add_argument("-e", "--emorydefault", action="store_true", help="use Emory default metadata set for empty fields")
    parser.add_argument("-r", "--reviewed", action="store_true", help="creates/updates FADGI header for reviewed files")
    parser.add_argument("-p", "--parentfiles", type=valid_directory, help="Directory of parent files")
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
        values = data[match_row]
        zipped = list(zip_longest(keys, values, fillvalue=''))
        for key, value in zipped:
            if key.casefold() == "_Parent File".casefold():
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
            pattern = r'(\d{2}:\d{2}.\d{3} --> )'
        elif fileExt == '.txt':
            pattern = r'^Type:'
        else:
            print(f'file {justName}{fileExt} is not .vtt or .txt')
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
            print('timestamps not found in file')
            parent_head = None
            return parent_head, lines
        elif (lines == 2 and fileExt == '.vtt') or lines == -2:
            print('no FADGI header detected in file')
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
        flatlist = [x.replace('software version', 'Software Version', 1) if 'software version' in x else x for x in flatlist]
        flatlist = [x.replace('Review history', 'Review History', 1) if 'Review history' in x else x for x in flatlist]
        header_locals = [x.replace('review history', 'Review History', 1) if 'review history' in x else x for x in flatlist]
        for index in sorted(chain(indices, lox), reverse=True):
            del parent_head[index]
        parent_head.extend(header_locals)
    for index, item in enumerate(parent_head):
        if ':' not in item:
            parent_head[index] = item + ': ' + item
    parent_head_tuples = [tuple(x.split(': ', 1)) for x in parent_head]
    header_data = parent_head_tuples    
    return header_data
    
def merge_headers(vtt_header_data, parent_header_data, source):
    if not any('File Creation Date'.casefold() in t[0].casefold() for t in vtt_header_data):
        if any('File Creation Date'.casefold() in t[0].casefold() for t in parent_header_data):
            parent_header_data = [t for t in parent_header_data if t[0].casefold() != 'File Creation Date'.casefold()]
    parent_header_data = [
        t + (source,) if t[0].casefold() == '_Reviewer'.casefold() and len(t) <= 2 else t for t in parent_header_data]
    vtt_locals = list({t for t in vtt_header_data if t and t[0].startswith('_')})
    p_locals = {t for t in parent_header_data if t and t[0].startswith('_')}
    vtt_nonlocal = list({t for t in vtt_header_data if t and not t[0].startswith('_')})
    vtt_keys = {x[0].casefold() for x in vtt_header_data}
    loc_append = {'_Reviewer'.casefold()}
    p_unique = [x for x in parent_header_data if x[0].casefold() not in vtt_keys]
    p_uniq_nonlocal = list({t for t in p_unique if t and not t[0].startswith('_')})
    p_uniq_local = list({t for t in p_unique if t and t[0].startswith('_')})
    p_append = [x for x in p_locals if x[0].casefold() in loc_append]
    dedupe_append = list(set(p_uniq_local + p_append))
    merged_header_data = vtt_nonlocal + p_uniq_nonlocal + vtt_locals + dedupe_append
#     merged_locals = vtt_locals + dedupe_append
    return merged_header_data

def build_combined_header(parent_header_data, csv_row_data, creation_date, reviewed, default):
    for key, value in csv_row_data:
        if "Source File".casefold() in key.casefold():
            source = value
            csv_row_data.remove((key, value))
    if csv_row_data != '':
        csv_row_data = [t for t in csv_row_data if t[1] != '']
        if not any('File Creation Date'.casefold() in t[0].casefold() for t in csv_row_data):
            if any('File Creation Date'.casefold() in t[0].casefold() for t in parent_header_data):
                header_date = next((v for k, v in parent_header_data if k.casefold() == 'File Creation Date'.casefold()), '')
                csv_row_data.append(('File Creation Date', header_date))
        combined_header_data = merge_headers(csv_row_data, parent_header_data, source)
    else:
        combined_header_data = parent_header_data

    if default == True:
        if not any('Type'.casefold() in t[0].casefold() for t in combined_header_data):
            combined_header_data.append(('Type', 'caption'))
        if not any('Language'.casefold() in t[0].casefold() for t in combined_header_data):
            combined_header_data.append(('Language', 'eng'))
        if not any('Responsible Party'.casefold() in t[0].casefold() for t in combined_header_data):
            combined_header_data.append(('Responsible Party', 'US, Emory University'))
        if not any('Media Identifier'.casefold() in t[0].casefold() for t in combined_header_data):
            combined_header_data.append(('Media Identifier', 'unknown'))
        if not any('Originating File'.casefold() in t[0].casefold() for t in combined_header_data):
            combined_header_data.append(('Originating File', 'unknown'))
        if not any('File Creator'.casefold() in t[0].casefold() for t in combined_header_data):
            combined_header_data.append(('File Creator', 'Whisper'))
        if not any('File Creation Date'.casefold() in t[0].casefold() for t in combined_header_data):
            combined_header_data.append(('File Creation Date', creation_date))
        if not any('Title'.casefold() in t[0].casefold() for t in combined_header_data):
            combined_header_data.append(('Title', 'unknown'))
        if not any('Origin History'.casefold() in t[0].casefold() for t in combined_header_data):
            combined_header_data.append(('Origin History', 'Created by Emory Libraries Media Preservation'))
    if default == True and reviewed == False:
        if not any('_Review History'.casefold() in t[0].casefold() for t in combined_header_data):
            combined_header_data.append(('_Review History', 'unreviewed'))
        if not any('_Parent File'.casefold() in t[0].casefold() for t in combined_header_data):
            combined_header_data.append(('_Parent File', 'unknown'))
    if default == True and reviewed == True:
        if not any('_Review History'.casefold() in t[0].casefold() for t in combined_header_data):
            combined_header_data.append(('_Review History', 'human-reviewed'))
        if not any('_Reviewer'.casefold() in t[0].casefold() for t in combined_header_data):
            combined_header_data.append(('_Reviewer', 'unknown'))
        if not any('_Parent File'.casefold() in t[0].casefold() for t in combined_header_data):
            combined_header_data.append(('_Parent File', 'unknown'))
    if default == False and reviewed == True:
        if any('_Review History'.casefold() in t[0].casefold() for t in combined_header_data):
            combined_header_data = [(t[0], 'human-reviewed') if t[0].casefold() == '_Review History'.casefold() else t for t in combined_header_data]
        else:
            combined_header_data.append(('_Review History', 'human-reviewed'))
        
    return combined_header_data

def check_conformance(vtt_head, fileExt, default):
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
        sorted_tupes.insert(1, ('', ''))
        note_index = next((i for i, s in enumerate(sorted_tupes) if note_str.casefold() in s[1].casefold()), -1)
        if note_index == -1:
            sorted_tupes.insert(2, ('', 'NOTE'))
        else:
            caps_note = ('', sorted_tupes[note_index][1].upper())
            sorted_tupes[note_index] = caps_note
            if note_index != 2:
                item = sorted_tupes.pop(note_index)
                sorted_tupes.insert(2, item)
        type_index = next((i for i, s in enumerate(sorted_tupes) if type_str.casefold() in s[0].casefold()), -1)
        if type_index != -1:
            if 'transcript'.casefold() in sorted_tupes[type_index][1].casefold():
                if default == False:
                    type_update = ('Type', '')
                    sorted_tupes[type_index] = type_update
                else:
                    type_update = ('Type', 'caption')
                    sorted_tupes[type_index] = type_update
    if fileExt == '.txt':
        sorted_tupes = [t for t in sorted_tupes if t[1] != webvtt_str]
        sorted_tupes = [t for t in sorted_tupes if t[1] != note_str]
        type_index = next((i for i, s in enumerate(sorted_tupes) if type_str.casefold() in s[0].casefold()), -1)
        if default == True:
            if type_index == -1:
                sorted_tupes.insert(0, ('Type', 'transcript'))
            else:
                type_update = ('Type', 'transcript')
                sorted_tupes[type_index] = type_update
        else:
            if type_index == -1:
                sorted_tupes.insert(0, ('Type', ''))

    sorted_tupes.append(('', ''))
    
    arrow = '-->'
    forbidden_arrow = [t for t in sorted_tupes if any(arrow in str(x) for x in t)]
    if forbidden_arrow:
        print(f'forbidden_arrow: {forbidden_arrow}')
    forbidden_dupes = ['Type', 'Originating File', 'File Creation Date', 'Title']
    seen = set()
    dupes = set()
    for x in sorted_tupes:
        if x[0] in seen:
            dupes.add(x[0])
        else:
            seen.add(x[0])
    forbidden_dupes_in_ya_tupes = [x for x in dupes if x in forbidden_dupes]
    if forbidden_dupes_in_ya_tupes:
        print(f'forbidden_dupes_in_ya_tupes: {forbidden_dupes_in_ya_tupes}')

    return sorted_tupes, forbidden_arrow, forbidden_dupes_in_ya_tupes

def write_new_header(final_header, outputDir, outputName, newvtt, line_count, fileExt):
    newfile = os.path.join(outputDir, outputName)
    final_header = [t[1:] if (t and not t[0]) else t for t in final_header]
    final_header = [(t[0], (', '.join([str(t[1]), str(t[2])]))) if len(t) == 3 else t for t in final_header]
    final_header = [': '.join(map(str, t)) for t in final_header]

    newfile = os.path.join(outputDir, outputName)
    with open(newvtt, 'r', encoding='UTF-8') as f_in, open(newfile, 'w', encoding='UTF-8') as f_out:
        for item in final_header:
            f_out.write(f'{item}\n')
        for _ in range(line_count):
            next(f_in, None)
        shutil.copyfileobj(f_in, f_out)
    f_in.close()
    f_out.close()

def generate_log(log, what2log):
    if not os.path.isfile(log):
        with open(log, "w", encoding='utf-8') as f:
            f.write(what2log + '\n')
    else:
        with open(log, "a", encoding='utf-8') as f:
            f.write(what2log + '\n')

def update_metadata(reviewed_dir, m_csv, outputDir, parent_dir, reviewed, default):
    logname = 'webvtt_metadata_log.txt'
    log_source = os.path.join(outputDir, logname)
    timenow = datetime.datetime.now()
    files_updated = []
    files_skipped = []
    files_nonconforming = []
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
                files_skipped.append(outputName)
                continue
            elif (line_count == 2 and fileExt == '.vtt') or line_count == -2:
                print('no FADGI header detected')
                header_data = []
                csv_row_data = ''
                if m_csv != None:
                    print('checking csv for match...')
                    match_row = find_match(m_csv, outputName)
                    if match_row == -1 and default == True:
                        if reviewed == False:
                            print('no match found, applying default unreviewed metadata')
                        else:
                            print('no match found, applying default reviewed metadata')
                        combined = build_combined_header(header_data, csv_row_data, creation_date, reviewed, default)
                    elif match_row == -1 and default == False:
                        print('no match found and default metadata is not being applied, skipping to next file')
                        files_skipped.append(outputName)
                        continue
                    else:
                        print(f'matching row found for {outputName}: row {match_row}; getting csv metadata...')
                        csv_row_data, parentfile = get_csv_metadata(match_row, m_csv)
                        if parentfile != '':
                            print(f'contains parent info: {parentfile}, getting parent file header...')
                            parent_head, lines = assess_parent_header(parentfile, parent_dir)
                            if parent_head != None:
                                print('combining parent file header and metadata from csv...')
                                header_data = get_header_data(parent_head)
                        combined = build_combined_header(header_data, csv_row_data, creation_date, reviewed, default)
                else:
                    if default == True:
                        if reviewed == False:
                            print('no csv and no header, using default unreviewed metadata')
                        else:
                            print('no csv and no header, using default reviewed metadata')
                        combined = build_combined_header(header_data, csv_row_data, creation_date, reviewed, default)
                    else:
                        print('no csv, no header, and default metadata is not being applied, skipping to next file')
                        files_skipped.append(outputName)
                        continue
            else:
                vtt_head, lines = assess_parent_header(newvtt, reviewed_dir)
                header_data = get_header_data(vtt_head)
                csv_row_data = ''
                if m_csv != None:
                    print('checking csv for match...')
                    match_row = find_match(m_csv, outputName)
                    if match_row == -1 and default == True:
                        if reviewed == False:
                            print('no match found, applying default unreviewed metadata')
                        else:
                            print('no match found, applying default reviewed metadata')
                        combined = build_combined_header(header_data, csv_row_data, creation_date, reviewed, default)
                    elif match_row == -1 and default == False:
                        if reviewed == False:
                            print('no match found and default metadata is not being applied, checking conformance only')
                            final_header, forbidden_arrow, forbidden_dupes_in_ya_tupes = check_conformance(header_data, fileExt, default)
                            write_new_header(final_header, outputDir, outputName, newvtt, line_count, fileExt)
                            files_updated.append(outputName)
                            if forbidden_arrow:
                                files_nonconforming.append(outputName + 'header contains restricted arrow substring:\n\t' + forbidden_arrow)
                            if forbidden_dupes_in_ya_tupes:
                                files_nonconforming.append(outputName + 'header has duplicate nonrepeatable elements:\n\t' + forbidden_dupes_in_ya_tupes)
                            continue
                        else:
                            print('no match found and default metadata is not being applied, only updating review history')
                            combined = build_combined_header(header_data, csv_row_data, creation_date, reviewed, default)
                    else:
                        print(f'matching row found for {outputName}: row {match_row}; getting csv metadata...')
                        csv_row_data, parentfile = get_csv_metadata(match_row, m_csv)
                        if parentfile != '':
                            print(f'contains parent info: {parentfile}, getting parent file header...')
                            parent_head, lines = assess_parent_header(parentfile, parent_dir)
                            if parent_head != None:
                                print('combining source header, parent file header, and metadata from csv...')
                                parent_header_data = get_header_data(parent_head)
                                header_data = merge_headers(header_data, parent_header_data, parentfile)
                        combined = build_combined_header(header_data, csv_row_data, creation_date, reviewed, default)
                else:
                    if default == True:
                        if reviewed == False:
                            print('no csv, using default unreviewed metadata')
                        else:
                            print('no csv, using default reviewed metadata')
                        combined = build_combined_header(header_data, csv_row_data, creation_date, reviewed, default)
                    else:
                        if reviewed == False:
                            print('no csv and default metadata is not being applied, checking conformance only')
                            final_header, forbidden_arrow, forbidden_dupes_in_ya_tupes = check_conformance(header_data, fileExt, default)
                            write_new_header(final_header, outputDir, outputName, newvtt, line_count, fileExt)
                            files_updated.append(outputName)
                            if forbidden_arrow:
                                files_nonconforming.append(outputName + 'header contains restricted arrow substring:\n\t' + forbidden_arrow)
                            if forbidden_dupes_in_ya_tupes:
                                files_nonconforming.append(outputName + 'header has duplicate nonrepeatable elements:\n\t' + forbidden_dupes_in_ya_tupes)
                            continue
                        else:
                            print('no csv and default metadata is not being applied, only updating review history')
                            combined = build_combined_header(header_data, csv_row_data, creation_date, reviewed, default)             
            if fileExt == '.txt' and line_count != -2:
                line_count = lines + 1
            final_header, forbidden_arrow, forbidden_dupes_in_ya_tupes = check_conformance(combined, fileExt, default)
            write_new_header(final_header, outputDir, outputName, newvtt, line_count, fileExt)
            files_updated.append(outputName)
            if forbidden_arrow:
                files_nonconforming.append(outputName + 'header contains restricted arrow substring:\n\t' + forbidden_arrow)
            if forbidden_dupes_in_ya_tupes:
                files_nonconforming.append(outputName + 'header has duplicate nonrepeatable elements:\n\t' + forbidden_dupes_in_ya_tupes)
            continue
        else:
            continue
    generate_log(log_source, timenow.strftime("%Y-%m-%d %H:%M:%S%p") + '\n')
    if files_skipped:
        generate_log(log_source, 'Files skipped:')
        for item in files_skipped:
            generate_log(log_source, '\t' + item)
    if files_updated:
        generate_log(log_source, 'Files updated:')
        for item in files_updated:
            generate_log(log_source, '\t' + item)
    if files_nonconforming:
        generate_log(log_source, 'Files with nonconforming data:')
        for item in files_nonconforming:
            generate_log(log_source, '\t' + item)

def main(args_):
    args = setup(args_)
    reviewed_dir = args.reviewed_dir
    parent_dir = args.parentfiles
    default = args.emorydefault
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
        print('webvtt files are: reviewed\n\tscript will update "review history" to "human-reviewed"\n\t(it will also create this element if it doesn\'t exist)')
    else:
        print('webvtt files are: unreviewed\n\tscript will create initial FADGI headers\n\tand check conformance of files with existing FADGI headers')
    if default == True:
        print('default metadata: true\n\tscript will use Emory default metadata set for empty fields')
    else:
        print('default metadata: false\n\tscript will not use Emory default metadata set for empty fields')
    proceed = ask_yes_no('proceed with these settings?')
    if proceed =='Y':
        outputDir = make_output_dir(reviewed_dir)
        update_metadata(reviewed_dir, m_csv, outputDir, parent_dir, reviewed, default)
    else:
        print('exiting. goodbye!')
        sys.exit()

if __name__ == '__main__':
    main(sys.argv[1:])