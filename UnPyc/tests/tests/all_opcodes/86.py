def f():
	a = 1
	def g():
		return a + 1

	return g()

print f()
