#!/usr/bin/env python3

import os
import sys
import glob
from pathlib import Path
import csv
import re
import argparse
import shutil

sys.argv = [
    'webvtt_metadata.py',
    '/Users/nraogra/Desktop/iPres2025/WebVTT_metadata/webvtt_files/metadata_updated'
    ]
# /Users/nraogra/Desktop/iPres2025/WebVTT_metadata/webvtt_metadata.csv

def setup(args_):
    parser = argparse.ArgumentParser(
        description='test description')
    parser.add_argument(
        'source',
        help='directory of files'
    )
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

def make_output_dir(source):
    outputDir = os.path.join(source, 'metadata_updated')
    print("checking for output folder...")
    if not os.path.exists(outputDir):
        os.mkdir(outputDir)
        print(f'\toutput folder created: \n\t{outputDir}')
    else:
        print(f'\toutput folder already exists: \n\t{outputDir}')
    return outputDir

def revise_menu(source, element_choice):
    print(f'\nWebVTT directory: {source}')
    print(f'Element selected: {element_choice}')
    print('\nWhat would you like to do?')
    print('1. Revise element from CSV (will match on WebVTT filenames)')
    print('2. Input new element value (will apply same value to all WebVTT files)')
    print('Q. Quit to main menu')
    print('\n')
    
def revise_element(source, element_choice, outputDir, localYN):
    while True:
        revise_menu(source, element_choice)
        choice = input('Enter your option: ').strip().upper()
        if choice == '1':
            get_csv_info(source, element_choice, outputDir, localYN)
        elif choice == '2':
            m_csv = ""
            col_index = ""
            update_vtt(source, m_csv, element_choice, col_index, outputDir, localYN)
        elif choice in ['Q', 'q']:
            print(' - Returning to main menu')
            break
        else:
            print(' - Incorrect input. Please enter 1, 2, or Q')

def get_csv_info(source, element_choice, outputDir, localYN):
    print('Revising from CSV')
    m_csv = input('\n\n**** Enter CSV with full path):     ')
    if not os.path.isfile(m_csv):
        print(f"'{m_csv}' is not a file.")
        return
    if not m_csv.endswith(".csv"):
        print(f"'{m_csv}' is not a csv file.")
        return
    source = os.path.abspath(source)
    print(m_csv)
    with open(m_csv, 'r', encoding='UTF-8') as mFile:
        mReader = csv.reader(mFile)
        try:
            header_row = next(mReader)
            if element_choice in header_row:
                col_index = header_row.index(element_choice)
                print(f'Element "{element_choice}" in header row {col_index}.')
                update_vtt(source, m_csv, element_choice, col_index, outputDir, localYN)
            else:
                print(f'Element "{element_choice}" not found in header row.\n')
                return
        except StopIteration:
            print('CSV is empty or has no headers.\n')
            return

def update_vtt(source, m_csv, element_choice, col_index, outputDir, localYN):
    if localYN == 'Y':
        element_choice = 'Local Usage Element: ' + element_choice
    if m_csv == "":
        while True:
            bulk_val = input(f'\n\n**** Input new element value to apply for field "{element_choice}":     ')
            proceed_yn = ask_yes_no(f'New value: "{bulk_val}". Update header line to "{element_choice}: {bulk_val}" for all WebVTT files in directory?')
            if proceed_yn == 'Y':
                break
            else:
                print('\nReturning to menu.')
                return
    for vttfile in glob.glob(f'{source}/*.vtt'):
        justName = Path(vttfile).stem
        outputName = justName + ".vtt"
        count = count_file_header(vttfile)
        elementline, orig_head, line_count = find_element_header(count, vttfile, element_choice)
        if elementline == "":
            print(f'{outputName}: Element "{element_choice}" not found in header, skipping file.')
            continue
        if line_count != -1:
            print(f'{outputName}: Element "{element_choice}" found in header line: {elementline}')
        if m_csv != "":
            new_val = find_file(outputName, m_csv, col_index)
        else:
            new_val = bulk_val
        if elementline.endswith('\n'):
            new_val = element_choice + ': ' + new_val + '\n'
        print(f'{outputName}: New value for element "{element_choice}": "{new_val}"')
        new_head = [new_val if x == elementline else x for x in orig_head]
        newfile = os.path.join(outputDir, outputName)
        with open(vttfile, 'r', encoding='UTF-8') as f_in, open(newfile, 'w', encoding='UTF-8') as f_out:
            for item in new_head:
                f_out.write(item)
            for _ in range(line_count+1):
                next(f_in, None)
            shutil.copyfileobj(f_in, f_out)
        f_in.close()
        f_out.close()
        
def count_file_header(vttfile):
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
        print('header line count error')
        return -1

def find_element_header(count, vttfile, element_choice):
    elementline = ""
    orig_head = []
    line_count = -1
    with open(vttfile, 'r', encoding='UTF-8') as input:
        for i, line in enumerate(input):
            if i >= count:
                break
            orig_head.append(line)
            if element_choice in line:
                elementline = line
                line_count = i
                break
    return elementline, orig_head, line_count

def find_file(outputName, m_csv, col_index):
    with open(m_csv, 'r', encoding='UTF-8') as mFile:
        mReader = csv.reader(mFile)
        match = False
        for row_num, row in enumerate(mReader):
            if row[0] == outputName:
                match = True
                new_val = row[col_index]
                return new_val
        if not match:
            new_val = ''
            return new_val

def main_menu(source):
    print(f'\nWebVTT directory: {source}')
    print('\nWhich element would you like to revise?\n')
    print('1. Type')
    print('2. Language')
    print('3. Responsible Party')
    print('4. Media Identifier')
    print('5. Originating File')
    print('6. File Creator')
    print('7. File Creation Date')
    print('8. Title')
    print('9. Origin History')
    print('10. Local Usage Element (any)')
    print('Q. Quit')

def main(args_):
    args = setup(args_)
    source = args.source
    if not os.path.isdir(source):
        print(f"No directory {source} exists, exiting program.")
        sys.exit()
    outputDir = make_output_dir(source)
    while True:
        main_menu(source)
        choice = input('\nEnter your option: ').strip().upper()
        elements = ['Type', 'Language', 'Responsible Party',
                    'Media Identifier', 'Originating File',
                    'File Creator', 'File Creation Date', 'Title',
                    'Origin History', 'Local Usage Element']
        element_dict = {str(index+1): element for index, element in enumerate(elements)}
        menu_list = [str(x) for x in range(1,10)]
        if choice in menu_list:
            element_choice = element_dict[choice]
            localYN = 'N'
            revise_element(source, element_choice, outputDir, localYN)
        elif choice == '10':
            localYN = 'Y'
            while True:
                element_choice = input('\n\n**** Input name of local usage element:     ')
                proceed_yn = ask_yes_no(f'New value: "Local Usage Element: {element_choice}". Is this correct?')
                if proceed_yn == 'Y':
                    revise_element(source, element_choice, outputDir, localYN)
                    break
                else:
                    print('\nReturning to menu.')
                    break
        elif choice == 'Q':
            print(' - Exiting program. Goodbye!')
            break
        else:
            print(f' - Incorrect input. Please enter {", ".join(menu_list)}, or Q\n')

if __name__ == '__main__':
    main(sys.argv[1:])