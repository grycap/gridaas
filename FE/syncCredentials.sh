#!/bin/bash
# Check arguments

if [ "$#" -eq 3 ] 
then
    # Get number of credentials and starting number node
    num=$1
    startNode=$2
    cont=$2
    caIP=$3

    # Sync each credentials to its corresponding node
    while [ $cont -lt $(($startNode+$num)) ] 
    do
        # Set permissions for files and directories on remote node
        ssh ubuntu@nodeGlobus"$cont" 'sudo chown ubuntu.ubuntu -R /etc/grid-security/'
        ssh ubuntu@nodeGlobus"$cont" 'sudo rm /etc/grid-security/hostkey.pem'

        # FE node gets credentials and store in temp folder
        scp root@"$caIP":/home/globusFiles/CA/* /tmp/rsyncFiles
        scp root@"$caIP":/home/globusFiles/nodes/globusNode"$cont"/* /tmp/rsyncFiles
        
        # FE node sync credentials to nodeGlobus
        scp /tmp/rsyncFiles/host* ubuntu@nodeGlobus"$cont":/etc/grid-security/
        rm /tmp/rsyncFiles/host*
        scp /tmp/rsyncFiles/* ubuntu@nodeGlobus"$cont":/etc/grid-security/certificates
        rm /tmp/rsyncFiles/*

        # Add 1 to counter
        cont=$(($cont+1))
    done
else
    echo "Invalid arguments. Usage: command <num credentials> <starting node>"
fi
