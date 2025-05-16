#!/usr/bin/env python3

import csv
import os
import glob
import sys
from pathlib import Path

# sys.argv = ['webvtt_metadata_bulk.py', 'path to csv', 'path to input folder']

# check that command has metadata file location
# and caption folder location
if len(sys.argv) != 3:
    print("Usage: python webvtt_metadata_bulk.py [metadata file] [input folder]")
    sys.exit(1)

if not os.path.isfile(sys.argv[1]):
    print("Error: %s is not a valid file." % sys.argv[1])
    print("Usage: python webvtt_metadata_bulk.py [metadata file] [input folder]")
    sys.exit(1)
        
if not os.path.isdir(sys.argv[2]):
    print("Error: %s is not a valid directory." % sys.argv[2])
    print("Usage: python webvtt_metadata_bulk.py [metadata file] [input folder]")
    sys.exit(1)
        
arg1 = sys.argv[1]
arg2 = sys.argv[2]

print('metadata file:',arg1)
print('vtt directory:',arg2)


def write_caption():
    with open(filename, 'r', encoding="utf8") as captionFile:
        next(captionFile)
        caption = captionFile.read()
        print("Reading from: " + filename)
    with open (outputFile, 'w', encoding="utf8") as writeFile:
        print("Writing to: " + outputName)
        writeFile.write(f"{line1}\n")
        writeFile.write(f"{line2}\n")
        writeFile.write(f"{line3}\n")
        writeFile.write(f"{line4}\n")
        writeFile.write(f"{line5}\n")
        writeFile.write(f"{line6}\n")
        writeFile.write(f"{line7}\n")
        writeFile.write(f"{line8}\n")
        if mData[8][1] != "":
            writeFile.write(f"{line9}\n")
        if mData[9][1] != "":
            writeFile.write(f"{line10}\n")
        if line11 != "":
            writeFile.write(f"{line11}\n")
        writeFile.write(caption)
        writeFile.close()
        print("File done")


# check for output folder and create if needed
directory = arg2
outputDir = os.path.join(directory, "output")

print("Checking for output folder...")

if not os.path.exists(outputDir):
    print(outputDir)
    os.mkdir(outputDir)
    print("Output folder %s created" % outputDir)
else:
    print("Output folder %s already exists" % outputDir)


# make output file in output folder
for filename in glob.glob(directory + '/*.vtt'):
    justName = Path(filename).stem
    outputName = justName + "_new.vtt"
    origFile = os.path.basename(filename)
    
    outputFile = os.path.join(outputDir, outputName)


# read metadata from csv
    with open(arg1, 'r') as metadataFile:
        metadataReader = csv.reader(metadataFile)
        mData = list(metadataReader)
                
    line1 = ("WEBVTT")
    line2 = ("Type: " + mData[1][1])
    line3 = ("Language: " + mData[2][1])
    line4 = ("Responsible Party: " + mData[3][1] + ", " + mData[3][2])
    line5 = ("Media Identifier: " + justName + ", " + mData[4][2])
    line6 = ("Originating File: " + justName + ".mp4")
    line7 = ("File Creator: " + mData[6][1])
    line8 = ("File Creation Date: " + mData[7][1])
    line9 = ("Title: " + mData[8][1])
    line10 = ("Origin History: " + mData[9][1])
    if mData[11][1] != "" and mData[12][1] != "":
        line11 = ("Local Usage Element: " + mData[11][0] + " " + mData[11][1] + "; " + mData[12][0] + " " + mData[12][1])
    elif mData[11][1] != "" and mData[12][1] == "":
        line11 = ("Local Usage Element: " + mData[11][0] + " " + mData[11][1])
    elif mData[11][1] == "" and mData[12][1] != "":
        line11 = ("Local Usage Element: " + mData[12][0] + " " + mData[12][1])
    else:
        line11 = ""
                  

# write metadata and captions to output files
    if not os.path.exists(outputFile):
        write_caption()
    else:
        while True:
            print("Output file %s already exists, do you want to overwrite? (y/n)" % outputName)
            userDecide = input()
            if userDecide == "n":
                print("Skipping file")
                break
            elif userDecide == "y":
                print("Overwriting file %s" % outputName)
                write_caption()
                break
