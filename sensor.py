#!/usr/bin/python

import time, threading, random, sys, getopt, signal
from time import gmtime, strftime

last_sample = 0
frequency = 1
terminate = False

# Take a temperature sample generated with a gaussian distribution which mean is the last sample taken and a standard deviation of 0.73.
def take_sample():
	global last_sample
	last_sample = min(80, max(-10, random.gauss(last_sample, 0.73)))
	return last_sample

# Gracefully program finish when ctrl+c signal is done.
def signal_handling(signum,frame):         
	global terminate
	terminate = True

signal.signal(signal.SIGINT,signal_handling)

# Add sample to file and set time for the next sample.
def run():

	if(terminate):
		print "Shutting down sensor"
		sys.exit(0)
	else:
		f = open('data/samples.txt', 'a+')
		f.write(str(take_sample()) + "; " + strftime("%a, %d %b %Y %H:%M:%S", gmtime()) + "\n")
		f.close()
		threading.Timer(frequency, run).start()

def main(argv):
	global last_sample
	global frequency

	try:
		opts, args = getopt.getopt(argv,"t:f:",["temp","frec"])
	except getopt.GetoptError:
		print 'sensor.py -f <frequency> -t <temperature>'
		sys.exit(2)
	for opt, arg in opts:
		if opt in ("-t", "--temp"):
			print "temp: " + str(arg)
			last_sample = float(arg)
		elif opt in ("-f", "--frec"):
			print "frec: " + str(arg)
			frequency = float(arg)

	run()

if __name__ == "__main__":
   main(sys.argv[1:])

