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
import pandas as pd

# sys.argv = [
#    '/Users/nraogra/Desktop/Captioning/webvtt_metadata-main/webvtt_metadata_export.py',
#    '/Users/nraogra/Desktop/Captioning/webvtt_metadata-main/samplefiles',
#    '-c',
#    '/Users/nraogra/Desktop/Captioning/webvtt_metadata-main/samplefiles/m-metadata.csv',
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

def setup(args_):
    parser = argparse.ArgumentParser()
    parser.add_argument("source_dir", type=valid_directory, help="Directory of source files")
    parser.add_argument("-c", "--csv", type=valid_csv, help="Metadata CSV")
    args = parser.parse_args(args_)
    return args

def make_export_csv(source_dir, m_csv):
    if m_csv == None:
        export_csv = Path(source_dir) / 'metadata.csv'
    else:
        export_csv = Path(m_csv)
    if export_csv.is_file():
        overwrite_csv = ask_yes_no(f'{export_csv} already exists, do you want to overwrite?')
        if overwrite_csv == 'Y':
            print("overwriting contents of csv")
        else:
            print("appending to contents of csv")
    else:
        create_csv = Path(export_csv)
        create_csv.parent.mkdir(parents=True, exist_ok=True)
        create_csv.touch(exist_ok=True)
        overwrite_csv = 'NA'
    return export_csv, overwrite_csv

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

def write_metadata(outputName, header_data, fileExt, export_csv):
    header_data.insert(0, ('File Extension', fileExt))
    header_data.insert(0, ('File Name', outputName))
    df = pd.DataFrame(header_data).T
    df.to_csv(export_csv, mode="a", encoding="utf-8", header=False, index=False)

def get_metadata(source_dir, export_csv, overwrite_csv):
    files_skipped = []
    files_nonconforming = []
    ext = ['.vtt', '.txt']
    if overwrite_csv == 'Y':
        with open(export_csv, "w", encoding='utf-8') as f:
            f.close
    for sourcefile in glob.glob(f'{source_dir}/*{ext}'):
        lines = 0
        line_count = 0
        if os.path.isfile(sourcefile):
            outputName, line_count, fileExt = assess_file(sourcefile)
            if outputName == '':
                continue
            print(f'\n{outputName}')
            if line_count == -1:
                print('timestamps not found in file, skipping to next file')
                files_skipped.append(outputName)
                continue
            elif (line_count == 2 and fileExt == '.vtt') or line_count in [-2, -3, -4]:
                print('no FADGI comment block detected')
                files_skipped.append(outputName)
                continue
            else:
                print(f'FADGI comment block found: {line_count} lines')
                vtt_head, lines = get_header(sourcefile, line_count)
                header_data = get_header_data(vtt_head)
                print(header_data)
                # conformance check?
                # files_nonconforming.append
                write_metadata(outputName, header_data, fileExt, export_csv)
    return files_skipped, files_nonconforming

# def make_log(files_skipped, files_nonconforming):


def main(args_):
    args = setup(args_)
    source_dir = args.source_dir
    print('*** webvtt metadata export - settings chosen: ***')
    print(f'source file directory:\n\t{source_dir}')
    if args.csv != None:
        m_csv = args.csv
        print(f'export csv:\n\t{m_csv}')
    else:
        m_csv = None
        print('export csv will be created in source file directory')
    proceed = ask_yes_no('proceed with these settings?')
    if proceed == 'Y':
        export_csv, overwrite_csv = make_export_csv(source_dir, m_csv)
        files_skipped, files_nonconforming = get_metadata(source_dir, export_csv, overwrite_csv)
#         make_log(files_skipped, files_nonconforming)
    else:
        print('exiting. goodbye!')
        sys.exit()

if __name__ == '__main__':
    main(sys.argv[1:])