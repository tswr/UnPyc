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

import sys
import copy
import traceback
import re

import UnPycLib.Parse as Parse
import UnPycLib.Disasm as Disasm


__version__ = '0.18'

__usage = "Usage: ./UnPyc [dvvDgcVh] <file>\n"

__copyright = "--== Copyright ==--\n" \
              "(c) Dmitri Kornev, 2009\ne-mail: tswr@tswr.ru\nwebpage: http://d.tswr.ru/\n"

__version = "--== Version ==--\n" \
            "unpyc v%s (testing)\n" % __version__

__help = "--== Help ==--\n" \
	 + __usage + \
	 "d  - disassemble\n" \
	 "x  - show xref`s (used with d)\n" \
	 "v  - verbose (used with d)\n" \
	 "vv - very verbose (used with d)\n" \
	 "D  - decompile (not implemented yet)\n" \
	 "g  - gui (control flows)\n" \
	 "c  - copyright\n" \
	 "V  - version\n" \
	 "h  - help\n" 

__doc__ = """
UnPyc - program for disassembling and decompiling *.pyc files.

`./UnPyc cVh`::
%s
%s
%s
""" % tuple(map(lambda x:re.compile(r'^',re.M).sub(' ',x),(__copyright,__version,__help))) # for epydoc to be ok

if __name__ == '__main__':
	verbose = 0
	xref = False

	if len(sys.argv) not in (2, 3): print __usage; exit(-1)
	if 'c' in sys.argv[1]: print __copyright
	if 'V' in sys.argv[1]: print __version
	if 'h' in sys.argv[1]: print __help
	if 'x' in sys.argv[1]: xref = True
	if 'v' in sys.argv[1]:
		if 'vv' in sys.argv[1]: verbose = 2
		else: verbose = 1

	if len(sys.argv) == 3:
		try:
			p = Parse.Parser(sys.argv[2], verboseDisasm=verbose, xrefDisasm=xref)
		except (Parse.ParseErrorException, Parse.IOErrorException, Parse.BadFirstObjectException), p:
			print p
			sys.exit(-1)
		except:
			print ">>> Unexpected exception:"
			traceback.print_exc()
			sys.exit(-3)

		if 'd' in sys.argv[1]:
			print "--== Disasm ==--"
			print p.co.str()

		if 'D' in sys.argv[1]:
			print "# --== Decompile ==--"
			print ">>> not implemented yet"

		if 'g' in sys.argv[1]:
			try:
				import UnPycLib.Gui as Gui
			except:
				print ">>> Cannot load Gui. Please make sure that you have python-tk installed on your system."
				sys.exit(-2)

			def cmp(x,y):
				if x < y: return -1
				if x > y: return 1
				return 0

			def whichBlock(i, a):
				b = -1
				for s in a:
					if i < s:	
						return b
					b += 1
				return b

			ga = Gui.App()
			da = Disasm.Disassembler(p.co)
			cb = da.getAllCodeBlocks()
			a = sorted(cb.blocks.keys())
		
			l = len(da.co.code.value)
			y = 0
		
			tbs = []
			nl = {}
			for i in range(len(a)):
				if i < len(a) - 1:
					b = ga.TextBox(da.codeDisasm(a[i], a[i+1] - a[i]), 300, y)
					y += b.height() + 10
					tbs.append(b)
				else:
					tbs.append(ga.TextBox(da.codeDisasm(a[i], l - a[i]), 300, y))
			for block in a:
				for s in cb.blocks[block]:
					ga.connectBlocks(tbs[whichBlock(s[0], a)], tbs[whichBlock(block, a)], s[1])
					nl[whichBlock(s[0], a)] = 1
			for block in a:
				if whichBlock(block,a) not in nl and whichBlock(block, a) + 1 < len(tbs):
					ga.connectBlocks(tbs[whichBlock(block, a)], tbs[whichBlock(block, a)+1], 2)
			ga.start()
