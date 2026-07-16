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
m_csv = '/Users/nraogra/Desktop/webvtt_v2/webvtt_metadata_parent.csv'
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

def build_combined_header(parent_header_data, header_locals, csv_row_data, creation_date, reviewed, nodefault, keys):
    base_dict = dict.fromkeys(keys, "")
#     base_tupes = [(x, '') for x in keys]
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
        merged_locals = merge_locals(local_string, header_locals)
        csv_filtered["Local Usage Element"] = "Local Usage Element: " + merged_locals
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

creation_date = ''
reviewed = False
nodefault = True
keys = ''

build_combined_header(merged_header_data, merged_locals, csv_row_data, creation_date, reviewed, nodefault, keys)
    
    