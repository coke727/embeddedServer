#!/bin/sh

if [ -d "/sys/bus/w1/devices/28*" ]; then

	#Download the repository with the code.
	echo "Downloading weather station code from Github."
	git clone https://github.com/coke727/embeddedServer.git
	cd embeddedServer

	#Wpa_supplicant setup
	echo "Configuration eduroam network with wpa_supplicant."
	sudo cat wpa_supplicant >> /etc/wpa_supplicant.conf
	sudo wpa_supplicant -Dwext -iwlan0 -c /etc/wpa_supplicant.conf
	sudo dhcpcd wlan0

	#Adding server execution to boot
	if grep -q weatherStation.py "/etc/rc.local"; then
		echo "The weather station is already in /etc/rc.local"
	else
		echo "Adding weather station to /etc/rc.local"
		sudo head -n -1 /etc/rc.local > ./temp.txt 
		sudo mv ./temp.txt /etc/rc.local
		sudo rm ./temp.txt
		sudo echo "" >> /etc/rc.local
		sudo echo -n "sudo python " >> /etc/rc.local
		sudo echo -n $(readlink -f weatherStation.py) >> /etc/rc.local
 	fi
	
	#Create temporal data dirs.
	echo "Creating temporal data directories."
	mkdir -p ./logs ./crons ./config ./data/backup

	if [ ! -d ""]; then
		echo "There isn't an RTC module installed. Please install the required hardware and restart this script. Otherwise the 3º power mode will be deactivated."
	fi

	sudo reboot
else
	echo "There is no temperature sensor installed in system. Please install the required hardware before continue."
fi