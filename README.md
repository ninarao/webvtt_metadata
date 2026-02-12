# webvtt_metadata
Python program that writes metadata to WebVTT files according to the [FADGI Guidelines for Embedding Metadata in WebVTT Files (Version 0.1)](https://www.digitizationguidelines.gov/guidelines/FADGI_WebVTT_embed_guidelines_v0.1_2024-04-18.pdf), using a csv template file, header data from an associated parent file, and/or a default metadata set. The script does not overwrite the input WebVTT files; output is written to a new folder that is created inside the input folder.

## Usage
The only required input is the path to the folder of input WebVTT files:

```webvtt_metadata.py [path/to/inputfolder]```

Command options:
- ``-c`` or ``--csv`` ``[path/to/webvtt_metadata.csv]``: Include metadata from a CSV
- ``-e`` or ``--emorydefault``: Use Emory default metadata set for empty metadata elements
- ``-r`` or ``--reviewed``: Creates/updates FADGI header for human-reviewed input files
- ``-p`` or ``--parentfiles`` ``[path/to/parentfolder]``: Check directory of parent files for associated header data (requires CSV to match input WebVTT file with parent WebVTT file)



## CSV template
The template includes all strongly recommended elements and optional elements:
- Type
- Language
- Responsible Party
- Media Identifier
- Originating File
- File Creator
- File Creation Date
- Optional: Title
- Optional: Origin History
- Optional: Local Usage Element 1 Key (can be repeated for additional local elements)
- Optional: Local Usage Element 1 Value (can be repeated for additional local elements)

Any elements left blank will not be included in the output header (or will be filled with default metadata if ``-e`` is used).

To include additional local usage elements, add column pairs named 'Local Usage Element 2 Key' and 'Local Usage Element 2 Value', and fill the key column with the name of the element and the value column with the value for the element. Repeat as needed, increasing the number in the column names.

The csv template is designed so that metadata can be entered separately for each webvtt file. For a version that uses a single set of metadata for all webvtt files in the input folder, use the "_bulk" versions:

``usage: webvtt_metadata_bulk.py [path/to/webvtt_metadata_bulk.csv] [path/to/inputfolder]``

For the original version of this script, use the "_v1" versions:

``usage: webvtt_metadata_v1.py [path/to/webvtt_metadata_v1.csv] [path/to/inputfolder]``

##
Feedback, comments, suggestions, etc are welcome!
