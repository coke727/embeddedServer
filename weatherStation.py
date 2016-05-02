#!/usr/bin/python
import sys
sys.path.append( "./lib" )
from os import listdir, system
from os.path import isfile, join
import subprocess
from subprocess import PIPE
import web_maker

log_path = "./logs/weatherstationlog.txt"

def ip_configuration():
	ip = "localhost"
	newip = "localhost"
	
	try:
		with open("./conf/ip", 'r') as ipfile:
			ip = ipfile.read().strip()
		ipfile.close()

		newip = subprocess.Popen(["hostname", "-I"], stdout=subprocess.PIPE).communicate()[0].strip()
		if (newip != ip):
			log("IP changed. New ip is " + newip)
			set_domain(newip)
	except:
		newip = subprocess.Popen(["hostname", "-I"], stdout=subprocess.PIPE).communicate()[0].strip()
		system("hostname -I > ./conf/ip")
		log("Ip file doesn't exist, generating one.")
		set_domain(newip)

def set_domain(newip):
	domain = ".fit.vutbr.cz"
	hostname = "dhcpr"
	machine_number = "000"

	system('echo "'+ newip +'" > ./conf/ip')
	ip = newip.split('.')

	if (int(ip[3]) == 179):
		hostname = "dhcpr"
	elif (int(ip[3]) == 178):
		hostname = "dhcps"
	if (int(ip[3]) < 100):
		machine_number = "0"+ip[3]
	elif (int(ip[3]) < 100):
		machine_number = "00"+ip[3]

	log("New domain is " + hostname+machine_number+domain)
	web_maker.make_pages(hostname+machine_number+domain)
	system('sudo echo "' +hostname+machine_number+ '" > /etc/hostname')
	system('sudo echo -e "' newip+ '\t' +hostname+machine_number+domain +'\t'+ hostname+machine_number+'\n" >> /etc/hosts')

def powerMode_configuration():
	powermode = 0

	try:
		with open("./conf/powermode", 'r') as powermodefile:
			powermode = int(powermodefile.read().strip())
		powermodefile.close()

		if( powermode = 0):
			#execute script
			#start server
		elif( powermode = 1):
			#execute script
			#start server
		elif( powermode = 2):
			#get crontab (si no existe pasar a 1) y ejecutarla.
			#mirar en que intervalo estamos si dentro de 2 o fuera y actuar en funcion.
		elif( powermode = 3):
			#hacer lo mismo que en modo 2
	except:
		log("Power mode config file doesn't exist. Creating one and switching to power mode 1.")
		system("echo '1' > ./conf/powermode")
		#ejecutar pm 1

def scp_configuration():
	try:
		with open("./conf/scp", 'r') as scpfile:
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
		with open("./conf/frequency_temp", 'r') as tempfile:
			frequency = tempfile.next().strip()
		tempfile.close()
	except:
		log("Temperature isn't set up. Creating default configuration file. Default Frequency 10 minutes.")
		system("echo '10' > ./config/frequency_temp")

	try:
		with open("./conf/file_size", 'r') as sizefile:
			size = sizefile.next().strip()
		sizefile.close()
	except:
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

