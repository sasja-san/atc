#!/bin/bash

FNAME="mwccarm.zip"
URL="http://decomp.aetias.com/files/mwccarm.zip"
EXTRACTION_DIR="tools"

printf "\nFetching %s. Zip file is 40 MB, uncompressed it's around 85 MB.\n" $FNAME
wget $URL
unzip $FNAME -d $EXTRACTION_DIR
printf "\nDeleting file %s.\n" $FNAME
rm $FNAME

