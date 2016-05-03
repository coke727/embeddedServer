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
			log("IP changed. New ip is " + newip)
			system('echo "'+ newip[0] +'" > ./config/ip')
			set_domain(newip[0])
	except:
		newip = subprocess.Popen(["hostname", "-I"], stdout=subprocess.PIPE).communicate()[0].split()
		system("hostname -I > ./config/ip")
		log("Ip file doesn't exist, generating one.")
		set_domain(newip[0])

def set_domain(newip):
	domain = ".fit.vutbr.cz"
	hostname = "dhcpr"
	machine_number = "000"

	ip = newip.split('.')

	if (int(ip[3]) == 179):
		hostname = "dhcpr"
	elif (int(ip[3]) == 178):
		hostname = "dhcps"
	if (int(ip[3]) < 100):
		machine_number = "0"+ip[3]
	elif (int(ip[3]) < 10):
		machine_number = "00"+ip[3]

	log("New domain is " + hostname+machine_number+domain)
	web_maker.make_pages(hostname+machine_number+domain)
	system('sudo echo "' +hostname+machine_number+ '" > /etc/hostname')
	system('sudo echo -e "' +newip+ '\t' +hostname+machine_number+domain +'\t'+ hostname+machine_number+'\n" >> /etc/hosts')
	system('sudo /etc/init.d/hostname.sh')

def crontab_exist():
	try:
		with open("./crons/pm2.tab", 'r') as cron:
			log("Using actual crontab.")
		cron.close()
		return True
	except:
		return False

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
			system("sudo python server.py")
		elif( powermode == 1):
			#execute script
			system("sudo pm1")
			#start server
			system("sudo python server.py")
		elif( powermode == 2):
			if(crontab_exist()):
				if(isPowermode2_on()):
					system("sudo pm2")
				else:
					system("sudo pm1")
			else:
				log("Crontab doesn't exist. Changing to power mode 1.")
				system("echo '1' > ./config/powermode")
		elif( powermode == 3):
			if(crontab_exist()):
				if(isPowermode2_on()):
					system("sudo pm2")
				else:
					system("sudo pm1")
			else:
				log("Crontab doesn't exist. Changing to power mode 1.")
				system("echo '1' > ./config/powermode")
	except:
		log("Power mode config file doesn't exist. Creating one and switching to power mode 1.")
		system("echo '1' > ./config/powermode")
		#ejecutar pm 1

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
		log("Scp daemon started")
	except:
		log("Scp isn't set up. Not starting scp daemon.")
	
def log(msg):
	with open(log_path, 'a+') as log:
		log.write('['+time.strftime("%a, %d %b %Y %H:%M:%S", time.gmtime())+'] ' + msg + '\n')
	log.close()

def temperature_configuration():
	try:
		with open("./config/frequency_temp", 'r') as tempfile:
			frequency = tempfile.next().strip()
		tempfile.close()
	except:
		frequency = 10
		log("Temperature isn't set up. Creating default configuration file. Default Frequency 10 minutes.")
		system("echo '10' > ./config/frequency_temp")

	try:
		with open("./config/file_size", 'r') as sizefile:
			size = sizefile.next().strip()
		sizefile.close()
	except:
		size = 120
		log("File size isn't set up. Creating default configuration file. Default file size is 120 samples.")
		system("echo '120' > ./config/file_size")

	system('sudo python tempdaemon.py start')
	log("Temperature daemon started. Frequency " + frequency + "min and file size "+ size + " samples.")

def main(argv):
	log("Device just boot. Starting weather station.")

	#Check actual device ip to adapt the hostname and hosts files in order to make visible device in BUT wifi network. 
	ip_configuration()

	#Check actual power saving mode and start server if it is necesary.
	powerMode_configuration()

	#Check if exist scp configuration, if it exist start scp daemon.
	scp_configuration()

	#Check temperature sensor and start temperature daemon.
	temperature_configuration()

	

if __name__ == "__main__":
   main(sys.argv[1:])

