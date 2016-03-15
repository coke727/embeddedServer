#!/usr/bin/python

import time, threading, random, sys, getopt, signal
from time import gmtime, strftime
import base64

frequency = 1
terminate = False
address= ""
user = ""
password = ""
port = ""
password = ""

# Take a temperature sample generated with a gaussian distribution which mean is the last sample taken and a standard deviation of 0.73.
#def create_file():
	#TODO create file to transfer, name, data, etc

# Gracefully program finish when ctrl+c signal is done.
def signal_handling(signum,frame):           
	global terminate
	terminate = True

signal.signal(signal.SIGINT,signal_handling)

# Transfer file and set time for the next transfer.
def run(usr, password, addr, frec, dir, port):

	if(terminate):
		print "Shutting down transfer script."
		sys.exit(0)
	else:
		#TODO Enviar por scp los datos
		print "Set Timer"
		threading.Timer(frequency, run).start()

def setFrequency(frec):
	global frequency
	frequency = frec

def setAddress(addr):
	global address
	frequency = addr

def setUser(usr):
	global user
	user = usr

#TODO get time restante para cambiar frec, almacenar var con last timestamp del ultimo scp
#TODO password
#run()

def main(argv):
	global last_sample
	global frequency

	try:
		opts, args = getopt.getopt(argv,"u:h:d:p:c:f",["user","address","directory","port","password","frec"])
	except getopt.GetoptError:
		print 'sensor.py -f <frequency> -t <temperature>'
		sys.exit(2)
	for opt, arg in opts:
		if opt in ("-u", "--user"):
			print "temp: " + str(arg)
			last_sample = float(arg)
		elif opt in ("-f", "--frec"):
			print "frec: " + str(arg)
			frequency = float(arg)
		elif opt in ("-d", "--directory"):
			print "frec: " + str(arg)
			frequency = float(arg)
		elif opt in ("-p", "--port"):
			print "frec: " + str(arg)
			frequency = float(arg)
		elif opt in ("-f", "--password"):
			print "frec: " + str(arg)
			frequency = float(arg)

	run()

if __name__ == "__main__":
   main(sys.argv[1:])

