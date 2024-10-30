# webvtt_metadata
Python program that writes metadata to WebVTT files according to the FADGI Guidelines for Embedding Metadata in WebVTT Files (Version 0.1), using a csv template file. The script does not overwrite the input WebVTT files; output is written to a new folder that is created inside the input folder.

The template includes all strongly recommended elements as well as options to include optional elements:
- Type
- Language
- Responsible Party
- Media Identifier
- Originating File
- File Creator
- File Creation Date
- Optional: Title
- Optional: Origin History
- Optional: Local Usage Element (element can be named/renamed as needed)
- Optional: Local Usage Element (element can be named/renamed as needed)

``usage: webvtt_metadata.py [path/to/webvtt_metadata.csv] [path/to/inputfolder]``

The csv template webvtt_metadata.csv is designed so that metadata can be entered separately for each webvtt file.  

For a version that uses a single set of metadata for all webvtt files in the input folder, use the "_bulk" versions:

``usage: webvtt_metadata_bulk.py [path/to/webvtt_metadata_bulk.csv] [path/to/inputfolder]``

Feedback, comments, suggestions, etc are welcome!
