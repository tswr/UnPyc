#!/usr/bin/perl

open F, "Opcodes.html";
$\ = $/;
$/ = undef;
$_ = <F>;
close F;
while (m!<tr>\s*<td>([0-9a-f]+)h</td>.*?<td><pre>\n(.*?)\n</pre></td>!isg) {
	open F, ">x/$1.py";
	print F $2;
	close F;
}
