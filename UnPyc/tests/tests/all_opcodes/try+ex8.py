b()
try:
	print 1
except TypeError as ex:
	print 2
except:
	print 3
finally:
	print 5
a()
