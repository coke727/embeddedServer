#!/usr/bin/python
import sys
sys.path.append( "./lib" )
from os import listdir, system
from os.path import isfile, join
import subprocess
from subprocess import PIPE
import web_maker
import time
import datetime
import utils

log_path = "./logs/weatherstationlog.txt"

def ip_configuration():
	ip = "localhost"
	newip = "localhost"
	
	try:
		with open("./config/ip", 'r') as ipfile:
			ip = ipfile.read().strip()
		ipfile.close()

		newip = subprocess.Popen(["hostname", "-I"], stdout=subprocess.PIPE).communicate()[0].split()
		if (newip[0] != ip):
			utils.log(log_path,"IP changed. New ip is " + newip)
			system('echo "'+ newip[0] +'" > ./config/ip')
			newDomain = web_maker.changeDeviceDomain(newip[0])
			utils.log(log_path, "Device domain changed to: " + newDomain)
	except:
		newip = subprocess.Popen(["hostname", "-I"], stdout=subprocess.PIPE).communicate()[0].split()
		system('echo "'+ newip[0] +'" > ./config/ip')
		utils.log(log_path, "Ip file doesn't exist, generating one.")
		web_maker.changeDeviceDomain(newip[0])
		utils.log(log_path, "Device domain changed to: " + utils.getConfiguration("domain"))

def isPowermode2_on():
	with open("./crons/pm2.tab", 'r') as cron:
		day_number = datetime.datetime.today().weekday()
		i = 0
		while (i <= day_number):
			starts = cron.next()
			i += 1
		starts = starts.split('*')
		starts = starts[1].strip()
		starts = starts.split(',')
	cron.close()
	hour_now = datetime.datetime.today().hour

	for h in starts:
		if (h == hour_now):
			return True

	return False


def powerMode_configuration():
	powermode = 0

	try:
		with open("./config/powermode", 'r') as powermodefile:
			powermode = int(powermodefile.read().strip())
		powermodefile.close()

		if( powermode == 0):
			#execute script
			system("sudo pmnormal")
			#start server
			system("sudo python server.py &")
		elif( powermode == 1):
			#execute script
			system("sudo pm1")
			#start server
			system("sudo python server.py &")
		elif( powermode == 2):
			if(utils.crontab_exist()):
				if(isPowermode2_on()):
					system("sudo pm2")
				else:
					system("sudo pm1")
			else:
				utils.log(log_path, "Crontab doesn't exist. Changing to power mode 1.")
				utils.setConfiguration("powermode", 1)
				system("pm1")

		elif( powermode == 3):
			if(utils.crontab_exist()):
				if(isPowermode2_on()):
					system("sudo pm2")
				else:
					system("sudo pm1")
			else:
				utils.log(log_path, "Crontab doesn't exist. Changing to power mode 1.")
				utils.setConfiguration("powermode", 1)
				system("pm1")
	except:
		utils.log(log_path, "Power mode config file doesn't exist. Creating one and switching to power mode 1.")
		utils.setConfiguration("powermode", 1)
		system("pm1")

def scp_configuration():
	try:
		with open("./config/scp", 'r') as scpfile:
			user = scpfile.next().strip()
			address = scpfile.next().strip()
			directory = scpfile.next().strip()
			port = scpfile.next().strip()
			password = scpfile.next().strip()
		scpfile.close()

		p = subprocess.Popen(["python", "scpdaemon.py", "start", address, user, port, directory], stdin=PIPE, stdout=PIPE)
		print p.communicate(password)
		utils.log(log_path, "Scp daemon started")
	except:
		utils.log(log_path, "Scp isn't set up. Not starting scp daemon.")

def temperature_configuration():
	try:
		with open("./config/frequency_temp", 'r') as tempfile:
			frequency = tempfile.next().strip()
		tempfile.close()
	except:
		frequency = 10
		utils.log(log_path, "Temperature isn't set up. Creating default configuration file. Default Frequency 10 minutes.")
		utils.setConfiguration("frequency_temp", frequency)

	try:
		with open("./config/file_size", 'r') as sizefile:
			size = sizefile.next().strip()
		sizefile.close()
	except:
		size = 120
		utils.log(log_path, "File size isn't set up. Creating default configuration file. Default file size is 120 samples.")
		utils.setConfiguration("file_size", size)

	system('sudo python tempdaemon.py start &')
	utils.log(log_path, "Temperature daemon started. Frequency " + str(frequency) + "min and file size "+ str(size) + " samples.")

def main(argv):
	utils.log(log_path, "Device just boot. Starting weather station.")

	#Check temperature sensor and start temperature daemon.
	temperature_configuration()

	#Check if exist scp configuration, if it exist start scp daemon.
	scp_configuration()

	#Check actual device ip to adapt the hostname and hosts files in order to make visible device in BUT wifi network. 
	ip_configuration()

	#Check actual power saving mode and start server if it is necesary.
	powerMode_configuration()

	exit()

if __name__ == "__main__":
   main(sys.argv[1:])

