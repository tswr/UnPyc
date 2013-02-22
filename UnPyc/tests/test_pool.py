#!/usr/bin/python

# [The "BSD licence"]
# Copyright (c) 2008-2009 Dmitri Kornev
# Copyright (c) 2011 Alexander Ogorodnikov
# All rights reserved.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are met:
#     * Redistributions of source code must retain the above copyright
#       notice, this list of conditions and the following disclaimer.
#     * Redistributions in binary form must reproduce the above copyright
#       notice, this list of conditions and the following disclaimer in the
#       documentation and/or other materials provided with the distribution.
#     * The name of the author may not be used to endorse or promote products
#       derived from this software without specific prior written permission.
#
# THIS SOFTWARE IS PROVIDED BY THE AUTHOR ''AS IS'' AND ANY
# EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
# DISCLAIMED. IN NO EVENT SHALL Dmitri Kornev BE LIABLE FOR ANY
# DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES
# (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES;
# LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND
# ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
# (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS
# SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
#
# -----
#
# Changelog:
# 2011. Alexander Ogorodnikov: Code was almost totally rewritten, added keys for run, 
#                                                      changed the format of checking tests: two compiled files compars now (source -> compiled and decompiled -> compiled),
#                                                      added multiprocessing.

'''
 >> Testing system for project UnPyc <<
 --== Help ==--
 Usage: test.py  <dirname>|<filename> [<dirname>|<filename>]*
                [-v] <version>
                [-p] <proc_count>
                [-D]
                
 Arguments:
  <dirname>|<filename>  recursive testing begins with this folders, 
                        testing this files
 
 Options:
    -v, --version       set version for compilation
                        <version> format: x.x (example: 2.6)
    -p, --processes     set count of processes for testing
    -D, --nodelete      don't delete .pyc, .py files after testing
                        (by default deletes, if the test is ok)
'''

__usage = '''
        test.py  <dirname>|<filename> [<dirname>|<filename>]*
                [-v] <version>
                [-p] <proc_count>
                [-D]
                [-h]

 Arguments:
  <dirname>|<filename>  recursive testing begins with this folders, 
                        testing this files'''

import os
import sys
import py_compile
import subprocess

import multiprocessing

import optparse

import time

def run():
# key_parse
    def help(option, opt_str, value, parser, *args, **kwargs):
        print '--== Help ==--'
        parser.print_help()
        print 
        sys.exit(0)
    
    parser = optparse.OptionParser(usage=__usage, add_help_option=False)
    parser.add_option('-v', '--version', type='string', dest='version', default=False, \
            help='set version for compilation; ' \
                 '<version> format: x.x (example: 2.6)')
    parser.add_option('-p', '--processes', type='int', dest='processes', default=False, \
            help='set count of processes for testing')
    parser.add_option('-D', '--nodelete', action='store_true', dest='nodelete', default=False, \
            help='don\'t delete .pyc, .py files after testing; ' \
                 '(by default deletes, if the test is ok)')
    parser.add_option('-h', '--help', action='callback', callback=help,
            help='show this help message')

    (options, args) = parser.parse_args()
    if len(args) == 0:
        parser.error('arguments are necessary!')
    python_cmd = "python"
    if not options.version:
        try:
            options.version = '%i.%i' % sys.version_info[:2]
        except AttributeError:
            options.version = sys.ver[:3]
    else:
        #Check python version
        (my_stdout, my_stderr) = subprocess.Popen([python_cmd+options.version,'-h'], shell = True, stdout=subprocess.PIPE, stderr=subprocess.PIPE).communicate()
        if my_stderr != "":
            parser.error('there\'s no such python version '+options.version+'!')
        else:
            python_cmd += options.version
    if options.processes is False:
        options.processes = multiprocessing.cpu_count()
    elif options.processes < 1:
        parser.error('incorrect number of processes: '+str(options.processes)+'!')
        
# end key_parse
    totest = []
    lockPrint = multiprocessing.Manager().Lock()    # lock for print
    lockUnPyc = multiprocessing.Manager().Lock()    # lock for file UnPyc
    
    for entry in args:
        if os.path.isfile(entry):
            totest.append((lockPrint,lockUnPyc, entry, options.version, python_cmd))
        elif os.path.isdir(entry):
            for file in expandDir(entry):
                totest.append((lockPrint,lockUnPyc, file, options.version, python_cmd))
        else:
            print >> sys.stderr, ">>> no such file or directory %s" % entry

    for (lp,lu,file,version,pc) in totest:
        cfile_dir = os.path.dirname(os.path.join("bytecode_" + version, file) + "c")
        if not os.path.exists(cfile_dir):
            os.makedirs(cfile_dir)
        elif not os.path.isdir(cfile_dir):
            totest.remove((file,version,pc))
            print 'Cannot create dir "' + cfile_dir + '"!'
    
    if not totest:
        sys.exit(0)
    start = time.time() # time
    pool = multiprocessing.Pool(processes=options.processes)
    results = pool.map(dotest, totest)
    pool.close()
    pool.join()
    finish = time.time() # time

    ok = []
    failed = []
    bad_test = []
    for (r_ok, r_failed, r_bad) in results:
        if r_ok is not None:
            ok.append(r_ok)
        elif r_failed is not None:
            failed.append(r_failed)
        else:
            bad_test.append(r_bad)
    
    print "___ Statistics ___"
    print "OK(%d)" % (len(ok))
    print "FAILED(%d):\n    %s" % (len(failed), "\n    ".join(failed))
    print "BAD_TEST(%d):\n    %s" % (len(bad_test), "\n    ".join(bad_test))
    print "time of testing on "+str(options.processes)+" processes: "+str(finish - start)+" secs"

    if not options.nodelete:
        for file in ok:
            cfile = os.path.join("bytecode_" + version, file) + "c"
            try:
                os.unlink(cfile)
            except Exception as e:
                print 'Cannot delete the file: ' + cfile
                print str(e)
            try:
                os.unlink(cfile+".py")
            except Exception as e:
                print 'Cannot delete the file: ' + cfile + ".py"
                print str(e)
            try:
                os.unlink(cfile+".pyc")
            except Exception as e:
                print 'Cannot delete the file: ' + cfile + ".pyc"
                print str(e)




def cmpPyc(lockUnPyc, pycfile_original, pycfile_secondary):
    # my_stderr = 'python: can\'t open file'
    # while my_stderr.count('python: can\'t open file'):
    lockUnPyc.acquire()
    (my_stdout, my_stderr) = subprocess.Popen(["UnPyc", "--diff=0", pycfile_original, pycfile_secondary], \
                    shell = True, stdout=subprocess.PIPE, stderr=subprocess.PIPE).communicate()
    lockUnPyc.release()
    if my_stdout.count('# Identical with specified precision'):
        return True
    else:
        fh_err = open(pycfile_secondary + "_err", 'w')
        fh_err.write(my_stdout)
        fh_err.close()
        return False
    
def test(lockUnPyc, pycfile_original, python_cmd):
    if os.path.isfile(pycfile_original):
        file_secondary = pycfile_original + ".py"
        # my_stderr = 'python: can\'t open file'
        # while my_stderr.count('python: can\'t open file'):
        lockUnPyc.acquire()
        (my_stdout, my_stderr) = subprocess.Popen(["UnPyc", "-D", pycfile_original,">",file_secondary], \
                        shell = True, stderr=subprocess.PIPE).communicate()
        lockUnPyc.release()
        if my_stderr != "":
            fh_err = open(file_secondary + "_err", 'w')
            fh_err.write(my_stderr)
            fh_err.close()
            return False
        (my_stdout, my_stderr) = subprocess.Popen([python_cmd, "-c", "import py_compile;py_compile.compile(r'"+file_secondary+"',doraise=True)"], \
                    shell = True, stderr=subprocess.PIPE, stdout=subprocess.PIPE).communicate()
        if my_stderr != "":
            return False
        pycfile_secondary = file_secondary + "c"
        return cmpPyc(lockUnPyc, pycfile_original, pycfile_secondary)
    return False

def dotest((lockPrint,lockUnPyc, file, version, python_cmd)):
    cfile = os.path.join("bytecode_" + version, file) + "c"
    (my_stdout, my_stderr) = subprocess.Popen([python_cmd, "-c", "import py_compile;py_compile.compile(r'"+file+"',r'"+cfile+"',doraise=True)"], \
                shell = True, stderr=subprocess.PIPE, stdout=subprocess.PIPE).communicate()
    #print "1"+my_stderr+"1"
    if my_stderr != "":
        return (None, None, file)
    if test(lockUnPyc, cfile, python_cmd):
        lockPrint.acquire()
        #sys.stdout.write("-> %s\t[ok]\n" % file)
        print "-> ", file.ljust(30),"\t[ok]" 
        lockPrint.release()
        return (file, None, None)
    else:
        lockPrint.acquire()
        #sys.stdout.write("-> %s\t[failed]\n" % file)
        print "-> ", file.ljust(30),"\t[failed]" 
        # print "-> %s\t[failed]" % file
        lockPrint.release()
        return (None, file, None)
            
def expandDir(dir):
    lst = []
    def cb(lst, dirname, fnames):
        for file in fnames:
            if os.path.isfile(os.path.join(dirname, file)) and \
                file[-3:] == '.py' and file[-6:] != '.py.py' and file != 'test.py':
                lst.append(os.path.join(dirname, file))
    os.path.walk(dir, cb, lst)
    return lst

    
if __name__ == '__main__':
    run()
