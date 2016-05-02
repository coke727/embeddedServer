#!/bin/sh

if [ -d "/sys/bus/w1/devices/28*" ]; then

	#Download the repository with the code.
	if [ ! -d "./embeddedServer"]; then
		echo "Downloading weather station code from Github."
		git clone https://github.com/coke727/embeddedServer.git
	else
		echo "[Warning!] Weather station code already in this directory. I will use the code already in the device, if it is not desirable move the code from this directory and execute this script another time."
		cd embeddedServer

	#Wpa_supplicant setup
	echo "Configuration eduroam network with wpa_supplicant."
	sudo cat wpa_supplicant >> /etc/wpa_supplicant.conf
	sudo wpa_supplicant -Dwext -iwlan0 -c /etc/wpa_supplicant.conf
	sudo dhcpcd wlan0

	#Adding scripts to PATH
	if [ ! -d "~/bin"]; then
		mkdir ~/bin
	cp -a ./scripts/mpnormal ~/bin
	cp -a ./scripts/mp1 ~/bin
	cp -a ./scripts/mp2 ~/bin
	cp -a ./scripts/mp3 ~/bin

	#Adding server execution to boot
	if grep -q weatherStation.py "/etc/rc.local"; then
		echo "[Warning!] The weather station is already in /etc/rc.local"
	else
		echo "Adding weather station to /etc/rc.local"
		sudo head -n -1 /etc/rc.local > ./temp.txt 
		sudo mv ./temp.txt /etc/rc.local
		sudo rm ./temp.txt
		sudo echo "" >> /etc/rc.local
		sudo echo -n "sudo python " >> /etc/rc.local
		sudo echo -n $(readlink -f weatherStation.py) >> /etc/rc.local
		sudo echo "exit 0" >> /etc/rc.local
 	fi
	
	#Create temporal data dirs.
	echo "Creating temporal data directories."
	mkdir -p ./logs ./crons ./config ./data/backup

	if [ ! -d "/sys/class/rtc/rtc0"]; then
		echo " [Warning!] There isn't an RTC module installed. Please install the required hardware and restart this script. Otherwise the 3º power mode will be disable."
		echo "Execute setup.sh after install the RTC module for enable 3º power mode." >> ./config/rtc_state
	else
		if [ -f "./config/rtc_state"]; then
			rm ./config/rtc_state
		else
			echo "RTC detectado correctamente."
		fi
	fi

	sudo reboot
else
	echo "[Error!] There is no temperature sensor installed in system. Please install the required hardware before continue."
fi