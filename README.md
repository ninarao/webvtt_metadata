# webvtt_metadata
Python program that writes metadata to WebVTT files according to the [FADGI Guidelines for Embedding Metadata in WebVTT Files (Version 2.0)], using a csv template file, existing FADGI comment block data from the current file, comment block data from an associated parent file, and/or a default metadata set. The script does not overwrite the input files; output is written to a new folder that is created inside the input folder.

### Updates
- The script has been updated to align with the updated FADGI guidelines, including:
  - repeatable elements are listed as separate "element: value" pairs, each pair on its own line
  - local element formatting has been updated
  - the FADGI metadata comment block begins with "NOTE" followed by a new line
  - any blank lines within the header block are removed
  - the metadata comment block is separated from the first cue by a blank line
- The script now produces a log file which lists files skipped, files checked, and files with nonconforming metadata comment blocks (blocks with duplicate nonrepeatable elements or the substring "-->" which is not allowed in WebVTT comment blocks)
- The script also works with plain text (.txt) files. This usage is outside the scope of the FADGI guidelines, but can be useful for transcript files. If .txt files are present, the script will apply FADGI metadata in the same way as for WebVTT files, with these exceptions:
  - instead of finding existing comment block data by searching for the first timecode cue, it searches .txt files for the "Type" element
  - if a comment block is found, it counts the block length as the number of lines from the file start to first blank line after the "Type" element
  - any "Type" value in the source file comment block will be applied to .txt files as is, but if getting the "Type" value from a parent file comment block, the script will apply this value as "transcript" if ``--emorydefault`` is selected or to "" if not
  - because "transcript" is not an allowed value for the WebVTT "Type" element, if comment block data with a "Type" value of "transcript" is applied to a .vtt file, the script will change this value to "caption" if ``--emorydefault`` is selected or to "" if not

### Usage
The only required input is the path to the folder of input files:

```webvtt_metadata.py [path/to/inputfolder]```

Command options:
- ``-c`` or ``--csv`` ``[path/to/webvtt_metadata.csv]``: Include metadata from a CSV
- ``-e`` or ``--emorydefault``: Use Emory default metadata set for empty metadata elements
- ``-r`` or ``--reviewed``: Updates "review history" value to "human-reviewed" for files with an existing FADGI comment block (it will also create this element if it doesn't exist)
- ``-p`` or ``--parentfiles`` ``[path/to/parentfolder]``: Check directory of parent files for associated comment block data (requires CSV to match source file with parent file)
- ``-o`` or ``--overwrite``: if new values are given for repeatable elements, overwrite the existing values

For nonrepeatable elements, the script uses metadata from the csv first, then from the source file comment block, then from the parent file comment block (with one exception: File Creation Date will be carried over from the csv metadata or the source file comment block, but not from the parent file comment block). For repeatable elements, if values exist in multiple sources, the script by default will preserve existing values and append any new ones. To overwrite values instead of appending, use option ``-o``. Local elements are handled the same as nonrepeatable except that values for ``_Reviewer`` are retained from each source and any file source is indicated.

### CSV template
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

Any elements left blank will not be included in the output comment block (or will be filled with default metadata if ``-e`` is used).

To include a local usage element, prefix the element name with an underscore ``_`` in the header row.

### Variations
#### webvtt_metadata_bulk.py
- applies a single set of metadata to all .vtt and .txt files in the source folder
- checks input for nonconforming elements ("-->" or duplicate nonrepeatable elements) and warns if present
- creates a log of files skipped, files updated, and files with nonconforming metadata comment blocks
- usage: ``webvtt_metadata_bulk.py -c [path/to/webvtt_metadata.csv] [path/to/sourcefolder]``
  - use csv row 1 for element names and row 3 for values
  - ``-o`` or ``--overwrite``: if new values are given for repeatable elements, overwrite the existing values
  - ``-t`` or ``--txt-type``: set a different "Type" value for .txt files (if used without specifying a value, will set Type as blank for .txt files)
#### webvtt_whoops.py
- for replacing or appending a single element-value pair in a metadata comment block (or creating this element for files that don't have existing comment blocks)
- works with nonlocal and local elements
- creates a log of files skipped and files updated
- new values can be added globally for all files or for individual files using an optional csv
- if using a csv, the script will skip any files not listed in the csv
- "NOTE" mode checks .vtt files for NOTE string at start of comment block and adds this if missing (this mode skips .txt files and files without comment blocks)
- usage: ``webvtt_whoops.py [path/to/inputfolder]`` 
  - ``-t`` or ``--txtheader``: applies actions to .txt files as well as .vtt files

##
Feedback, comments, suggestions, etc are welcome!
