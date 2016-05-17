#!/bin/sh

ACTUAL=$(pwd)

sudo apt-get update
sudo apt-get install git
sudo apt-get install python-pip python-crypto python-dev libgmp-dev cpufrequtils
sudo apt-get install build-essential libffi-dev libssl-dev
sudo pip install python-crontab
sudo pip install cryptography
sudo pip install paramiko

#Download project
echo "Downloading weather station code from Github."
sudo git clone https://github.com/coke727/weatherStation.git

#Creating power saving modes script folder
mkdir /home/$USER/bin
cp -a $ACTUAL/weatherStation/scripts/pmnormal /home/$USER/bin
cp -a $ACTUAL/weatherStation/scripts/pm1 /home/$USER/bin
cp -a $ACTUAL/weatherStation/scripts/pm2 /home/$USER/bin
cp -a $ACTUAL/weatherStation/scripts/pm3 /home/$USER/bin
chmod 777 /home/$USER/bin/*

#Adding server execution to boot
if grep -q boot.sh "/etc/profile"; then
	echo "[Warning!] The init weather station script is already in /etc/profile"
else
	echo "Adding weather station to /etc/profile"
	sudo echo "" >> /etc/profile
	sudo echo -n "sh "$ACTUAL"/weatherStation/scripts/boot.sh" >> /etc/profile
	sudo echo -e "\n" >> /etc/profile
	fi

#Create temporal data dirs.
echo "Creating temporal data directories."
sudo mkdir -p $ACTUAL"/weatherStation/logs" $ACTUAL"/weatherStation/config" $ACTUAL"/weatherStation/data/backup"

sudo reboot
