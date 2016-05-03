import os
import commands
import glob
import yapdi
import sys
sys.path.append( "./lib" )
import syslog
import datetime
import time
import yapdi
from os import listdir
from os.path import isfile, join
import utils

os.system("modprobe w1-gpio")
os.system("modprobe w1-therm")

samples_path ="./data/"
base_dir = "/sys/bus/w1/devices/"
device_folder = glob.glob(base_dir + "28*")[0]
device_file = device_folder + "/w1_slave"

COMMAND_START = 'start'
COMMAND_STOP = 'stop'
COMMAND_RESTART = 'restart'

frequency = 600
number_samples = 120

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
	global number_samples

	frequency = int(utils.getConfiguration("frequency_temp"))
	number_samples = int(utils.getConfiguration("file_size"))

def usage():
	print("USAGE: python %s %s|%s|%s" % (sys.argv[0], COMMAND_START, COMMAND_STOP, COMMAND_RESTART))

# Invalid executions
if len(sys.argv) < 2 or sys.argv[1] not in [COMMAND_START, COMMAND_STOP, COMMAND_RESTART]:
	usage()
	exit()

#Get current data file and if there is no data file or the data file is full create a new one.
def get_data_file():
	datafiles = [f for f in listdir(samples_path) if isfile(join(samples_path, f))]
	datafiles.sort(reverse=True)
	samples_in_file = 0
	try:
		with open(samples_path+datafiles[0]) as samples:
			samples_in_file = enumerate(samples)
			if(samples_in_file >= number_samples):
				create_empty("datafile_"+time.strftime("%y.%m.%d_%H.%M.%S", time.gmtime()) + ".txt")
				return ("datafile_"+time.strftime("%y.%m.%d_%H.%M.%S", time.gmtime()) + ".txt", 0)
			else:
				return (samples_path+datafiles[0], samples_in_file)
	except:
		create_empty("datafile_"+time.strftime("%y.%m.%d_%H.%M.%S", time.gmtime()) + ".txt")
		return ("datafile_"+time.strftime("%y.%m.%d_%H.%M.%S", time.gmtime()) + ".txt", 0)

def create_empty(name):
	file = open("samples_path/"+name, 'w+')
	file.close()


def count():
	get_arguments()
	file_data = get_data_file()
	samples_in_file = file_data[1]
	file_path = file_data[0]

	while 1:
		if (samples_in_file >= number_samples):
			file_data = get_data_file()
			file_path = file_data[0]
			samples_in_file = file_data[1]
		temp_c = read_temp() 
		time_now = time.strftime("%a, %d %b %Y %H:%M:%S", time.gmtime())
		with file(file_path,'r') as original: data = original.read()
		with file(file_path,'w+') as modified: modified.write(str(temp_c) + "; "+ time_now+"\n" + data)
		samples_in_file+=1
		time.sleep(frequency)

if sys.argv[1] == COMMAND_START:
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
	daemon = yapdi.Daemon()
	retcode = daemon.restart()

	# Execute if daemonization was successful else exit
	if retcode == yapdi.OPERATION_SUCCESSFUL:
		count()
	else:
		print('Daemonization failed')
	print('Hello Daemon')
