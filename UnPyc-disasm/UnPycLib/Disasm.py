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

import struct

import Opcodes as Opcodes
import Parse as Parse

__doc__ = """*.pyc disassembler."""

class Command:
	"""Single command in bytecode (its offset, opcode, mnemonics, argument)."""

	def __init__(self, offset, opcode, mnemonics, argument=None):
		"""
		@param offset: offset of the command in co_code.
		@param opcode: byte, that defines command.
		@param mnemonics: mnemonics of the command.
		@param argument: word, that defines argument (None if command takes no arguments).
		"""
		self.offset = offset
		self.opcode = opcode
		self.argument = argument
		self.mnemonics = mnemonics
		if argument is not None: self.length = 3
		else: self.length = 1

class CodeBlocks:
	"""Code blocks of a given program that form its control flow graph."""

	def __init__(self):
		"""Simple constructor."""
		self.blocks = {0:[]}

	def add(self, where, xref=None, name=None):
		"""
		Add a new CodeBlock to the collection.
		@param where: offset of the added block.
		@param xref: offset of the block, that references the added block.
		@param name: type of reference (JF, JIF, NJIF, JIT, NJIT, JA, finally, except).
		"""
		if xref == None and name == None:
			if where not in self.blocks: self.blocks[where] = []
		else:
			if where in self.blocks: self.blocks[where].append((xref, name))
			else: self.blocks[where] = [(xref, name)]

	def strkey(self, k):
		"""
		Stringify the given CodeBlock.
		@param k: offset of the block to stringify.
		"""
		return ", ".join(("%s(%.8X)") % (n, x) for (x, n) in self.blocks[k])

	def __str__(self):
		"""Stringifier."""
		r = ''
		for k in sorted(self.blocks.keys()): r += "%.8X <- " % k + self.strkey(k) + "\n"
		return r

class Disassembler:
	"""Disassembler itself."""

	def __init__(self, co):	
		"""
		@param co: code object, that is going to be disassembled.
		"""
		self.co = co
		self.__commands = None

	@staticmethod
	def disasmCommands(co_code):
		"""
		@param co_code: bytecode.
		@return: array of L{Command} class instances.
		"""
		commands = []
		i = 0
		border = len(co_code)
		while i < border:
			offset = i
			opcode = struct.unpack('=B', co_code[i])[0]
			i += 1
			name = None
			argument = None
			if opcode in Opcodes.opcodes:
				name = Opcodes.opcodes[opcode][0]
				if Opcodes.opcodes[opcode][1] != 0: 
					argument = Parse.getInt(co_code[i:i + Opcodes.opcodes[opcode][1]])
					i += Opcodes.opcodes[opcode][1]
			commands.append(Command(offset, opcode, name, argument))
		return commands

	def getCommands(self, offset=0, length=0):
		"""
		A caching wrapper for disasmCommands.
		@param offset: start offset in co_code.
		@param length: length of the substring in co_code.
		"""
		data = self.co.code.value
		if offset == 0 and length == 0:
			if self.__commands == None: self.__commands = self.disasmCommands(data)
			return self.__commands
		if length == 0: length = len(data) - offset
		if length + offset > len(data):	length = len(data) - offset
		return self.disasmCommands(data[offset : length + offset])

	def getAllCodeBlocks(self, offset=0, length=0):
		"""
		@param offset: start offset in co_code.
		@param length: length of the substring in co_code.
		@return: L{CodeBlocks} of current code object.
		"""
		commands = self.getCommands(offset, length)
		cb = CodeBlocks()
		for cmd in commands:
			ci = cmd.offset
			if cmd.mnemonics is not None:
				if cmd.argument is not None: 
					if cmd.mnemonics == 'JUMP_FORWARD':
						cb.add(cmd.offset + cmd.length)
						cb.add(cmd.offset + cmd.argument + cmd.length, ci, 'JF')
					elif cmd.mnemonics == 'JUMP_IF_FALSE':
						cb.add(cmd.offset + cmd.length, ci, 'NJIF')
						cb.add(cmd.offset + cmd.argument + cmd.length, ci, 'JIF')
					elif cmd.mnemonics == 'JUMP_IF_TRUE':
						cb.add(cmd.offset + cmd.length, ci, 'NJIT')
						cb.add(cmd.offset + cmd.argument + cmd.length, ci, 'JIT')
					elif cmd.mnemonics == 'JUMP_ABSOLUTE':
						cb.add(cmd.offset + cmd.length)
						cb.add(cmd.argument, ci, 'JA')
					elif cmd.mnemonics == 'SETUP_FINALLY':
						cb.add(cmd.offset + cmd.argument + cmd.length, ci, 'finally')
					elif cmd.mnemonics == 'SETUP_EXCEPT':
						cb.add(cmd.offset + cmd.length, ci, 'try')	
						cb.add(cmd.offset + cmd.argument + cmd.length, ci, 'except')
		return cb

	def codeDisasm(self, offset=0, length=0, verbose=0, xref=False):
		"""
		Makes the disassembler output.
		@param offset: start offset in co_code.
		@param length: length of the substring in co_code.
		@param verbose: verbosity of the output (0, 1, 2)
		@param xref: show back references from jumps and such.
		@return: the disassembler output.		
		"""
		cb = self.getAllCodeBlocks(offset, length)
		commands = self.getCommands(offset, length)
		r = ''
		for cmd in commands:
			if xref and cmd.offset in cb.blocks:
				xstring = cb.strkey(cmd.offset)
				if xstring != '': r += "\n> xref " + cb.strkey(cmd.offset) + "\n"
			r += "%.8X     " % cmd.offset
			r += "%.2X " % cmd.opcode
			if cmd.mnemonics is not None:
				r += '- ' + cmd.mnemonics + " " * (20 - len(cmd.mnemonics))
				if cmd.argument is not None: 
					if verbose >= 1: r += '%.4X' % cmd.argument
					if cmd.mnemonics in ('LOAD_CONST', 'COMPARE_OP', 'LOAD_FAST', 'STORE_FAST', 'DELETE_FAST',
						'IMPORT_NAME', 'IMPORT_FROM', 'STORE_GLOBAL', 'DELETE_GLOBAL', 'LOAD_GLOBAL',
						'STORE_ATTR', 'DELETE_ATTR', 'LOAD_ATTR', 'STORE_NAME', 'DELETE_NAME', 'LOAD_NAME',
						'LOAD_CLOSURE', 'LOAD_DEREF', 'STORE_DEREF', 'JUMP_FORWARD', 'JUMP_IF_TRUE', 'JUMP_IF_FALSE',
						'SETUP_FINALLY', 'SETUP_EXCEPT', 'SETUP_LOOP', 'FOR_ITER', 'JUMP_ABSOLUTE'): 
							if verbose >= 1: r += ' = '
							if cmd.mnemonics == 'LOAD_CONST':
								if self.co.consts.value[cmd.argument].__class__.__name__ == 'pyCode':
									r += self.co.consts.value[cmd.argument].info(verbose)
								else:
									#r +=  Parse.shorten(Parse.dropNewLines(self.co.consts.value[cmd.argument].info(verbose)))
									r +=  self.co.consts.value[cmd.argument].info(verbose)
							elif cmd.mnemonics == 'COMPARE_OP':
								r += '"' + Opcodes.cmp_op[cmd.argument] + '"'
							elif cmd.mnemonics in ('LOAD_FAST', 'STORE_FAST', 'DELETE_FAST'):
								r += self.co.varnames.value[cmd.argument].info(verbose)
							elif cmd.mnemonics in ('IMPORT_NAME', 'IMPORT_FROM', 
								'STORE_GLOBAL', 'DELETE_GLOBAL', 'LOAD_GLOBAL',
								'STORE_ATTR', 'DELETE_ATTR', 'LOAD_ATTR',
								'STORE_NAME', 'DELETE_NAME', 'LOAD_NAME'):
									r += self.co.names.value[cmd.argument].info(verbose)
							elif cmd.mnemonics in ('LOAD_CLOSURE', 'LOAD_DEREF', 'STORE_DEREF'):
								if cmd.argument < len(self.co.cellvars.value):
									r += self.co.cellvars.value[cmd.argument].info(verbose)
								else:
									r += self.co.freevars.value[cmd.argument - len(self.co.cellvars.value)].info(verbose)
							elif cmd.mnemonics in ('JUMP_FORWARD', 'JUMP_IF_TRUE', 'JUMP_IF_FALSE', 
								'SETUP_FINALLY', 'SETUP_EXCEPT', 'SETUP_LOOP',
								'FOR_ITER'):
									r += '-> %.8X' % (cmd.offset + cmd.argument + cmd.length)
							elif cmd.mnemonics == 'JUMP_ABSOLUTE':
								r += '-> %.8X' % cmd.argument
					else:
						if verbose == 0: r += 'r%.4X' % cmd.argument
				if verbose >= 2 and len(Opcodes.opcodes[cmd.opcode]) > 2:
					r += '\n' + Parse.indentText(Parse.narrowText(Opcodes.opcodes[cmd.opcode][2]), 1)
			r += '\n'
		return r
