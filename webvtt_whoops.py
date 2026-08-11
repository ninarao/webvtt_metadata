#!/usr/bin/env python3

import os
import sys
import glob
from pathlib import Path
import csv
import re
import argparse
import shutil
from itertools import islice

sys.argv = [
   'webvtt_whoops.py',
   '/Users/nraogra/Desktop/webvtt_v2', 
   '-t'
   ]
# /Users/nraogra/Desktop/webvtt_v2/webvtt_metadata_locals.csv

def setup(args_):
    parser = argparse.ArgumentParser(
        description='test description')
    parser.add_argument(
        'source',
        help='directory of files'
    )
    parser.add_argument(
        "-t",
        "--txtheader",
        action="store_true",
        help="apply to txt files also"
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

def append_or_overwrite(source, element_choice, localYN):
    while True:
        print(f'\nWebVTT directory: {source}')
        if localYN == 'N':
            print(f'\n{element_choice} is a repeatable element. Would you like to append to or overwrite existing values?\n')
        else:
            print(f'\nFor local usage element "{element_choice}" would you like to append to or overwrite existing values?\n')
        print('1. Append')
        print('2. Overwrite')
        print('Q. Quit to main menu')
        print('\n')
        answer = input()
        if answer == '1':
            mode = 'append'
            return mode
        elif answer == '2':
            mode = 'overwrite'
            return mode
        elif answer in ('Q', 'q'):
            print(' - Returning to main menu')
            mode = 'quit'
            return mode
        else:
            print(' - Incorrect input. Please enter enter 1, 2, or Q')
    
def revise_element(source, element_choice, outputDir, localYN):
    while True:
        print(f'\nWebVTT directory: {source}')
        print(f'Element selected: {element_choice}')
        print('\nWhat would you like to do?')
        print('1. Revise element from CSV (will match on WebVTT filenames)')
        print('2. Input new element value (will apply same value to all WebVTT files)')
        print('Q. Quit to main menu')
        print('\n')
        choice = input('Enter your option: ').strip().upper()
        if choice in ['1', '2', 'Q', 'q']:
            return choice
        else:
            print(' - Incorrect input. Please enter 1, 2, or Q')

def get_csv_info(source, element_choice, localYN):
    print('Revising from CSV')
    while True:
        m_csv = input('\n\n**** Enter CSV with full path (or Q to return to main menu):     ')
        col_index = ''
        if m_csv in ['Q', 'q']:
            m_csv = ''
            return m_csv, col_index
        if not (os.path.isfile(m_csv) and m_csv.endswith(".csv")):
            print(f"'{m_csv}' is not a csv file.")
            continue
        source = os.path.abspath(source)
        print(m_csv)
        if localYN == 'Y':
            element_choice = '_' + element_choice
        with open(m_csv, 'r', encoding='UTF-8') as mFile:
            mReader = csv.reader(mFile)
            try:
                header_row = next(mReader)
                header_row_lower = [x.casefold() for x in header_row]
                if element_choice.casefold() in header_row_lower:
                    col_index = header_row_lower.index(element_choice.casefold())
                    print(f'Element "{element_choice}" in header row {col_index}.')
                else:
                    print(f'Element "{element_choice}" not found in header row.\n')
                    m_csv = ''
                return m_csv, col_index
            except StopIteration:
                print('CSV is empty or has no headers.\n')
                m_csv = ''
                return m_csv, col_index

def update_vtt(source, m_csv, element_choice, col_index, outputDir, localYN, txt_header, mode):
    if m_csv == "" and element_choice != 'NOTE':
        while True:
            bulk_val = input(f'\n\n**** Input new value for element "{element_choice}":     ')
            if mode == 'append':
                print(f'New value: "{bulk_val}". Append "{element_choice}: {bulk_val}" to header.')
            elif mode == 'overwrite':
                print(f'New value: "{bulk_val}". Overwrite existing "{element_choice}" value(s) with "{element_choice}: {bulk_val}".')
            proceed_yn = ask_yes_no(f'Proceed?')
            if proceed_yn == 'Y':
                break
            else:
                print('\nReturning to main menu.')
                status = 'mainmenu'
                return status
    ext = ['.vtt', '.txt']
#     if localYN == 'Y':
#         element_choice = '_' + element_choice
    for vttfile in glob.glob(f'{source}/*{ext}'):
        if os.path.isfile(vttfile):
            justName = Path(vttfile).stem
            fileExt = Path(vttfile).suffix
            if fileExt == '.vtt':
                outputName = justName + ".vtt"
                print(outputName)
                pattern = r'(\d{2}:\d{2}.\d{3} --> )'
            elif fileExt == '.txt' and txt_header == True:
                outputName = justName + ".txt"
                print(outputName)
                pattern = r'^Type:'
            else:
                continue
            count = count_file_header(vttfile, pattern, fileExt)
            line_count = -1
            if count != -1:
                elementline, orig_head, line_count = find_element_header(count, vttfile, element_choice, localYN)
                print(f'{outputName}: Element "{element_choice}" found in header line: {elementline}')
            if m_csv != "":
                new_val = find_file(outputName, m_csv, col_index)
            else:
                new_val = bulk_val
            if m_csv != "" and new_val == '':
                print(f'{outputName}: file not found in csv, skipping file.')
                continue
            if any(x.endswith('\n') for x in elementline):
                new_val = element_choice + ': ' + new_val + '\n'
            if localYN == 'Y':
                new_val = '_' + new_val
                if elementline:
                    print(f'orig_head: {orig_head}')
                    print(f'elementline: {elementline}')
            if mode == 'overwrite':
                print(f'{outputName}: New value for element "{element_choice}": "{new_val}"')
                orig_head = [new_val if x in elementline else x for x in orig_head]
                new_head = []
                dupes_found = False
                for x in orig_head:
                    if x == new_val:
                        if not dupes_found:
                            new_head.append(x)
                            dupes_found = True
                    else:
                        new_head.append(x)
            if mode == 'append':
                print(f'{outputName}: Additional value for element "{element_choice}": "{new_val}"')
                orig_head.insert(line_count+1, new_val)
                new_head = orig_head
            if element_choice == 'NOTE':
                line_count = count - 1
                if elementline == "":
                    print(f'{outputName}: "{element_choice}" not found, adding to header')
                    try:
                        index = [i for i, s in enumerate(orig_head) if 'Type' in s]
                    except ValueError:
                        print('error: not found')
                    if index:
                        index_int = index[0]
                    else:
                        index_int = 0
                    new_val = 'NOTE\n'
                    orig_head.insert(index_int, new_val)
                    new_head = orig_head
                elif elementline != "":
                    print(f'{outputName}: "{element_choice}" found in header, skipping file.')
                    continue
            else:
                if elementline == "" or line_count == -1:
                    print(f'{outputName}: Element "{element_choice}" not found in header, skipping file.')
                    continue
            newfile = os.path.join(outputDir, outputName)
            with open(vttfile, 'r', encoding='UTF-8') as f_in, open(newfile, 'w', encoding='UTF-8') as f_out:
                for item in new_head:
                    f_out.write(item)
                for _ in range(count):
                    next(f_in, None)
                shutil.copyfileobj(f_in, f_out)
            f_in.close()
            f_out.close()
        
def count_file_header(vttfile, pattern, fileExt):
    count = 0
    found = ''
    try:
        with open(vttfile, 'r', encoding='UTF-8') as input:
            for line in input:
                count += 1
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
                    print(f'FADGI header found: {count} lines')
                    return count
    except Exception:
        print('header line count error')
        return -1
    if found == '':
        print('no FADGI header detected in file')
        return -1

def find_element_header(count, vttfile, element_choice, localYN):
    elementline = []
    orig_head = []
    line_count = []
    with open(vttfile, 'r', encoding='UTF-8') as input:
        for i, line in enumerate(input):
            if i >= count:
                break
            orig_head.append(line)
            if localYN == 'Y':
                if line.casefold().startswith('Local Usage Element'.casefold()) and element_choice.casefold() in line:
                    elementline.append(line)
                    line_count.append(i)
                if line.casefold().startswith(('_'+element_choice).casefold()):
                    elementline.append(line)
                    line_count.append(i)
            else:
                if line.casefold().startswith(element_choice.casefold()):
                    elementline.append(line)
                    line_count.append(i)
    if not line_count:
        line_count = -1
    else:
        line_count = max(line_count)
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
    print('N. Add NOTE if missing from header')
    print('Q. Quit')
    
def run_main(source, outputDir):
    while True:
        main_menu(source)
        choice = input('\nEnter your option: ').strip().upper()
        elements = ['Type', 'Language', 'Responsible Party',
                    'Media Identifier', 'Originating File',
                    'File Creator', 'File Creation Date', 'Title',
                    'Origin History', 'Local Usage Element']
        element_dict = {str(index+1): element for index, element in enumerate(elements)}
        menu_list = [str(x) for x in range(1,10)]
        repeatable_list = [str(x) for x in [2, 3, 4, 6, 9]]
        localYN = 'N'
        if choice in repeatable_list:
            element_choice = element_dict[choice]
            mode = append_or_overwrite(source, element_choice, localYN)
            print(f'mode: {mode}')
            if mode in ('append', 'overwrite'):
                return mode, element_choice, localYN
        elif choice in menu_list:
            element_choice = element_dict[choice]
            mode = 'overwrite'
            print(f'mode: {mode}')
            return mode, element_choice, localYN
        elif choice == '10':
            localYN = 'Y'
            while True:
                element_choice = input('\n\n**** Input name of local usage element (without underscore prefix):     ')
                proceed_yn = ask_yes_no(f'Local usage element: "{element_choice}". Is this correct?')
                if proceed_yn == 'Y':
                    mode = append_or_overwrite(source, element_choice, localYN)
                    print(f'mode: {mode}')
                    return mode, element_choice, localYN
                else:
                    print('\nReturning to main menu.')
                    break
        elif choice.upper() == 'N':
            m_csv = ""
            element_choice = 'NOTE'
            col_index = ""
            update_vtt(source, m_csv, element_choice, col_index, outputDir, localYN, txt_header, mode)
        elif choice.upper() == 'Q':
            print(' - Exiting program. Goodbye!')
            mode = 'QUIT'
            element_choice = ''
            localYN = ''
            return mode, element_choice, localYN
        else:
            print(f' - Incorrect input. Please enter {", ".join(menu_list)}, or Q\n')

def main(args_):
    args = setup(args_)
    source = args.source
    if not os.path.isdir(source):
        print(f"No directory {source} exists, exiting program.")
        sys.exit()
    if args.txtheader == True:
        print("\nActions will be applied to txt and vtt files.")
        txt_header = True
    else:
        print("\nActions will be applied to vtt files.")
        txt_header = False
    outputDir = make_output_dir(source)
    while True:
        mode, element_choice, localYN = run_main(source, outputDir)
        if mode == 'quit':
            continue
        if mode == 'QUIT':
            break
        choice = revise_element(source, element_choice, outputDir, localYN)
        print(f'choice: {choice}')
        if choice == '1':
            m_csv, col_index = get_csv_info(source, element_choice, localYN)
            if col_index == '':
                continue
            if col_index != '':
                status = update_vtt(source, m_csv, element_choice, col_index, outputDir, localYN, txt_header, mode)
        elif choice == '2':
            m_csv = ''
            col_index = ''
            status = update_vtt(source, m_csv, element_choice, col_index, outputDir, localYN, txt_header, mode)
            if status == 'mainmenu':
                continue
        elif choice in ['Q', 'q']:
            print(' - Returning to main menu')
            continue
        else:
            break

if __name__ == '__main__':
    main(sys.argv[1:])