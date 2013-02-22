def f():
	with 1:
		try:
			return
		finally:
			return
		try:
			return
		finally:
			return
		print 1
	