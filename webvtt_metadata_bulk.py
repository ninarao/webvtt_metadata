#!/usr/bin/env python3

import os
import sys
import glob
from pathlib import Path
import csv
import re
import argparse
import shutil
from itertools import zip_longest, islice, chain
import datetime
import textwrap

# sys.argv = [
#    '/Users/nraogra/Desktop/webvtt_v2/webvtt_metadata_bulk.py',
#    '-c',
#    '/Users/nraogra/Desktop/webvtt_v2/webvtt_metadata_locals.csv', 
#    '/Users/nraogra/Desktop/webvtt_v2',
#    '-o',
#    '-t'
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
    parser.add_argument("-o", "--overwrite", action="store_true", help="overwrite existing webvtt metadata blocks instead of skipping")
    parser.add_argument("-t", "--txt-type", nargs='?', const='blank', default='same', help="set a different Type value for txt files (if used without a value, will set Type as blank for txt files)")
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

def generate_log(log, what2log):
    if not os.path.isfile(log):
        with open(log, "w", encoding='utf-8') as f:
            f.write(what2log + '\n')
    else:
        with open(log, "a", encoding='utf-8') as f:
            f.write(what2log + '\n')

def get_csv_metadata(m_csv):
    with open(m_csv, 'r', encoding='UTF-8-sig') as metadataFile:
        metadataReader = csv.reader(metadataFile)
        data = list(metadataReader)
        try:
            keys = data[0]
            values = data[2]
            csv_row_data = list(zip_longest(keys, values, fillvalue=''))
            csv_row_data = [t for t in csv_row_data if t[1] != '']
            for key, value in csv_row_data:
                if key.casefold() == "Source File".casefold():
                    csv_row_data.remove((key, value))
            return csv_row_data
        except:
            csv_row_data = ''
            return csv_row_data

def check_conformance(csv_row_data):
    arrow = '-->'
    forbidden_arrow = [t for t in csv_row_data if any(arrow in str(x) for x in t)]
    nonrepeatable = ['Type', 'Originating File', 'File Creation Date', 'Title']
    seen = set()
    dupes = set()
    for x in csv_row_data:
        if x[0] in seen:
            dupes.add(x[0])
        else:
            seen.add(x[0])
    forbidden_dupes = [x for x in dupes if x in nonrepeatable]
    forbidden_dupes_in_tupes = set()
    for x in csv_row_data:
        if x[0] in forbidden_dupes:
            forbidden_dupes_in_tupes.add(x)
    if forbidden_dupes_in_tupes:
        forbidden_dupes_in_tupes = [': '.join(map(str, t)) for t in forbidden_dupes_in_tupes]
        forbidden_dupes_in_tupes = [textwrap.fill(t, width=75) for t in forbidden_dupes_in_tupes]
    return forbidden_arrow, forbidden_dupes_in_tupes

def count_file_header(sourcefile, pattern, fileExt):
    count = 0
    found = ''
    webvtt = 'no'
    try:
        with open(sourcefile, 'r', encoding='UTF-8') as input:
            for line in input:
                count += 1
                if re.search('WEBVTT\n', line):
                    webvtt = 'yes'
                if re.search(pattern, line):
                    count -= 1
                    found = 'yes'
                    if fileExt == '.txt' and found == 'yes':
                        matches = []
                        nl_str = '\n'
                        for line_num, line in enumerate(islice(input, None)):
                            if line == nl_str:
                                matches.append(line_num)
                                if len(matches) == 1:
                                    break
                        if len(matches) == 1:
                            count = matches[0] + count + 1
                    input.close()
                    return count
    except Exception:
        print('header line count error')
        return -1
    if found == '' and fileExt == '.vtt':
        return -2
    if found == '' and webvtt == 'no' and fileExt == '.txt':
        return -1
    if found == '' and webvtt == 'yes' and fileExt == '.txt':
        return -3

def build_header(csv_row_data, txt_type, fileExt):
    ref_list = ['Header', 'Note', 'Type', 'Language', 'Responsible Party',
            'Media Identifier', 'Originating File', 'File Creator',
            'File Creation Date', 'Title', 'Origin History']
    order_map = {key.lower(): index for index, key in enumerate(ref_list)}
    header = sorted(csv_row_data, key=lambda x: (order_map.get(x[0].lower(), float('inf')), x[0].lower(), id(x)))
    type_str = 'Type'
    if fileExt == '.vtt':
        header.insert(0, ('', 'WEBVTT'))
        header.insert(1, ('', ''))
        header.insert(2, ('', 'NOTE'))
    if fileExt == '.txt':
        type_index = next((i for i, s in enumerate(header) if type_str.casefold() in s[0].casefold()), -1)
        if type_index == -1:
            if txt_type in ['blank', 'same']:
                header.insert(0, ('Type', ''))
            else:
                header.insert(0, ('Type', txt_type))
        else:
            if txt_type == 'blank':
                type_update = ('Type', '')
                header[type_index] = type_update
            elif txt_type != 'same':
                type_update = ('Type', txt_type)
                header[type_index] = type_update
    header.append(('', ''))
    return header

def write_new_header(header, outputDir, outputName, sourcefile, line_count):
    header = [t[1:] if (t and not t[0]) else t for t in header]
    header = [(t[0], (', '.join([str(t[1]), str(t[2])]))) if len(t) == 3 else t for t in header]
    header = [': '.join(map(str, t)) for t in header]
    newfile = os.path.join(outputDir, outputName)
    with open(sourcefile, 'r', encoding='UTF-8') as f_in, open(newfile, 'w', encoding='UTF-8') as f_out:
        for item in header:
            f_out.write(f'{item}\n')
        for _ in range(line_count):
            next(f_in, None)
        shutil.copyfileobj(f_in, f_out)
    f_in.close()
    f_out.close()

def update_metadata(source_dir, overwrite, csv_row_data, txt_type, outputDir):
    files_updated = []
    files_skipped = []
    ext = ['.vtt', '.txt']
    for sourcefile in glob.glob(f'{source_dir}/*{ext}'):
        lines = 0
        if os.path.isfile(sourcefile):
            justName = Path(sourcefile).stem
            fileExt = Path(sourcefile).suffix
            if fileExt == '.vtt':
                outputName = justName + ".vtt"
                pattern = r'(\d{2}:\d{2}.\d{3} --> )'
            elif fileExt == '.txt':
                outputName = justName + ".txt"
                pattern = r'^Type:'
            else:
                continue
        line_count = count_file_header(sourcefile, pattern, fileExt)
        if line_count == -2:
            print(f'{outputName}: timestamps not found, skipping file')
            files_skipped.append(outputName)
            continue
        elif (line_count == 2 and fileExt == '.vtt') or line_count in [-1, -3]:
            print(f'{outputName}: no FADGI header detected')
            header = build_header(csv_row_data, txt_type, fileExt)
            if fileExt == '.txt':
                line_count = line_count + 1
            write_new_header(header, outputDir, outputName, sourcefile, line_count)
            files_updated.append(outputName)
        else:
            if overwrite == False:
                print(f'{outputName}: has existing webvtt metadata block, skipping file')
                files_skipped.append(outputName)
                continue
            else:
                print(f'{outputName}: overwriting existing webvtt metadata block')
                header = build_header(csv_row_data, txt_type, fileExt)
                if fileExt == '.txt':
                    line_count = line_count + 1
                write_new_header(header, outputDir, outputName, sourcefile, line_count)
                files_updated.append(outputName)
    return files_updated, files_skipped
    
def make_log(files_updated, files_skipped, outputDir, forbiddens):
    timenow = datetime.datetime.now()
    logname = f'webvtt_metadata_log_{timenow.strftime("%y-%m-%d_%Hh%Mm%Ss")}.txt'
    log_source = os.path.join(outputDir, logname)
    generate_log(log_source, 'WebVTT metadata bulk log for ' + outputDir + '\n')
    if files_skipped:
        generate_log(log_source, 'Files skipped:')
        for item in files_skipped:
            generate_log(log_source, item)
    if files_skipped and files_updated:
        generate_log(log_source, '')
    if files_updated:
        generate_log(log_source, 'Files updated:')
        for item in files_updated:
            generate_log(log_source, item) 
    if forbiddens:
        generate_log(log_source, '')
        generate_log(log_source, 'Nonconforming metadata elements:')
        for item in forbiddens:
            generate_log(log_source, item)
    generate_log(log_source, '\nFinished running at ' + timenow.strftime("%Y-%m-%d %H:%M:%S%p") + '\n')
            
def main(args_):
    args = setup(args_)
    source_dir = args.source_dir
    m_csv = args.csv
    overwrite = args.overwrite
    txt_type = args.txt_type
    print('*** webvtt_metadata bulk version ***')
    print(f'source file directory:\n\t{source_dir}')
    print(f'metadata csv:\n\t{m_csv}')
    if overwrite == True:
        print('overwrite mode:\n\tscript will overwrite existing webvtt metadata blocks instead of skipping')
    else:
        print('skip mode:\n\tscript will skip files with existing webvtt metadata blocks')
    outputDir = make_output_dir(source_dir)
    csv_row_data = get_csv_metadata(m_csv)
    if csv_row_data == '':
        print('\ncsv header row (row 1) or metadata row (row 3) is empty')
    else:
        forbidden_arrow, forbidden_dupes_in_tupes = check_conformance(csv_row_data)
        if forbidden_arrow or forbidden_dupes_in_tupes:
            while True:
                print('\ncsv contains nonconforming metadata:')
                if forbidden_arrow:
                    forbidden_arrow = [': '.join(map(str, t)) for t in forbidden_arrow]
                    print('substring "-->" is not allowed in WebVTT comment blocks')
                    print(f'\t{"\n\t".join(map(str, forbidden_arrow))}')
                if forbidden_dupes_in_tupes:
                    print('duplicate nonrepeatable elements')
                    print(f'\t{"\n\t".join(forbidden_dupes_in_tupes)}')
                proceed_yn = ask_yes_no('do you want to continue?')
                if proceed_yn == 'Y':
                    forbiddens = list(chain(forbidden_arrow, forbidden_dupes_in_tupes))
                    files_updated, files_skipped = update_metadata(source_dir, overwrite, csv_row_data, txt_type, outputDir)
                    make_log(files_updated, files_skipped, outputDir, forbiddens)
                    break
                else:
                    break
        else:
            forbiddens = ''
            files_updated, files_skipped = update_metadata(source_dir, overwrite, csv_row_data, txt_type, outputDir)
            make_log(files_updated, files_skipped, outputDir, forbiddens)

if __name__ == '__main__':
    main(sys.argv[1:])