from driver import Sphero
s = Sphero()
try:
	s.connect()
except IOError as e:
	print "Error:",e
	print "retrying."
	s.disconnect()
	s.connect()

s.start()