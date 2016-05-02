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

import sys
sys.path.append( "./lib" )
import syslog
import time
import datetime
from transfer import SCPClient
import paramiko
import yapdi
from os import system, listdir
from os.path import isfile, join
import utils

COMMAND_START = 'start'
COMMAND_STOP = 'stop'
COMMAND_RESTART = 'restart'
COMMAND_RESTORE = 'restore'

address= ""
user = ""
password = ""
port = 22
directory = ""
samples_path = "./data/"
backup_samples_path = "./data/backup/"
log_path = "./logs/scplog.txt"

def createSSHClient(server, port, user, password):
	client = paramiko.SSHClient()
	client.load_system_host_keys()
	client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
	client.connect(server, port, user, password)
	return client

def get_arguments():
	global address
	global user
	global password
	global port
	global directory

	try:
		address = sys.argv[2]
		user = sys.argv [3]
		port = int(sys.argv[4])
		directory = sys.argv[5]
		password = raw_input()
		print ("addr %s user %s port %s dir %s pass %s" % (address, user, port, directory, password))

	except:
		usage()
	#print ("frec %s addr %s user %s port %s dir %s pass %s" % (frequency, address, user, port, directory, password))

def usage():
	print("USAGE: python %s %s|%s|%s|%s <address> <user> <port> <directory>" % (sys.argv[0], COMMAND_START, COMMAND_STOP, COMMAND_RESTART, COMMAND_RESTORE))

# Invalid executions
if len(sys.argv) < 2 or sys.argv[1] not in [COMMAND_START, COMMAND_STOP, COMMAND_RESTART, COMMAND_RESTORE]:
	usage()
	exit()

#every time a send a scp file i made a backup, when i want to see what files i need to send i compare the samples and the
#backup directories files.
def getFilesToSend():
	try:
		with open("./config/sendedFiles", 'r') as file:
			sendedFiles = [x.strip('\n') for x in file.readlines()]
		file.close()
	except:
		log('No files in sendedFiles configuration.')
		sendedFiles = []
	
	datafiles = [f for f in listdir(samples_path) if isfile(join(samples_path, f))]
	files_to_send = list(set(datafiles) - set(sendedFiles))
	files_to_send.sort(reverse=True)

	return files_to_send

def createBackup(file_name):
	command = 'cp -a ' + samples_path + file_name + ' ' + backup_samples_path
	system(command)
	log('Created backup of ' + file_name)

def turnWifiOn():
	system('sudo ifup wlan0')
	log('Turn on wifi for send data.')
	sleep(5)

def turnWifiOff():
	system('sudo ifdown wlan0')
	log('Turn off wifi after send data.')

def mark_as_send(file_name):
	file_size = int(utils.getConfiguration('file_size'))
	with open(samples_path+file_name) as datafile:
			samples_in_file = enumerate(datafile)
	datafile.close()

	if(samples_in_file >= file_size):
		with open("./config/sendedFiles", 'a+') as file:
			file.write(file_name+"\n")
		file.close

def log(msg):
	with open(log_path, 'a+') as log:
		log.write('['+time.strftime("%a, %d %b %Y %H:%M:%S", time.gmtime())+'] ' + msg + '\n')
	log.close()

def count():
	while 1:
		frequency = int(utils.getConfiguration('frequency_scp'))
		powermode = int(utils.getConfiguration('powermode'))

		if(powermode == 2 or powermode == 3):
			turnWifiOn()

		try:
			ssh = createSSHClient(address, port, user, password)
			scp = SCPClient(ssh.get_transport())
		except:
			log("Error trying connect with the destiny device.")
			yapdi.Daemon().kill()
			exit()

		try:
			datafiles = getFilesToSend()
			for datafile in datafiles:
				scp.put(samples_path+datafile, directory)
				createBackup(datafile)
				mark_as_send(datafile)
				log("File " + datafile + " sended to " + address)
				if(powermode == 2 or powermode == 3):
					turnWifiOff()
			time.sleep(frequency * 3600)
		except:
			log("Error sending the files.")
			time.sleep(frequency * 3600)

if sys.argv[1] == COMMAND_START:
	get_arguments()
	daemon = yapdi.Daemon()
	log("Starting daemon.")

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

elif sys.argv[1] == COMMAND_RESTORE:
	with open("./config/sendedFiles", 'w+') as file:
		print "Data about sended files cleaned."
		log("Data about sended files cleaned.")
	file.close()

elif sys.argv[1] == COMMAND_STOP:
	daemon = yapdi.Daemon()
	log("Daemon Stoped.")

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