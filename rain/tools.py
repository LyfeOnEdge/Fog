from time import time

def timer_dec(call):
	def wrapped(*args, **kwargs):
		start = time.time()
		res = call(*args, **kwargs)
		dt = time.time() - start
		print(f'Call {call.__name__!r} took {dt}s')
		return res
	return wrapped

def perf_check(call, count, *args, **kwargs):
	start = time.time()
	for i in range(count): call(*args, **kwargs)
	dt = time.time() - start
	print(f'{count} calls of {call.__name__!r} took {dt}s')