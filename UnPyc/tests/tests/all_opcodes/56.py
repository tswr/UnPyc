def foo():
	print 'hello'
	yield 1
	print 'world'
	yield 2

a = foo()
print a.next()
print a.next()
