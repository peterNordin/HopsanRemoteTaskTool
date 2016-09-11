#!/bin/bash
# Example server-side script for zipping the contents of the HOME directory (for retrieval) 
# Author: Peter Nordin

# working directory
wd="./"
# output file
outputfile="mytaskoutput.txt"
# resulting zip file
resultfile="zipHomeFiles.zip"

# Init output file
date > $outputfile
hostname >> $outputfile
echo "Zipping HOME directory script" >> $outputfile
pwd >> $outputfile
ls -l >> $outputfile

# Zip the files, remove old one first
if [ -f mytask/$resultfiles ]; then
  rm mytask/$resultfiles
fi

echo "Zipping" >> $outputfile
zip -r $resultfile $wd >> $outputfile
# Due some hardcoded stuff somewhere, the file must be in the mytask directory
mkdir -p mytask
mv $resultfile mytask
mv $outputfile mytask
ls -l mytask >> mytask/$outputfile

