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
error = 0
log_path = "./logs/templog.txt"

""" Daemon which periodically read the temperature sensor and store the sample taken in a data file.

There are three commands available for control this daemon during the execution time:
* COMMAND_START start the daemon process
* COMMAND_STOP kill the daemon process
* COMMAND_RESTART restart the daemon

The global variables of this module are:
:param frequency: time between each sample.
:param number_samples: number of samples in each file. 120 is the default value.
:param error: value substracted from the sensor temperature in order to correct the sensor error.
:param log_path: path where store the logs generated for the daemon.
:param samples_path: path where the samples are stored.
:param base_dir: folder where are the devices connected to system.
:param device_folder: folder where is the temperature sensor.
:param device_file: path to file where actual temperature value is stored.
:type frequency: int
:type number_samples: int
:type error: int
:type log_path: string
:type samples_path: string
:type base_dir: string
:type device_folder: string
:type device_file: string
"""

def read_temp_raw():
	""" Read the output of the temperature sensor. This is not human readable information.

	:return: sample taken from the temperature sensor.
    :rtype: string
	"""
	f = open(device_file, 'r')
	lines = f.readlines()
	f.close()
	return lines

def read_temp():
	""" Translate the sensor sample to a human readable format in celsius degrees.

	:return: sample taken from the temperature sensor.
    :rtype: float
	"""
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
	""" Read the configuration files and get the actual values of the configurations.

	The configuration this sensor use are:
	* Error: stored in "sensor_error" configuration file.
	* Frequency: stored in "frequency_temp" configuration file.
	* Number of samples: stored in "file_size" configuration file.
	"""
	global frequency
	global number_samples
	global error

	error = int(utils.getConfiguration("sensor_error"))
	frequency = int(utils.getConfiguration("frequency_temp"))
	number_samples = int(utils.getConfiguration("file_size"))

	utils.log(log_path,"Get arguments: Frequency "+ str(frequency) +" and Number Samples " + str(number_samples) + " and Error: " + error)

def usage():
	""" Print in the shell the right usage of this daemon.
	"""
	print("USAGE: python %s %s|%s|%s" % (sys.argv[0], COMMAND_START, COMMAND_STOP, COMMAND_RESTART))

# Invalid executions
if len(sys.argv) < 2 or sys.argv[1] not in [COMMAND_START, COMMAND_STOP, COMMAND_RESTART]:
	usage()
	exit()

#Get current data file and if there is no data file or the data file is full create a new one.
def get_data_file():
	""" Gets the current data file where write the next sample.

	Gets the last created sample file in order to store there the new sample. If the last file has the maximun
	number of samples the function will create a new empty file using the actual time stamp as part of the name.
	"""
	datafiles = [f for f in listdir(samples_path) if isfile(join(samples_path, f))]
	datafiles.sort(reverse=True)
	samples_in_file = 0
	try:
		with open(samples_path+datafiles[0]) as samples:
			samples_in_file = len(samples.readlines())
			if(samples_in_file >= number_samples):
				create_empty("datafile_"+time.strftime("%y.%m.%d_%H.%M.%S", time.localtime()) + ".txt")
				return (samples_path+"datafile_"+time.strftime("%y.%m.%d_%H.%M.%S", time.localtime()) + ".txt", 0)
			else:
				return (samples_path+datafiles[0], samples_in_file)
	except:
		create_empty("datafile_"+time.strftime("%y.%m.%d_%H.%M.%S", time.localtime()) + ".txt")
		return (samples_path+"datafile_"+time.strftime("%y.%m.%d_%H.%M.%S", time.localtime()) + ".txt", 0)

def create_empty(name):
	""" Create a new empty data file.
	"""
	file = open(samples_path+name, 'w+')
	file.close()
	utils.log(log_path,"New data file: datafile_"+time.strftime("%y.%m.%d_%H.%M.%S", time.localtime()) + ".txt")


def count():
	""" Infinite loop executed by this daemon. In every iteration the daemon gets the configuration values and the file where write
	the new sample. Then the daemon gets the temperature sample and stores it with a time stamp in the data file.
	"""
	get_arguments()
	file_data = get_data_file()
	samples_in_file = file_data[1]
	file_path = file_data[0]

	while 1:
		if (samples_in_file >= number_samples):
			utils.log(log_path,"File completed: " + str(samples_in_file) + " samples with limit "+ str(number_samples))
			file_data = get_data_file()
			file_path = file_data[0]
			samples_in_file = file_data[1]
		temp_c = read_temp() + error
		time_now = time.strftime("%a, %d %b %Y %H:%M:%S", time.localtime())
		try:
			with file(file_path,'r') as original: data = original.read()
		except:
			utils.log(log_path,"Can't open actual data file. Skipping data file and creating new one.")
			with file("datafile_"+time.strftime("%y.%m.%d_%H.%M.%S", time.localtime()) + ".txt",'w+') as original: data = original.read()

		with file(file_path,'w+') as modified: modified.write(str(temp_c) + "; "+ time_now+"\n" + data)
		samples_in_file+=1
		time.sleep(frequency*60)

if sys.argv[1] == COMMAND_START:
	daemon = yapdi.Daemon(pidfile='/var/run/temp.pid')

	# Check whether an instance is already running
	if daemon.status():
		print("An instance is already running.")
		exit()
	retcode = daemon.daemonize()

	# Execute if daemonization was successful else exit
	if retcode == yapdi.OPERATION_SUCCESSFUL:
		utils.log(log_path,"Starting temperature daemon.")
		count()
	else:
		print('Daemonization failed')

elif sys.argv[1] == COMMAND_STOP:
	daemon = yapdi.Daemon(pidfile='/var/run/temp.pid')

	# Check whether no instance is running
	if not daemon.status():
		print("No instance running.")
		exit()

	utils.log(log_path,"Stoping temperature daemon.")
	retcode = daemon.kill()
	if retcode == yapdi.OPERATION_FAILED:
		print('Trying to stop running instance failed')

elif sys.argv[1] == COMMAND_RESTART:
	daemon = yapdi.Daemon(pidfile='/var/run/temp.pid')
	utils.log(log_path,"Daemon restarted.")
	retcode = daemon.restart()

	# Execute if daemonization was successful else exit
	if retcode == yapdi.OPERATION_SUCCESSFUL:
		count()
	else:
		print('Daemonization failed')
	print('Hello Daemon')
