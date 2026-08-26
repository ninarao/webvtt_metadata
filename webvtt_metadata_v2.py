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
import textwrap

# sys.argv = [
#    '/Users/nraogra/Desktop/webvtt_v2/webvtt_metadata_v2.py',
#    '/Users/nraogra/Desktop/webvtt_v2',
#    '-c',
#    '/Users/nraogra/Desktop/webvtt_v2/webvtt_metadata_locals.csv',
#     '-r',
#     '-e',
#    '-o',
#    '-p', 
#    '/Users/nraogra/Desktop/webvtt_v2',
#    ]

def valid_directory(path_string):
    if not os.path.isdir(path_string):
        raise argparse.ArgumentTypeError(f"'{path_string}' is not a valid directory.")
    return path_string

def valid_csv(path_csv):
    if not path_csv.endswith(".csv"):
        raise argparse.ArgumentTypeError(f"'{path_csv}' is not a valid csv file.")
    else:
        return path_csv
    
def setup(args_):
    parser = argparse.ArgumentParser()
    parser.add_argument("source_dir", type=valid_directory, help="Directory of source files")
    parser.add_argument("-c", "--csv", type=valid_csv, help="Metadata CSV")
    parser.add_argument("-e", "--emorydefault", action="store_true", help="use Emory default metadata set for empty fields")
    parser.add_argument("-r", "--reviewed", action="store_true", help="creates/updates FADGI header for reviewed files")
    parser.add_argument("-o", "--overwrite", action="store_true", help="overwrite repeatable element values instead of appending")
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

def make_output_dir(source_dir):
    outputDir = os.path.join(source_dir, 'metadata_updated')
    print("checking for output folder...")
    if not os.path.exists(outputDir):
        os.mkdir(outputDir)
        print(f'\toutput folder created: \n\t{outputDir}')
    else:
        print(f'\toutput folder already exists: \n\t{outputDir}')
    return outputDir

def get_header_line_count(sourcefile, pattern, fileExt):
    count = 0
    try:
        with open(sourcefile, 'r', encoding='UTF-8') as input:
            for line in input:
                count += 1
                if re.search(pattern, line):
                    count -= 1
                    input.close()
                    return count
    except Exception:
        print('line count error')
        return -4
    if fileExt == '.vtt':
        return -1
    elif fileExt == '.txt':
        with open(sourcefile, 'r', encoding='UTF-8') as input:
            if input.readline() == 'WEBVTT\n':
                count = -3
            else:
                count = -2
            input.close()
            return count

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
    with open(m_csv, 'r', encoding='UTF-8-sig') as metadataFile:
        metadataReader = csv.reader(metadataFile)
        data = list(metadataReader)
        keys = data[0]
        values = data[match_row]
        parentfile = ''
        zipped = list(zip_longest(keys, values, fillvalue=''))
        for key, value in zipped:
            if key.casefold() == "_Parent File".casefold():
                parentfile = value
        csv_row_data = zipped
        return csv_row_data, parentfile

def assess_file(sourcefile):
    justName = Path(sourcefile).stem
    fileExt = Path(sourcefile).suffix
    lines = 0
    if fileExt == '.vtt':
        pattern = r'(\d{2}:\d{2}.\d{3} --> )'
        outputName = justName + ".vtt"
    elif fileExt == '.txt':
        pattern = r'^Type:'
        outputName = justName + ".txt"
    else:
        outputName = ''
        return outputName, lines, fileExt
    lines = get_header_line_count(sourcefile, pattern, fileExt)
    if fileExt == '.txt' and lines >= 0:
        matches = []
        nl_str = '\n'
        with open(sourcefile, 'r', encoding='UTF-8') as input:
            for line_num, line in enumerate(islice(input, lines, None)):
                if line == nl_str:
                    matches.append(line_num)
                    if len(matches) == 1:
                        break
        if len(matches) == 1:
            lines = matches[0] + lines
    return outputName, lines, fileExt

def get_header(sourcefile, lines):
    with open(sourcefile, 'r', encoding='UTF-8') as input:
        parent_head = [next(input) for _ in range(lines)]
    input.close()
    return parent_head, lines

def assess_parent_header(parentfile, parent_dir):
    lines = -1
    if parent_dir is None:
        print('no directory for parent files')
        parent_head = None
        return parent_head, lines
    sourcefile = os.path.join(parent_dir, parentfile)
    if not os.path.isfile(sourcefile):
        print(f'file does not exist: {sourcefile}')
        parent_head = None
        return parent_head, lines
    else:
        outputName, lines, fileExt = assess_file(sourcefile)
        if outputName == '':
            print('file is not .vtt or .txt')
            parent_head = None
        elif (lines == 2 and fileExt == '.vtt') or lines in [-1, -2, -3, -4]:
            parent_head = None
        else:
            parent_head, lines = get_header(sourcefile, lines)
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
        header_locals = [x.replace(']', ':', 1) if ']' in x else x for x in flatlist]
        make_title_case = ['_software version', '_review history']
        for i, x in enumerate(header_locals):
            if x.casefold().startswith(tuple(make_title_case)):
                for y in make_title_case:
                    if x.casefold().startswith(y):
                        header_locals[i] = x[:len(y)].title() + x[len(y):]
                        break
        for index in sorted(chain(indices, lox), reverse=True):
            del parent_head[index]
        parent_head.extend(header_locals)
    for index, item in enumerate(parent_head):
        if ':' not in item:
            parent_head[index] = item + ': ' + item
    parent_head_tuples = [tuple(x.split(': ', 1)) for x in parent_head]
    header_data = parent_head_tuples
    return header_data
    
def merge_headers(vtt_header_data, parent_header_data, source, overwrite):
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
    repeatable_keys = [x.casefold() for x in ['Language', 'Responsible Party', 'Media Identifier', 'File Creator', 'Origin History']]
    p_unique = [x for x in parent_header_data if x[0].casefold() not in vtt_keys]
    p_uniq_nonlocal = list({t for t in p_unique if t and not t[0].startswith('_')})
    p_uniq_local = list({t for t in p_unique if t and t[0].startswith('_')})
    p_append = [x for x in p_locals if x[0].casefold() in loc_append]
    dedupe_append = list(set(p_uniq_local + p_append))
    if overwrite == False:
        p_repeats = [x for x in parent_header_data if x[0].casefold() in repeatable_keys]
        m_header_data = vtt_nonlocal + p_uniq_nonlocal + p_repeats + vtt_locals + dedupe_append
        merged_header_data = list(set(m_header_data))
    else:
        merged_header_data = vtt_nonlocal + p_uniq_nonlocal + vtt_locals + dedupe_append
#     merged_locals = vtt_locals + dedupe_append
    return merged_header_data

def build_combined_header(parent_header_data, csv_row_data, creation_date, reviewed, default, overwrite):
    for key, value in csv_row_data:
        if key.casefold() == "Source File".casefold():
            source = value
            csv_row_data.remove((key, value))
    if csv_row_data != '':
        csv_row_data = [t for t in csv_row_data if t[1] != '']
        if not any('File Creation Date'.casefold() in t[0].casefold() for t in csv_row_data):
            if any('File Creation Date'.casefold() in t[0].casefold() for t in parent_header_data):
                header_date = next((v for k, v in parent_header_data if k.casefold() == 'File Creation Date'.casefold()), '')
                csv_row_data.append(('File Creation Date', header_date))
        combined_header_data = merge_headers(csv_row_data, parent_header_data, source, overwrite)
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
        else:
            combined_header_data = [(t[0], 'human-reviewed') if t[0].casefold() == '_Review History'.casefold() else t for t in combined_header_data]
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
        forbidden_arrow = [': '.join(map(str, t)) for t in forbidden_arrow]
        forbidden_arrow = [textwrap.indent(textwrap.fill(t, width=75), '    ') for t in forbidden_arrow]
        print(f'forbidden_arrow: {forbidden_arrow}')
    nonrepeatable = ['Type', 'Originating File', 'File Creation Date', 'Title']
    seen = set()
    dupes = set()
    for x in sorted_tupes:
        if x[0] in seen:
            dupes.add(x[0])
        else:
            seen.add(x[0])
    forbidden_dupes = [x for x in dupes if x in nonrepeatable]
    forbidden_dupes_in_tupes = set()
    for x in sorted_tupes:
        if x[0] in forbidden_dupes:
            forbidden_dupes_in_tupes.add(x)
    if forbidden_dupes_in_tupes:
        forbidden_dupes_in_tupes = [': '.join(map(str, t)) for t in forbidden_dupes_in_tupes]
        forbidden_dupes_in_tupes = [textwrap.indent(textwrap.fill(t, width=75), '    ') for t in forbidden_dupes_in_tupes]
        print(f'forbidden_dupes_in_tupes: {forbidden_dupes_in_tupes}')
    return sorted_tupes, forbidden_arrow, forbidden_dupes_in_tupes

def write_new_header(final_header, outputDir, outputName, sourcefile, line_count):
    final_header = [t[1:] if (t and not t[0]) else t for t in final_header]
    final_header = [(t[0], (', '.join([str(t[1]), str(t[2])]))) if len(t) == 3 else t for t in final_header]
    final_header = [': '.join(map(str, t)) for t in final_header]
    newfile = os.path.join(outputDir, outputName)
    with open(sourcefile, 'r', encoding='UTF-8') as f_in, open(newfile, 'w', encoding='UTF-8') as f_out:
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
            
def make_log(files_updated, files_skipped, outputDir, files_nonconforming):
    timenow = datetime.datetime.now()
    logname = f'webvtt_metadata_log_{timenow.strftime("%y-%m-%d_%Hh%Mm%Ss")}.txt'
    log_source = os.path.join(outputDir, logname)
    generate_log(log_source, 'WebVTT metadata log for ' + outputDir + '\n')
    if files_skipped:
        generate_log(log_source, 'Files skipped:')
        for item in files_skipped:
            generate_log(log_source, item)
    if files_skipped and files_updated:
        generate_log(log_source, '')
    if files_updated:
        generate_log(log_source, 'Files checked:')
        for item in files_updated:
            generate_log(log_source, item)
    if files_updated and files_nonconforming:
        generate_log(log_source, '')
    elif files_skipped and files_nonconforming and not files_updated:
        generate_log(log_source, '')
    if files_nonconforming:
        generate_log(log_source, 'Files with nonconforming metadata:')
        for item in files_nonconforming:
            generate_log(log_source, item)
    generate_log(log_source, '\nFinished running at ' + timenow.strftime("%Y-%m-%d %H:%M:%S%p") + '\n')

def update_metadata(source_dir, m_csv, outputDir, parent_dir, reviewed, default, overwrite):
    files_updated = []
    files_skipped = []
    files_nonconforming = []
    ext = ['.vtt', '.txt']
    for sourcefile in glob.glob(f'{source_dir}/*{ext}'):
        lines = 0
        line_count = 0
        if os.path.isfile(sourcefile):
            outputName, line_count, fileExt = assess_file(sourcefile)
            if outputName == '':
                continue
            if platform.system() == 'Windows':
                c_timestamp = os.path.getctime(sourcefile)
                datestamp = datetime.datetime.fromtimestamp(c_timestamp)
            else:
                stat = os.stat(sourcefile)
                try:
                    timestamp = stat.st_birthtime
                    datestamp = datetime.datetime.fromtimestamp(timestamp)
                except AttributeError:
                    timestamp = stat.st_mtime
                    datestamp = datetime.datetime.fromtimestamp(timestamp)
            creation_date = datestamp.strftime("%Y-%m-%d")
            print(f'\n{outputName}')
            if line_count == -1:
                print('timestamps not found in file, skipping to next file')
                files_skipped.append(outputName)
                continue
            elif (line_count == 2 and fileExt == '.vtt') or line_count in [-2, -3, -4]:
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
                        combined = build_combined_header(header_data, csv_row_data, creation_date, reviewed, default, overwrite)
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
                        combined = build_combined_header(header_data, csv_row_data, creation_date, reviewed, default, overwrite)
                else:
                    if default == True:
                        if reviewed == False:
                            print('no csv and no header, using default unreviewed metadata')
                        else:
                            print('no csv and no header, using default reviewed metadata')
                        combined = build_combined_header(header_data, csv_row_data, creation_date, reviewed, default, overwrite)
                    else:
                        print('no csv, no header, and default metadata is not being applied, skipping to next file')
                        files_skipped.append(outputName)
                        continue
            else:
                print(f'FADGI header found: {line_count} lines')
                vtt_head, lines = get_header(sourcefile, line_count)
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
                        combined = build_combined_header(header_data, csv_row_data, creation_date, reviewed, default, overwrite)
                    elif match_row == -1 and default == False:
                        if reviewed == False:
                            print('no match found and default metadata is not being applied, checking conformance only')
                            final_header, forbidden_arrow, forbidden_dupes_in_tupes = check_conformance(header_data, fileExt, default)
                            if fileExt == '.txt' and line_count != -2:
                                line_count = lines + 1
                            write_new_header(final_header, outputDir, outputName, sourcefile, line_count)
                            files_updated.append(outputName)
                            if forbidden_arrow:
                                files_nonconforming.append(outputName + ' header contains restricted arrow substring:\n' +
                                                           '\n'.join([str(x) for x in forbidden_arrow]))
                            if forbidden_dupes_in_tupes:
                                files_nonconforming.append(outputName + ' header has duplicate nonrepeatable elements:\n' +
                                                           '\n'.join(map(str, forbidden_dupes_in_tupes)))
                            continue
                        else:
                            print('no match found and default metadata is not being applied, only updating review history')
                            combined = build_combined_header(header_data, csv_row_data, creation_date, reviewed, default, overwrite)
                    else:
                        print(f'matching row found for {outputName}: row {match_row}; getting csv metadata...')
                        csv_row_data, parentfile = get_csv_metadata(match_row, m_csv)
                        if parentfile != '':
                            print(f'contains parent info: {parentfile}, getting parent file header...')
                            parent_head, lines = assess_parent_header(parentfile, parent_dir)
                            if parent_head != None:
                                print('combining source header, parent file header, and metadata from csv...')
                                parent_header_data = get_header_data(parent_head)
                                header_data = merge_headers(header_data, parent_header_data, parentfile, overwrite)
                        combined = build_combined_header(header_data, csv_row_data, creation_date, reviewed, default, overwrite)
                else:
                    if default == True:
                        if reviewed == False:
                            print('no csv, using default unreviewed metadata')
                        else:
                            print('no csv, using default reviewed metadata')
                        combined = build_combined_header(header_data, csv_row_data, creation_date, reviewed, default, overwrite)
                    else:
                        if reviewed == False:
                            print('no csv and default metadata is not being applied, checking conformance only')
                            final_header, forbidden_arrow, forbidden_dupes_in_tupes = check_conformance(header_data, fileExt, default)
                            if fileExt == '.txt' and line_count != -2:
                                line_count = lines + 1
                            write_new_header(final_header, outputDir, outputName, sourcefile, line_count)
                            files_updated.append(outputName)
                            if forbidden_arrow:
                                files_nonconforming.append(outputName + ' header contains restricted arrow substring:\n' +
                                                           '\n'.join([str(x) for x in forbidden_arrow]))
                            if forbidden_dupes_in_tupes:
                                files_nonconforming.append(outputName + ' header has duplicate nonrepeatable elements:\n' +
                                                           '\n'.join(map(str, forbidden_dupes_in_tupes)))
                            continue
                        else:
                            print('no csv and default metadata is not being applied, only updating review history')
                            combined = build_combined_header(header_data, csv_row_data, creation_date, reviewed, default, overwrite)             
            final_header, forbidden_arrow, forbidden_dupes_in_tupes = check_conformance(combined, fileExt, default)
            if fileExt == '.txt':
                if line_count not in [-1, -2, -3, -4]:
                    line_count = lines + 1
                elif line_count == -3:
                    line_count = 2
            write_new_header(final_header, outputDir, outputName, sourcefile, line_count)
            files_updated.append(outputName)
            if forbidden_arrow:
                files_nonconforming.append(outputName + ' header contains restricted arrow substring:\n' +
                                           '\n'.join([str(x) for x in forbidden_arrow]))
            if forbidden_dupes_in_tupes:
                files_nonconforming.append(outputName + ' header has duplicate nonrepeatable elements:\n' +
                                           '\n'.join(map(str, forbidden_dupes_in_tupes)))
            continue
        else:
            continue
    return files_updated, files_skipped, outputDir, files_nonconforming

def main(args_):
    args = setup(args_)
    source_dir = args.source_dir
    parent_dir = args.parentfiles
    default = args.emorydefault
    reviewed = args.reviewed
    overwrite = args.overwrite
    print('*** webvtt metadata - settings chosen: ***')
    print(f'source vtt directory:\n\t{source_dir}')
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
        print('source files are: reviewed\n\tscript will update "review history" to "human-reviewed"\n\t(it will also create this element if it doesn\'t exist)')
    else:
        print('source files are: unreviewed\n\tscript will create initial FADGI headers\n\tand check or update existing FADGI headers'
              '\n\texisting "review history" elements will not be changed')
    if default == True:
        print('default metadata: true\n\tscript will use Emory default metadata set for empty fields')
    else:
        print('default metadata: false\n\tscript will not use Emory default metadata set for empty fields')
    if overwrite == True:
        print('overwrite mode:\n\tscript will overwrite existing repeatable element values if new values are given')
    else:
        print('append mode:\n\tscript will append repeatable element values and preserve any existing values')
    proceed = ask_yes_no('proceed with these settings?')
    if proceed =='Y':
        outputDir = make_output_dir(source_dir)
        files_updated, files_skipped, outputDir, files_nonconforming = update_metadata(source_dir, m_csv, outputDir, parent_dir, reviewed, default, overwrite)
        make_log(files_updated, files_skipped, outputDir, files_nonconforming)
    else:
        print('exiting. goodbye!')
        sys.exit()

if __name__ == '__main__':
    main(sys.argv[1:])
