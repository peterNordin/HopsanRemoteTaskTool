#!/bin/bash
# Example server-side script for building a Hopsan component library on the server side
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

homedir=`pwd`
outputfile="$homedir/$outputfile"
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
mv $taskfile $wd || { exit 1; }
# Enter work dir
cd $wd
# Unpack task related files
unzip -o $taskfile
pwd >> $outputfile
ls -l >> $outputfile

# Prepare for task execution
libname="$(grep hopsancomponentlibrary *.xml -l)"
libname=${libname%.*}
cd $homedir
if [ -d $libname ]; then
  rm -rf $libname
fi
mv $wd $libname
pwd >> $outputfile
ls -l >> $outputfile


# Enter libdir and remember path
libdir="$homedir/$libname"
echo "libname $libname" >> $outputfile
echo "libdir $libdir" >> $outputfile


# --------------------------------------
# Do any library specific internal build work
# --------------------------------------
# TODO call some bundeled script instead
cd $libdir
#cd libDFC
#make -B MAKETARGET
# --------------------------------------

# --------------------------------------
# Call build utility in HopsanCLI
# --------------------------------------
cd $homedir
HopsanCLI --buildComponentLibrary $libdir/$libname.xml 2>&1 >> $outputfile
# --------------------------------------

# --------------------------------------
# Post process
# --------------------------------------
# Need to move the output file to the wd since task runner expect it there
mkdir -p $wd
mv $outputfile $wd
