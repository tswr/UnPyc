b()
try:
	print 1
except TypeError as ex:
	print 2
except:
	print 3
else:
	print 4
a()
