#!/bin/sh

#install dependencies
apt update

apt install python3 python3-pip -y
pip3 install pysensors elevate

mkdir -p /root/IPMI-Controller
cp ./IPMI-Controller.py /root/IPMI-Controller
cp ./IPMI-config.ini /root/IPMI-Controller

cp ./ipmi-controller.service /lib/systemd/system
systemctl enable ipmi-controller
systemctl start ipmi-controller

service ipmi-controller status | cat

echo "Install Successful."