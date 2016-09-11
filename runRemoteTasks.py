#!/usr/bin/env python
__author__ = 'Peter Nordin'
__license__ = "GPLv3"
__email__ = "peter.nordin@liu.se"

import shutil as sh
import sys
import os
import subprocess
import time
import argparse

# Input and output files
gInputTaskList = 'taskList'
gInputServerlist = 'serverlist'
gOutputDoneTaskList = 'doneTasks'
gOutputFailedTaskList = 'failedTasks'

# Program locations psoix=linux
if os.name == 'posix':
    gSevenZip = r'7z'
    gHopsanclient = r'/opt/hopsan/bin/HopsanServerClient'
# Program locations for Windows
elif os.name == 'nt':
    gSevenZip = r'C:\Program Files\7-Zip\7z.exe'
    gHopsanclient = r'C:\Program Files\Hopsan\bin\HopsanServerClient.exe'
    #gHopsanclient = r'C:\svn\hopsan\trunk\bin\HopsanServerClient.exe'

# Remote files and identification
gUserID = 'anonymous'
gServerSideScript = 'serverSideRunTask.sh'
gServerSideWD = 'mytask'
gTaskZipFile = 'mytask.zip'
gOutputFile = 'mytaskoutput.txt'
# gResultFiles = ['hopsancli_debug.txt']
gResultFiles = []

# Other settings
gRunOnAll = False
gSleepTime = 5
gNumSlots = 2
gTest = False


def mkdirs(path):
    try:
        os.makedirs(path)
    except OSError as exception:
        if exception.errno != os.errno.EEXIST:
            raise


def remove(path):
    try:
        os.remove(path)
    except OSError as exception:
        if exception.errno != os.errno.ENOENT:
            raise


def move(src, dst):
    if src != dst:
        sh.move(src, dst)
    else:
        print('In move: Same src and dst')


def appendToFile(filepath, text):
    with open(filepath, 'a+') as f:
        f.write(text+'\n')

class ServerHandler:
    def __init__(self):
        self.servers = list()
        self.takenservers = list()

    def readservers(self, serverlistfile):
        try:
            with open(serverlistfile, 'r+') as f:
                for line in f:
                    self.servers.append(line.strip())
            print(self.servers)
        except IOError as e:
            print "I/O error({0}): {1}, {2}".format(e.errno, e.strerror, serverlistfile)

    def numservers(self):
        return len(self.servers)+len(self.takenservers)

    def numfreeservers(self):
        return len(self.servers)

    def takeserver(self):
        if self.numfreeservers() > 0:
            srv = self.servers.pop(0)
            self.takenservers.append(srv)
            return srv
        else:
            return None

    def returnserver(self, server):
        self.servers.append(server)
        self.takenservers.remove(server)


class Experiment:
    def __init__(self, server, process, expdir):
        self.server = server
        self.process = process
        self.experimentdirectory = expdir
        self.outputdir = expdir
        self.taskcompletedok = False
        self.retrievalcompletdok = False

    def isrunning(self):
        if self.process is not None:
            return self.process.poll() is None
        else:
            return False

    def communicate(self):
        if self.process is not None:
            return self.process.communicate()
        else:
            return '', ''

    def rc(self):
        if self.process is not None:
            #print('rc: '+str(self.process.returncode))
            return self.process.returncode
        else:
            return 1


def compressDirectory(srcdir, dst):
    print('Compressing: '+srcdir+' to dst: '+dst)
    fname = os.path.basename(dst)
    print([gSevenZip, 'a', '-tzip', fname, '-r', '*'])
    if gTest:
        return True
    else:
        remove(dst)
        p = subprocess.Popen([gSevenZip, 'a', '-tzip', fname, '-r', '*'], cwd=srcdir)
        p.wait()
        move(os.path.join(srcdir, fname), dst)
        return os.path.exists(dst)


def executeRemoteTask(lwd, address, userid, taskzipfile, serversidescript):
    print('Running task at: '+address+' Using local WD: '+lwd)
    print([gHopsanclient, '-s', address, '-u ' + userid, '-a ' + taskzipfile, '-a ' + serversidescript, '--numslots', str(gNumSlots), '--shellexec', '/bin/bash ' + os.path.basename(serversidescript)])
    if gTest:
        p = subprocess.Popen(['ping', '127.0.0.1', '-c', '4'], stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    else:
        p = subprocess.Popen([gHopsanclient, '-s', address, '-u ' + userid, '-a ' + taskzipfile, '-a ' + serversidescript,
                              '--numslots', str(gNumSlots), '--shellexec', '/bin/bash ' + os.path.basename(serversidescript)],
                             cwd=lwd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    return p


def retriveRemoteTaskResults(lwd, address, userid, outputfile, resultfiles, sequential=False):
    print('Retrieving from: '+address+' Using local WD: ' + lwd)
    mkdirs(lwd)
    cmdlist = [gHopsanclient, '-s', address, '-u ' + userid, '--request ' + outputfile.replace('\\', '/')]
    for r in resultfiles:
        cmdlist.append('--request ' + r.replace('\\', '/'))
    print(cmdlist)
    if gTest:
        p = subprocess.Popen(['ping', '127.0.0.1', '-c', '1'], stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    else:
        p = subprocess.Popen(cmdlist, cwd=lwd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    if sequential:
        p.wait()
        if not gTest:
            for r in resultfiles:
                src = os.path.join(lwd, r)
                if not os.path.exists(src):
                    print('Error: ' + src + ' does not exist!')
            src = os.path.join(lwd, outputfile)
            if not os.path.exists(src):
                print('Error: ' + src + ' does not exist!')
    return p


if __name__ == "__main__":

    argparser = argparse.ArgumentParser()
    argparser.add_argument('--user', help='User name to use')
    argparser.add_argument('--hopsandir', help='Path to the Hopsan bin directory to use')
    argparser.add_argument('--serverlist', help='Text file with server ip:port line by line')
    argparser.add_argument('--ssscript', help='Server side script to execute')
    argparser.add_argument('--tasklist', help='A list of tasks (directories) to process')
    argparser.add_argument('--runonall', help='Run the task on every server', action='store_true')
    argparser.add_argument('--outdir', help='The destination for received file (will be created if missing)')
    argparser.add_argument('--resultfiles', nargs='*', action='append')
    argparser.add_argument('--numslots', type=int, help='The number of required slots, n>0')

    args = argparser.parse_args()

    if args.runonall:
        gRunOnAll = True
    if args.user:
        gUserID = args.user
    if args.hopsandir:
        gHopsanclient = os.path.realpath(os.path.join(args.hopsandir, 'HopsanServerClient'))
    if args.serverlist:
        gInputServerlist = os.path.realpath(args.serverlist)
    if args.tasklist:
        gInputTaskList = os.path.realpath(args.tasklist)
    if args.ssscript:
        gServerSideScript = os.path.realpath(args.ssscript)
    outdir = os.path.join(os.path.expanduser('~'), 'Temp/RemoteOut')
    if args.outdir:
        outdir = os.path.realpath(args.outdir)
    mkdirs(outdir)
    if args.numslots:
        gNumSlots = max(1, args.numslots)

    print('User: '+gUserID)
    print('HopsanClient: '+gHopsanclient)
    print('ServerSideScript: '+gServerSideScript)
    print('Using output directory: '+outdir)
    print('Run task on every server: '+str(gRunOnAll))
    if args.resultfiles:
        gResultFiles = [rf for rfl in args.resultfiles for rf in rfl]
        print 'Result files: ',
        print(gResultFiles)
    print('Requesting num slots: '+str(gNumSlots))

    SH = ServerHandler()
    SH.readservers(gInputServerlist)
    print('Num servers: '+str(SH.numservers()))

    if SH.numservers() < 1:
        print('Error: No servers')
        sys.exit(-1)

    experiment_list = list()
    try:
        with open(gInputTaskList, 'r+') as f:
            for line in f:
                line = line.strip()
                if line != '':
                    experiment_list.append(line)
    except IOError as e:
        print "I/O error({0}): {1}, {2}".format(e.errno, e.strerror, gInputTaskList)


    running_experiments = list()
    running_retreivals = list()
    done_experiments = list()
    failed_experiments = list()
    zipped_tasks = list()
    num_experiments = len(experiment_list)
    # Duplicate tasks for every server, if they should be run on all
    if gRunOnAll:
        newlist = list()
        for exp in list(experiment_list):
            for i in range(SH.numfreeservers()):
                newlist.append(exp)
        experiment_list = newlist
        num_experiments = len(experiment_list)
    # Clear output files
    if num_experiments > 0:
        remove(gOutputDoneTaskList)
        remove(gOutputFailedTaskList)
    # Run until all experiments have been processed
    while len(done_experiments)+len(failed_experiments) < num_experiments:
        havefreeservers = SH.numfreeservers() > 0
        if len(experiment_list) > 0 and havefreeservers:
            # If every task should run on every server, then start it once for every server
            if gRunOnAll:
                while SH.numfreeservers() > 0 and len(experiment_list) > 0:
                    expdir = os.path.realpath(experiment_list.pop(0))
                    print('Processing experiment: ' + expdir)
                    zipfile = os.path.join(expdir, gTaskZipFile)
                    if zipfile not in zipped_tasks:
                        remove(zipfile)  # Remove previous version to avoid including it in new zip
                        if compressDirectory(expdir, zipfile):
                            zipped_tasks.append(zipfile)
                        else:	
                            print('Error: Failed to compress: ' + expdir)
                            failed_experiments.append(expdir)
                        print('\n')

                    if zipfile in zipped_tasks:
                        srv = SH.takeserver()
                        p = executeRemoteTask(os.getcwd(), srv, gUserID, zipfile, gServerSideScript)
                        exp = Experiment(srv, p, expdir+'_'+srv.replace(':', '_'))
                        running_experiments.append(exp)
                        havefreeservers = True

            # Else start a new experiment on ONE server, if we have free servers
            else:
                expdir = os.path.realpath(experiment_list.pop(0))
                print('Processing experiment: ' + expdir)
                zipfile = os.path.join(expdir, gTaskZipFile)
                if zipfile not in zipped_tasks:
                    remove(zipfile)  # Remove previous version to avoid including it in new zip
                    if compressDirectory(expdir, zipfile):
                        zipped_tasks.append(zipfile)
                    else:	
                        print('Error: Failed to compress: ' + expdir)
                        failed_experiments.append(expdir)
                    print('\n')

                if zipfile in zipped_tasks:
                    srv = SH.takeserver()
                    p = executeRemoteTask(os.getcwd(), srv, gUserID, zipfile, gServerSideScript)
                    exp = Experiment(srv, p, expdir)
                    running_experiments.append(exp)

            print('Free servers ' + str(SH.numfreeservers()) + ' out of ' + str(SH.numservers()))

        # Check running and handle completed experiments
        for rexp in list(running_experiments):
            if not rexp.isrunning():
                rexp.outputdir = os.path.join(outdir, os.path.basename(rexp.experimentdirectory))
                mkdirs(rexp.outputdir)
                clientSideLog = os.path.join(rexp.outputdir, 'clientSideTaskLog.txt')
                remove(clientSideLog)  # Remove old log file if it exists
                stdout, stderr = rexp.communicate()
                appendToFile(clientSideLog, stdout)
                rexp.taskcompletedok = (rexp.rc() == 0)

                # OK we are done, lets start a fetch results process
                outputfile = os.path.join(gServerSideWD, gOutputFile)
                resultfiles = [os.path.join(gServerSideWD, rf) for rf in gResultFiles]
                p = retriveRemoteTaskResults(rexp.outputdir, rexp.server, gUserID, outputfile, resultfiles, True)
                rexp.process = p
                running_retreivals.append(rexp)
                running_experiments.remove(rexp)

        #  Check retrievals and return the server as a free servers for further processing
        for rret in list(running_retreivals):
            if not rret.isrunning():
                clientSideLog = os.path.join(rret.outputdir, 'clientSideRetrieveLog.txt')
                remove(clientSideLog)  # Remove old log file if it exists
                stdout, stderr = rret.communicate()
                appendToFile(clientSideLog, stdout)
                running_retreivals.remove(rret)
                rret.retrievalcompletedok = (rret.rc() == 0)

                # We are done, lets check if both task and retrieval were ok
                if rret.taskcompletedok and rret.retrievalcompletedok:
                    appendToFile(gOutputDoneTaskList, rret.experimentdirectory)
                    done_experiments.append(rret)
                else:
                    appendToFile(gOutputFailedTaskList, rret.experimentdirectory)
                    failed_experiments.append(rret.experimentdirectory)

                SH.returnserver(rret.server)

        # Handle case when we have no free servers
        if not havefreeservers:
            print('All servers are busy, Still running')
            # Wait a while until we try again
            time.sleep(gSleepTime)
        # Handle case when all experiments are running
        elif len(experiment_list) == 0 and len(running_experiments) != 0:
            print('Experiments are still running')
            time.sleep(gSleepTime)
        # Handle case when we are only waiting for transfers to complete
        elif len(experiment_list) == 0 and len(running_retreivals) != 0:
            # Sleep for a short time her, but do not spam with messages
            time.sleep(1)

        print('\n')
        print('NumExperiments:' + str(num_experiments) + '  Done:' + str(len(done_experiments)) + '  RunningTasks:' +
              str(len(running_experiments)) + '  RunningRetreivals:' + str(len(running_retreivals)) + '  Failed:' +
              str(len(failed_experiments)))
        print('Free servers ' + str(SH.numfreeservers()) + ' out of ' + str(SH.numservers()))
        print('\n')
        time.sleep(1)

    # OK we are done, lets check that every server has been returned
    print('Done: Free servers '+str(SH.numfreeservers())+' out of '+str(SH.numservers()))
    if len(failed_experiments) > 0:
        print('The following tasks failed:')
        for fe in failed_experiments:
            print(fe+' TaskOK: '+str(fe.taskcompletedok)+'    RetrieveOK: '+str(fe.retrievalcompletdok))
