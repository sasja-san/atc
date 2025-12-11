#!/bin/bash

FNAME="mwccarm.zip"
URL="http://decomp.aetias.com/files/mwccarm.zip"
ALTERNATE_URL="https://twlsdk.randommeaninglesscharacters.com/download/mwccarm.zip"
EXTRACTION_DIR="tools"

printf "\nFetching %s.\n" $FNAME
printf "\tZip file is 40 MB.\n"
printf "\tUncompressed it's around 85 MB.\n\n" 
wget $URL
unzip $FNAME -d $EXTRACTION_DIR
printf "\nDeleting file %s.\n" $FNAME
rm $FNAME

