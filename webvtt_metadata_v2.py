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

# elements (repeatable?)
#     Type (no)
#     Language (yes)
#     Responsible Party (yes)
#     Media Identifier (yes)
#     Originating File (no)
#     File Creator (yes)
#     File Creation Date (no)
#     Title (no)
#     Origin History (yes)
#     Local (yes)

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
    note_tuple = ('NOTE', 'NOTE')
    if note_tuple in parent_head_tuples:
        parent_head_tuples.remove(note_tuple)
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
#     base_tupes = [(x, '') for x in keys]
    csv_row_data = [t for t in csv_row_data if t[1] != '']
    csv_locals = list({t for t in csv_row_data if t and t[0].startswith('_')})
#     print(f'csv_locals: {csv_locals}')
    if csv_locals == []:
        locals = False
    else:
        locals = True
#     print(f'csv_locals found? {locals}')
    if not any('File Creation Date' in t[0] for t in csv_row_data):
        if any('File Creation Date' in t[0] for t in parent_header_data):
            header_date = next((v for k, v in parent_header_data if k == 'File Creation Date'), '')
            csv_row_data.append(('File Creation Date', header_date))
#         elif creation_date != 'no_update':
#             csv_row_data.append(('File Creation Date', creation_date))
    combined_header_data, combined_locals = merge_headers(csv_row_data, parent_header_data)
#     print(f'combined_header_data: {combined_header_data}')
#     print(f'combined_locals: {combined_locals}')
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
    return combined_header_data

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

combined = build_combined_header(merged_header_data, merged_locals, csv_row_data, creation_date, reviewed, nodefault)
print(f'combined: {combined}')



    