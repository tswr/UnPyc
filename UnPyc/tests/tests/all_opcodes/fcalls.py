def f(a, b, c, d=4, e=5):
	print a
	print b
	print c
	print d
	print e
	print '-------------'

f(1, 2, 3)
f(1, 2, 3, 4)
f(1, 2, 3, e=5, d=4)
a1 = [3, 4, 5]
f(1, 2, *a1)
a2 = [3, 4]
f(1, 2, e=5, *a2)
b1 = {'c': 3, 'd': 4, 'e': 5}
f(1, 2, **b1)
b2 = {'d': 4, 'e': 5}
a3 = (2, 3)
f(1, *a3, **b2)
