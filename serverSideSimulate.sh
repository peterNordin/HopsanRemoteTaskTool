#!/bin/bash
# Example script to start a simulation on the server side
# Author: Peter Nordin

# working directory
wd="mytask"
# zip file with task related files
taskfile="mytask.zip"
# model name
hmffile="mymodel.hmf"
# opt script
optfile="myoptinstruct.txt"
# output file
outputfile="mytaskoutput.txt"
resultsfile="hopsancli_debug.txt"

# Init output file
date > $outputfile
hostname >> $outputfile
# First clear old data
if [ -d $wd ]; then
  rm -rf $wd
fi
# Create work dir
mkdir -p $wd
# Move files to work dir
pwd >> $outputfile
ls -l >> $outputfile
mv $outputfile $wd
mv $taskfile $wd || { exit 1; }
# Enter work dir
cd $wd
# Unpack task related files
unzip -o $taskfile
pwd >> $outputfile
ls -l >> $outputfile

# Prepare for task execution

# Start the task, call HopsanCLI
sleep 1
echo "HopsanCLI -m $hmffile -o $optfile" >> $outputfile
HopsanCLI -m $hmffile -s hmf -e  MachineModelLib/libMachineModelLib.so 2>&1 >> $outputfile

# Post process (zip result files if needed)
