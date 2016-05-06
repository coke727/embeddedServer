#!/bin/sh

ACTUAL=$(pwd)
cd /sys/bus/w1/devices
shopt -s nullglob
set -- 28*

if [ $# -gt 0 ]; then

	sudo apt-get install python-pip python-crypto python-dev libgmp-dev cpufrequtils
	sudo apt-get install build-essential libffi-dev libssl-dev
	sudo pip install python-crontab
	sudo pip install cryptography
	sudo pip install paramiko

	#Download the repository with the code.
	if [ -d $ACTUAL"/embeddedServer"]; then
		echo "Downloading weather station code from Github."
		git clone https://github.com/coke727/embeddedServer.git
	else
		echo "[Warning!] Weather station code already in this directory. I will use the code already in the device, if it is not desirable move the code from this directory and execute this script another time."
	fi

	#Wpa_supplicant setup
	echo "Configuration eduroam network with wpa_supplicant."
	sudo cat $ACTUAL/embeddedServer/wpa_supplicant >> /etc/wpa_supplicant/wpa_supplicant.conf
	sudo wpa_supplicant -Dwext -iwlan0 -c /etc/wpa_supplicant.conf
	sudo dhcpcd wlan0

	#Adding scripts to PATH
	if [ ! -d "/home/"$USER"/bin"]; then
		mkdir ~/bin
	fi

	cp -a $ACTUAL/scripts/mpnormal ~/bin
	cp -a $ACTUAL/scripts/mp1 ~/bin
	cp -a $ACTUAL/scripts/mp2 ~/bin
	cp -a $ACTUAL/scripts/mp3 ~/bin
	chmod 777 ~/bin/*

	#Adding server execution to boot
	if grep -q boot.sh "/etc/profile"; then
		echo "[Warning!] The init weather station script is already in /etc/profile"
	else
		echo "Adding weather station to /etc/profile"
		sudo echo "" >> /etc/profile
		sudo echo -n "sudo python "$ACTUAL"/embeddedServer/boot.sh" >> /etc/profile
		sudo echo -e "\n" >> /etc/profile
 	fi
	
	#Create temporal data dirs.
	echo "Creating temporal data directories."
	mkdir -p $ACTUAL"/embeddedServer/logs" $ACTUAL"/embeddedServer/crons" $ACTUAL"/embeddedServer/config" $ACTUAL"/embeddedServer/data/backup"

	#Checking rtc sensor.
	if [ ! -d "/sys/class/rtc/rtc0"]; then
		echo " [Warning!] There isn't an RTC module installed. Please install the required hardware and restart this script. Otherwise the 3º power mode will be disable."
		echo "Execute setup.sh after install the RTC module for enable 3º power mode." >> ./config/rtc_state
	else
		if [ -f $ACTUAL"/embeddedServer/config/rtc_state"]; then
			rm ./config/rtc_state
		else
			echo "RTC detectado correctamente."
		fi
	fi

	sudo reboot
else
	echo "[Error!] There is no temperature sensor installed in system. Please install the required hardware before continue."
fi