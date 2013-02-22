#!/usr/bin/python

# [The "BSD licence"]
# Copyright (c) 2008-2009 Dmitri Kornev
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

'''
UnPyc - program for disassembling and decompiling *.pyc files.

`./UnPyc -cVh`::

 --== Copyright ==--
 [The "BSD licence"]
 Copyright (c) 2008-2009 Dmitri Kornev
 All rights reserved.
 
 e-mail:  tswr@tswr.ru
 webpage: http://d.tswr.ru/
 
 --== Version ==--
 UnPyc v0.8.2 (testing)
 
 --== Help ==--
 Usage: UnPyc -D [ --co=NAME ] [ --debugDraw ] [ -q ] <filename>
        UnPyc -d [ --co=NAME ] [ -x ] [ -v ] [ -v ] [ -q ] <filename>
        UnPyc --colist <filename>
        UnPyc -g <filename>
        UnPyc [ -h ] [ -V ] [ -c ] [ -l ]
 
 Options:
   Decompilation:
     -D, --decompile    decompile
     --debugDraw        draw intermediate CFGs
 
   Disassembly:
     -d, --disassemble  disassemble
     -x, --xref         show basic blocks and xrefs
     -v                 verbose, use twice for more verbosity
 
   Common:
     --colist           list names of all code-objects
     --co=NAME          specify code-object to work with in a dotted manner
     -q, --quiet        don't print --== HEADER ==--
 
   Gui:
     -g, --gui          gui (control flow graph)
 
   Info:
     -c, --copyright    copyright
     -l, --license      license
     -V, --version      version
     -h, --help         show this help message
'''

__version__ = '0.8.2'

import sys
import traceback
import optparse
import tempfile
import py_compile
import os

import parse
import disasm
import decompile
import text

__usage = \
     'Usage: %prog -D [ --co=NAME ] [ --debugDraw ] [ -q ] <filename>\n' \
     '       %prog -d [ --co=NAME ] [ -x ] [ -v ] [ -v ] [ -q ] <filename>\n' \
     '       %prog --colist <filename>\n' \
     '       %prog --diff=STRICT <filename> <filename>\n' \
     '       %prog -g <filename>\n' \
     '       %prog [ -h ] [ -V ] [ -c ] [ -l ]'

__copyright = '--== Copyright ==--\n' \
              '[The "BSD licence"]\n' \
              'Copyright (c) 2008-2009 Dmitri Kornev\n' \
              'All rights reserved.\n\n' \
              'e-mail:  tswr@users.sf.net\nwebpage: http://unpyc.sf.net/\n'

__license = '''--== LICENSE ==--
[The "BSD licence"]
Copyright (c) 2008-2009 Dmitri Kornev
All rights reserved.

Redistribution and use in source and binary forms, with or without
modification, are permitted provided that the following conditions are met:
    * Redistributions of source code must retain the above copyright
      notice, this list of conditions and the following disclaimer.
    * Redistributions in binary form must reproduce the above copyright
      notice, this list of conditions and the following disclaimer in the
      documentation and/or other materials provided with the distribution.
    * The name of the author may not be used to endorse or promote products
      derived from this software without specific prior written permission.

THIS SOFTWARE IS PROVIDED BY THE AUTHOR ''AS IS'' AND ANY
EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
DISCLAIMED. IN NO EVENT SHALL Dmitri Kornev BE LIABLE FOR ANY
DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES
(INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES;
LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND
ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
(INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS
SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
'''

__version = '--== Version ==--\n' \
            'UnPyc v%s (testing)\n' % __version__

def start():
    '''Starts the unpyc application.'''

    def copyright(option, opt_str, value, parser, *args, **kwargs):
        print __copyright

    def license(option, opt_str, value, parser, *args, **kwargs):
        print __license

    def version(option, opt_str, value, parser, *args, **kwargs):
        print __version

    def help(option, opt_str, value, parser, *args, **kwargs):
        print '--== Help ==--'
        parser.print_help()
        print

    parser = optparse.OptionParser(usage=__usage, add_help_option=False)

    decompileGroup = optparse.OptionGroup(parser, 'Decompilation')
    decompileGroup.add_option('-D', '--decompile',
              action='store_true', dest='decompile', default=False,
              help='decompile')
    decompileGroup.add_option('--debugDraw',
              action='store_true', dest='debugDraw', default=False,
              help='draw intermediate CFGs')
    decompileGroup.add_option('--test',
              dest='selfTest', default='-1', metavar='STRICT',
              help='run diff of the original and generated ' \
                   'pyc files after decompilation '\
                   'if STRICT is 0 - ignore filename, firstlineno, lnotab; ' \
                   'if STRICT is 1 - ignore filename; ' \
                   'if STRICT is 2 - pyc files should be identical; ' \
                   '$? is 0 if diff was ok, 1 if not')

    disasmGroup = optparse.OptionGroup(parser, 'Disassembly')
    disasmGroup.add_option('-d', '--disassemble',
              action='store_true', dest='disassemble', default=False,
              help='disassemble')
    disasmGroup.add_option('-x', '--xref',
              action='store_true', dest='xref', default=False,
              help='show basic blocks and xrefs')
    disasmGroup.add_option('-v',
              action='count', dest='verbose', default=0,
              help='verbose, use twice for more verbosity')

    commonGroup = optparse.OptionGroup(parser, 'Common')
    commonGroup.add_option('--colist',
              action='store_true', dest='colist', default=False,
              help='list names of all code-objects')
    commonGroup.add_option('--co', dest='coname', default=None, metavar='NAME',
              help='specify code-object to work with in a dotted manner')
    commonGroup.add_option('-q', '--quiet',
              action='store_true', dest='quiet', default=False,
              help='don\'t print --== HEADER ==-- and diff output')

    diffGroup = optparse.OptionGroup(parser, 'Diff')
    diffGroup.add_option('--diff',
              dest='diff', default='-1', metavar='STRICT',
              help='compare two pyc files, STRICT is 0, 1, 2')

    guiGroup = optparse.OptionGroup(parser, 'Gui')
    guiGroup.add_option('-g', '--gui',
              action='store_true', dest='gui', default=False,
              help='gui (control flow graph)')

    infoGroup = optparse.OptionGroup(parser, 'Info')
    infoGroup.add_option('-c', '--copyright',
              action='callback', callback=copyright,
              help='copyright')
    infoGroup.add_option('-l', '--license',
              action='callback', callback=license,
              help='license')
    infoGroup.add_option('-V', '--version',
              action='callback', callback=version,
              help='version')
    infoGroup.add_option('-h', '--help',
              action='callback', callback=help,
              help='show this help message')

    parser.add_option_group(decompileGroup)
    parser.add_option_group(disasmGroup)
    parser.add_option_group(commonGroup)
    parser.add_option_group(diffGroup)
    parser.add_option_group(guiGroup)
    parser.add_option_group(infoGroup)

    (options, args) = parser.parse_args()

    if options.disassemble or options.decompile or \
       options.gui or options.colist:
        if len(args) != 1:
            parser.error('incorrect number of arguments')
        else:
            filename = args[0]
            co = None
            full = True
            try:
                parser = parse.Parser(filename, verboseDisasm=options.verbose,
                                      xrefDisasm=options.xref)
                if options.coname is not None:
                    full = False
                    co = parser.findCoByAbsName(options.coname)
                    if co is None:
                        raise parse.CoNotFoundException(options.coname)
                else:
                    co = parser.co
                disassembler = disasm.Disassembler(co)
                optimizingDisassembler = disasm.Disassembler(co,
                                                             optimizeJumps=True)
                decompiler = decompile.Decompiler(optimizingDisassembler,
                                                  options.debugDraw)
            except (parse.ParseErrorException,
                    parse.IOErrorException,
                    parse.BadFirstObjectException,
                    parse.CoNotFoundException), p:
                print p
                sys.exit(-1)
            except:
                print '>>> Unexpected exception:'
                traceback.print_exc()
                sys.exit(-3)

            if options.disassemble:
                if not options.quiet: print '--== Disasm ==--'
                print disassembler.disassemble(),

            if options.decompile:
                if not options.quiet: print '# --== Decompile ==--'
                decompileStr = decompiler.decompile(full=full)
                print decompileStr,
                if options.selfTest in '012':
                    if not options.quiet: print '# --== Testing ==--'
                    fh, path = tempfile.mkstemp('.py', 'unpyc.')
                    fh = os.fdopen(fh, 'w')
                    fh.write(decompileStr)
                    fh.close()
                    try:
                        py_compile.compile(path, doraise=True)
                    except py_compile.PyCompileError:
                        if not options.quiet:
                            print '# Failed to compile the result ' \
                                  'of decompilation'
                        sys.exit(1)
                    co2 = parse.Parser(path + 'c').co
                    if not full: co2 = co2.consts.value[0]
                    os.unlink(path)
                    os.unlink(path + 'c')
                    answer = parse.DiffComment()
                    if co.__eq__(co2, strict=int(options.selfTest), \
                                 answer=answer):
                        if not options.quiet:
                            print '# Identical with specified precision\n'
                        sys.exit(0)
                    else:
                        if not options.quiet:
                            print '# Different'
                            print text.commentText(answer.message)
                        sys.exit(1)

            if options.colist:
                if not options.quiet: print ' --== CO list ==--'
                print parser.listAllCoNames(),

            if options.gui:
                try:
                    import gui
                    gui.App(disassembler).start()
                except ImportError:
                    print '>>> Cannot load gui. Please make sure that you ' \
                          'have python-tk installed on your system.'
                    sys.exit(-2)
    elif options.diff in '012':
        if len(args) != 2:            
            parser.error('incorrect number of arguments')
        else:
            print '# --== Diff ==--'
            file1, file2 = args
            try:
                co1 = parse.Parser(file1).co
                co2 = parse.Parser(file2).co
                answer = parse.DiffComment()
                if co1.__eq__(co2, strict=int(options.diff), answer=answer):
                    print '# Identical with specified precision\n'
                    sys.exit(0)
                else:
                    print '# Different:'
                    print answer.message
                    sys.exit(1)
            except (parse.ParseErrorException,
                    parse.IOErrorException,
                    parse.BadFirstObjectException,
                    parse.CoNotFoundException), p:
                print p
                sys.exit(-1)
            except SystemExit, p:
                raise p
            except:
                print '>>> Unexpected exception:'
                traceback.print_exc()
                sys.exit(-3)
    else:
        if args:
            parser.error('incorrect number of arguments')
        if len(sys.argv) == 1:
            help(None, None, None, parser)

if __name__ == '__main__':
    start()
