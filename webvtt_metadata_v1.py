#!/usr/bin/env python3

import csv
import os
import glob
import sys
from pathlib import Path

# sys.argv = ['webvtt_metadata.py', 'path to csv', 'path to input folder']

# check that command has metadata file location
# and caption folder location
if len(sys.argv) != 3:
    print("Usage: python webvtt_metadata.py [metadata file] [input folder]")
    sys.exit(1)

if not os.path.isfile(sys.argv[1]):
    print("Error: %s is not a valid file." % sys.argv[1])
    print("Usage: python webvtt_metadata.py [metadata file] [input folder]")
    sys.exit(1)
        
if not os.path.isdir(sys.argv[2]):
    print("Error: %s is not a valid directory." % sys.argv[2])
    print("Usage: python webvtt_metadata.py [metadata file] [input folder]")
    sys.exit(1)
        
arg1 = sys.argv[1]
arg2 = sys.argv[2]

print('metadata file:',arg1)
print('vtt directory:',arg2)


def write_caption():
    with open(filename, 'r') as captionFile:
        next(captionFile)
        caption = captionFile.read()
        print("Reading from: " + filename)
    with open (outputFile, 'w') as writeFile:
        print("Writing to: " + outputName)
        writeFile.write(f"{line1}\n")
        writeFile.write(f"{line2}\n")
        writeFile.write(f"{line3}\n")
        writeFile.write(f"{line4}\n")
        writeFile.write(f"{line5}\n")
        writeFile.write(f"{line6}\n")
        writeFile.write(f"{line7}\n")
        writeFile.write(f"{line8}\n")
        if row[9] != "":
            writeFile.write(f"{line9}\n")
        if row[10] != "":
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


# define output file in output folder
for filename in glob.glob(directory + '/*.vtt'):
    justName = Path(filename).stem
    outputName = justName + ".vtt"
    sourceFile = os.path.basename(filename)
    outputFile = os.path.join(outputDir, outputName)
    
# read metadata from csv
    with open(arg1, 'r') as metadataFile:
        metadataReader = csv.reader(metadataFile)
        for row in metadataReader:
            if row[0] == sourceFile:
                print(f"Match found for {sourceFile}")
                line1 = ("WEBVTT")
                line2 = ("Type: " + row[1])
                line3 = ("Language: " + row[2])
                line4 = ("Responsible Party: " + row[3])
                if row[5] == "":
                    line5 = ("Media Identifier: " + row[4])
                elif row[5] != "":
                    line5 = ("Media Identifier: " + row[4] + ", " + row[5])
                line6 = ("Originating File: " + row[6])
                line7 = ("File Creator: " + row[7])
                line8 = ("File Creation Date: " + row[8])
                line9 = ("Title: " + row[9])
                line10 = ("Origin History: " + row[10])
                if row[12] != "" and row[14] != "":
                    line11 = ("Local Usage Element: " + row[11] + " " + row[12] + "; " + row[13] + " " + row[14])
                elif row[12] != "" and row[14] == "":
                    line11 = ("Local Usage Element: " + row[11] + " " + row[12])
                elif row[12] == "" and row[14] != "":
                    line11 = ("Local Usage Element: " + row[13] + " " + row[14])
                elif row[12] == "" and row[14] == "":
                    line11 = ""

    # write metadata and captions to output files
                if not os.path.exists(outputFile):
                    write_caption()
                else:
#                     while True:
                    print("Output file %s already exists, do you want to overwrite? (y/n)" % outputName)
                    userDecide = input()
                    if userDecide == "n":
                        print("Skipping file")
                        break
                    elif userDecide == "y":
                        print("Overwriting file %s" % outputName)
                        write_caption()
                        break
