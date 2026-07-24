# webvtt_metadata
Python program that writes metadata to WebVTT files according to the [FADGI Guidelines for Embedding Metadata in WebVTT Files (Version 2.0)](https://www.digitizationguidelines.gov/guidelines/FADGI_WebVTT_embed_guidelines_v0.1_2024-04-18.pdf), using a csv template file, header data from the current file, header data from an associated parent file, and/or a default metadata set. The script does not overwrite the input files; output is written to a new folder that is created inside the input folder.

## Updates
- The script has been updated according to the updated FADGI guidelines, including:
  - repeatable elements are listed as separate element: value pairs, each pair on its own line
  - local element formatting has been updated
  - the FADGI header block begins with "NOTE"
  - any blank lines within the header block are removed
  - the header block is separated from the first cue by a blank line
- The script checks for duplicate nonrepeatable elements and the string "-->" (which is not allowed in WebVTT NOTE blocks) and reports any nonconforming headers in a log file. The log file also lists all files skipped and all files updated.
- The script also works with plain text (.txt) files. This usage is outside the scope of the FADGI guidelines, but can be useful for transcript files. If .txt files are present, the script will apply FADGI metadata in the same way as for WebVTT files, with these exceptions:
  - instead of finding existing header data by searching for the first timecode cue, it searches .txt files for the "Type" element
  - if a header is found, it counts header length as the number of lines from the file start to first blank line after the "Type" element
  - if the existing header has a "Type" value of "caption", the script changes this value to "transcript" if ``--emorydefault`` is selected or to "" if not
  - because "transcript" is not an allowed value for the WebVTT "Type" element, if header data with a "Type" value of "transcript" is applied to a .vtt file, the script will change this value to "caption" if ``--emorydefault`` is selected or to "" if not

## Usage
The only required input is the path to the folder of input files:

```webvtt_metadata.py [path/to/inputfolder]```

Command options:
- ``-c`` or ``--csv`` ``[path/to/webvtt_metadata.csv]``: Include metadata from a CSV
- ``-e`` or ``--emorydefault``: Use Emory default metadata set for empty metadata elements
- ``-r`` or ``--reviewed``: Updates "review history" value to "human-reviewed" for files with an existing FADGI header (it will also create this element if it doesn't exist)
- ``-p`` or ``--parentfiles`` ``[path/to/parentfolder]``: Check directory of parent files for associated header data (requires CSV to match source file with parent file)

For non-local elements, the script uses metadata from the csv first, then from the source file header, then from the parent file header, with one exception: File Creation Date will be carried over from the csv metadata or the source file header, but not from the parent file header. Local elements merge in the same way except metadata for [Reviewer] is retained from each source and any file source is indicated.

## CSV template
The template includes all strongly recommended, recommended, and optional elements:
- Type (strongly recommended)
- Language (strongly recommended)
- Responsible Party (strongly recommended)
- Media Identifier (strongly recommended)
- Originating File (strongly recommended)
- File Creator (strongly recommended)
- File Creation Date (strongly recommended)
- Title (recommended)
- Origin History (recommended) 
- Local Usage Element (optional; can be repeated for additional local elements)

Any elements left blank will not be included in the output header (or will be filled with default metadata if ``-e`` is used).

To include a local usage element, prefix the element name with an underscore (_) in the header row.

## Variations

The csv template is designed so that metadata can be entered separately for each webvtt file. For a version that uses a single set of metadata for all webvtt files in the input folder, use the "_bulk" versions:

``webvtt_metadata_bulk.py [path/to/webvtt_metadata_bulk.csv] [path/to/inputfolder]``

Or if you just need to replace a single element in a WebVTT header, use `webvtt_whoops.py`:

``webvtt_whoops.py [path/to/inputfolder]`` 

(This script will prompt for an optional csv - if replacing with values from a csv, the name of the element should be in the header row.)


##
Feedback, comments, suggestions, etc are welcome!
