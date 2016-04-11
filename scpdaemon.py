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
import syslog
import time
from transfer import SCPClient
import paramiko
import yapdi

COMMAND_START = 'start'
COMMAND_STOP = 'stop'
COMMAND_RESTART = 'restart'

frequency = 1
address= ""
user = ""
password = ""
port = 22
directory = ""

def createSSHClient(server, port, user, password):
	client = paramiko.SSHClient()
	client.load_system_host_keys()
	client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
	client.connect(server, port, user, password)
	return client

def get_arguments():
	global frequency
	global address
	global user
	global password
	global port
	global directory

	frequency = int(sys.argv[2])
	address = sys.argv[3]
	user = sys.argv [4]
	port = int(sys.argv[5])
	directory = sys.argv[6]
	password = raw_input()
	#print ("frec %s addr %s user %s port %s dir %s pass %s" % (frequency, address, user, port, directory, password))

def usage():
	print("USAGE: python %s %s|%s|%s" % (sys.argv[0], COMMAND_START, COMMAND_STOP, COMMAND_RESTART))

# Invalid executions
if len(sys.argv) < 2 or sys.argv[1] not in [COMMAND_START, COMMAND_STOP, COMMAND_RESTART]:
	usage()
	exit()

def count(): #FIXME name of the function
	while 1:
		ssh = createSSHClient(address, port, user, password)
		scp = SCPClient(ssh.get_transport())
		scp.put("./data/samples.txt", directory)
		time.sleep(frequency * 3600)

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