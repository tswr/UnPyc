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
#                                                      changed the format of checking tests: two compiled files compars now (source -> compiled and decompiled -> compiled).

'''
 >> Testing system for project UnPyc <<
 --== Help ==--
 Usage: test.py  <dirname>|<filename> [<dirname>|<filename>]*
                [-v] <version>
                [-D]
                
 Arguments:
  <dirname>|<filename>  recursive testing begins with this folders, 
                        testing this files
 
 Options:
    -v, --version       set version for compilation
                        <version> format: x.x (example: 2.6)
    -D, --nodelete      don't delete .pyc, .py files after testing
                        (by default deletes, if the test is ok)
'''

__usage = '''
        test.py  <dirname>|<filename> [<dirname>|<filename>]*
                [-v] <version>
                [-D]
                [-h]

 Arguments:
  <dirname>|<filename>  recursive testing begins with this folders, 
                        testing this files'''

import os
import sys
import py_compile
import subprocess

import optparse

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
# end key_parse
    totest = []
    for entry in args:
        if os.path.isfile(entry):
            totest.append(entry)
        elif os.path.isdir(entry):
            totest.extend(expandDir(entry))
        else:
            print >> sys.stderr, ">>> no such file or directory %s" % entry
    dotest(totest, options.version, options.nodelete, python_cmd)


def cmpPyc(pycfile_original, pycfile_secondary):
    (my_stdout, my_stderr) = subprocess.Popen(["UnPyc", "--diff=0", pycfile_original, pycfile_secondary], shell = True, stdout=subprocess.PIPE).communicate()
    if my_stdout.count('# Identical with specified precision'):
        return True
    else:
        fh_err = open(pycfile_secondary + "_err", 'w')
        fh_err.write(my_stdout)
        fh_err.close()
        return False
    
def test(pycfile_original, python_cmd):
    if os.path.isfile(pycfile_original):
        file_secondary = pycfile_original + ".py"
        (my_stdout, my_stderr) = subprocess.Popen(["UnPyc", "-D", pycfile_original,">",file_secondary], shell = True, stderr=subprocess.PIPE).communicate()
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
        return cmpPyc(pycfile_original, pycfile_secondary)
    return False

def dotest(totest, version, nodelete, python_cmd):
    ok = []
    failed = []
    bad_test = []
    for file in totest:
        cfile = os.path.join("bytecode_" + version, file) + "c"
        cfile_dir = os.path.dirname(cfile)
        if not os.path.exists(cfile_dir):
            os.makedirs(cfile_dir)
        elif not os.path.isdir(cfile_dir):
            print 'Cannot create dir "' + cfile_dir + '"!'
            continue
                
        (my_stdout, my_stderr) = subprocess.Popen([python_cmd, "-c", "import py_compile;py_compile.compile(r'"+file+"',r'"+cfile+"',doraise=True)"], \
                    shell = True, stderr=subprocess.PIPE, stdout=subprocess.PIPE).communicate()
        if my_stderr != "":
            bad_test.append(file)
            continue
        print "-> %s\t" % file,
        if test(cfile, python_cmd):
            ok.append(file)
            print "[ok]"
            if not nodelete:
                try:
                    os.unlink(cfile)
                except all_errors as e:
                    print 'Cannot delete the file: ' + cfile
                    print str(e)
                try:
                    os.unlink(cfile+".py")
                except all_errors as e:
                    print 'Cannot delete the file: ' + cfile + ".py"
                    print str(e)
                try:
                    os.unlink(cfile+".pyc")
                except all_errors as e:
                    print 'Cannot delete the file: ' + cfile + ".pyc"
                    print str(e)
        else:
            failed.append(file)
            print "[failed]"
    print "___ Statistics ___"
    print "OK(%d)" % (len(ok))
    print "FAILED(%d):\n    %s" % (len(failed), "\n    ".join(failed))
    print "BAD_TEST(%d):\n    %s" % (len(bad_test), "\n    ".join(bad_test))

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
