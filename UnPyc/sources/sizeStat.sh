#!/bin/bash

wc -lc ./UnPyc unpyclib/*.py

#a=`find . -name \*.py -exec cat '{}' \; | wc -lc`
#l=`echo $a | awk '{ print $1 }'`
#b=`echo $a | awk '{ print $2 }'`
#echo "number of lines:  $l"
#echo "number of bytes:  $b"
#echo "number of kbytes:" `echo $b/1024 | bc`
