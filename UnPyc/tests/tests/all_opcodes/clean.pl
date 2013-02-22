#!/usr/bin/perl

$\ = $/;
$" = ", ";

for $f (<*.py>) {
	print "___ $f ___";
	system "diff $f $f.res";
	if ($? >> 8 == 0) {
		push @ok, $f;
		system("rm -fv $f.res.ok");
	} else {
		push @failed, $f;
	}
}

print "___ Statistics ___";
print "OK(".@ok."): @ok";
print "FAILED(".@failed."): @failed";
