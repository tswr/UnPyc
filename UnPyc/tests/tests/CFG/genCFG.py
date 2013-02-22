#!/usr/bin/python

# [The "BSD licence"]
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

'''
 >> Generator of tests on Control Flow Graph <<

 Usage: genCFG.py <depth>

 This program gets parameters from file "genCFG.ini".
 
 Arguments:
  <depth>   Generator will create tests with structure's enclosure of <depth>

'''

import sys
import os
import re
import string


def getBlocks(iniName):
    blocks = []
    lines = []
    try:
        fh = open(iniName, 'r')
        lines = fh.readlines()
        fh.close()
    except IOError:
        print 'Cannot open ini-file: "'+iniName+'"!'
        sys.exit(0)
    
    for line in lines:
        badLine = False
        line = re.sub("\n$", "", line)
        if line[:1] == "#":
            continue
        stats = re.split("\"\s*;\s*\"|^\"|\"$", line)
        for stat in stats:
            if stat == "":
                stats.remove(stat)
        if not stats:
            continue

        name = stats.pop(0)
        regex = ""
        # Choosing #block# !
        if name[:7] == "#block#":
            for stat in stats:
                if re.search("#block#", stat):
                    print "Recursive record don't permitted: \""+stat+"\"!"
                    badLine = True
                    break
        if badLine:
            continue
        
        for stat in stats:
            isBlock = False
            foundBlock = re.search(":\s*{(.*)}\s*$", stat)
            if foundBlock:
                inBlocks = re.split("\s*;\s*", foundBlock.group(1))
                for inBlock in inBlocks:
                    if inBlock == "":
                        inBlocks.remove(inBlock)
                stat = re.sub(":\s*{.*}\s*$", ":", stat)
                isBlock = True

            if re.search("#block#", stat):
                print "Incorrect record: \""+stat+"\"!"
                badLine = True
                break
            regex = regex + "\t{cur_depth}"+stat+"\n"
            if isBlock:
                for inBlock in inBlocks:
                    if inBlock != "#block#":
                        regex = regex + "\t\t{cur_depth}"+inBlock+"\n"
                    else:
                        regex = regex + "#block#\n"
        if badLine:
            continue
        regex = re.sub("\n$", "", regex)    
        
        blocks.append((name, regex))
       
    return blocks

def goNextDepth(cur_depth, max_depth, program, blocks, file_name):
    if cur_depth == max_depth:
        program_pass = re.sub("#block#", "\t"*cur_depth+"pass", program)
        file_name_pass = "pass_"+file_name
        try:
            fh = open(os.path.join(str(max_depth), os.path.join("pass", file_name_pass)), 'w')
            fh.write(program_pass)
            fh.close()
        except IOError:
            print 'Cannot create file: "'+file_name_pass+'"!'

        program_return = re.sub("#block#", "\t"*cur_depth+"return", program)
        program_return = re.sub("\n","\n\t", program_return)
        program_return = "def f():\n\t"+program_return
        file_name_return = "return_"+file_name
        try:
            fh = open(os.path.join(str(max_depth), os.path.join("return", file_name_return)), 'w')
            fh.write(program_return)
            fh.close()
        except IOError:
            print 'Cannot create file: "'+file_name_return+'"!'

        for (name_bl, block) in blocks:
            if name_bl[:7] != "#block#":
                continue
            block = re.sub("\t\{cur_depth}", "\t"*cur_depth, block)
            program_name_bl = re.sub("#block#", block, program)
            file_name_name_bl = name_bl+"_"+file_name
            try:
                fh = open(os.path.join(str(max_depth), os.path.join(name_bl, file_name_name_bl)), 'w')
                fh.write(program_name_bl)
                fh.close()
            except IOError:
                print 'Cannot create file: "'+file_name_name_bl+'"!'
            
    else:   # cur_depth < max_depth
        for (prefix, block) in blocks:
            if prefix[:7] == "#block#":
                continue
            block = re.sub("\t\{cur_depth}", "\t"*cur_depth, block)
            goNextDepth(cur_depth+1, max_depth, re.sub("#block#", block, program), blocks, prefix+"_"+file_name)

            
if __name__ == '__main__':
    if len(sys.argv) < 2:
        print "Input depth!"
        sys.exit(0)
    max_depth = sys.argv[1]

    pass_dir = os.path.join(max_depth,"pass")
    if not os.path.exists(pass_dir):
        os.makedirs(pass_dir)
    elif not os.path.isdir(pass_dir):
        print 'Cannot create dir "' + pass_dir + '"!'
        sys.exit(0)
    return_dir = os.path.join(max_depth,"return")
    if not os.path.exists(return_dir):
        os.makedirs(return_dir)
    elif not os.path.isdir(return_dir):
        print 'Cannot create dir "' + return_dir + '"!'
        sys.exit(0)

    iniName = "genCFG.ini"
    blocks = getBlocks(iniName)

    for (name, block) in blocks:
        if name[:7] != "#block#":
            continue
        block_dir = os.path.join(max_depth,name)
        if not os.path.exists(block_dir):
            os.makedirs(block_dir)
        elif not os.path.isdir(block_dir):
            print 'Cannot create dir "' + block_dir + '"!'
            blocks.remove((name, block))

    cur_depth = 0;
    program = "#block#\n"
    file_name = ".py"

    goNextDepth(cur_depth, string.atoi(max_depth), program, blocks, file_name)

