# !/usr/bin/env python

''' YapDi Example - Demonstrate basic YapDi functionality.
	Author - Kasun Herath <kasunh01@gmail.com>
	USAGE - python basic.py start|stop|restart
	python basic.py start would execute count() in daemon mode 
	if there is no instance already running. 
	count() prints a counting number to syslog. To view output of
	count() execute a follow tail to syslog file. Most probably 
	tail -f /var/log/syslog under linux and tail -f /var/log/messages
	under BSD.
	python basic.py stop would kill any running instance.
	python basic.py restart would kill any running instance; and
	start an instance. '''

import time
import yapdi
import os
import glob

os.system("modprobe w1-gpio")
os.system("modprobe w1-therm")

base_dir = "/sys/bus/w1/devices/"
device_folder = glob.glob(base_dir + "28*")[0]
device_file = device_folder + "/w1_slave"

COMMAND_START = 'start'
COMMAND_STOP = 'stop'
COMMAND_RESTART = 'restart'

frequency = 1

def read_temp_raw():
	f = open(device_file, 'r')
	lines = f.readlines()
	f.close()
	return lines

def read_temp():
	lines = read_temp_raw()
	while lines[0].strip()[-3:] != 'YES':
		time.sleep(0.2)
		lines = read_temp_raw()
	equal_pos = lines[1].find('t=')
	if equal_pos != -1:
		temp_string = lines[1][equal_pos+2:]
		temp_c = float(temp_string)/1000
		return temp_c

def get_arguments():
	global frequency
	frequency = int(sys.argv[2])

def usage():
	print("USAGE: python %s %s|%s|%s" % (sys.argv[0], COMMAND_START, COMMAND_STOP, COMMAND_RESTART))

# Invalid executions
if len(sys.argv) < 2 or sys.argv[1] not in [COMMAND_START, COMMAND_STOP, COMMAND_RESTART]:
	usage()
	exit()

def count(): #FIXME name of the function
	while 1:
		f = open('data/samples.txt', 'a+')
		f.write(str(read_temp()) + "; " + strftime("%a, %d %b %Y %H:%M:%S", gmtime()) + "\n")
		f.close()
		time.sleep(frequency * 60)

if sys.argv[1] == COMMAND_START:
	get_arguments()
	daemon = yapdi.Daemon()

	# Check whether an instance is already running
	if daemon.status():
		print("An instance is already running.")
		exit()
	retcode = daemon.daemonize()

	# Execute if daemonization was successful else exit
	if retcode == yapdi.OPERATION_SUCCESSFUL:
		count()
	else:
		print('Daemonization failed')

elif sys.argv[1] == COMMAND_STOP:
	daemon = yapdi.Daemon()

	# Check whether no instance is running
	if not daemon.status():
		print("No instance running.")
		exit()
	retcode = daemon.kill()
	if retcode == yapdi.OPERATION_FAILED:
		print('Trying to stop running instance failed')

elif sys.argv[1] == COMMAND_RESTART:
	get_arguments()
	daemon = yapdi.Daemon()
	retcode = daemon.restart()

	# Execute if daemonization was successful else exit
	if retcode == yapdi.OPERATION_SUCCESSFUL:
		count()
	else:
		print('Daemonization failed')