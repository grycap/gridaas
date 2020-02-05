#!/bin/bash
line='--------------------------------------------------------'


# Loop for print interface
echo -e "$line \n Welcome to GaaS deployment interface! \n $line"

while true 
do
    echo -e "Select one option: \n  1. Deploy GaaS IM docker container \n  2. Connect to FE node interface \n  0. Exit"
    read inputAns

    # Exit option
    if [ $((inputAns)) -eq 0] 
    then
        break 
    fi

    # Deploy IM option
    if [ $((inputAns)) -eq 1] 
    then
        # Check if ssh key exists and create one if not exists
        if [ ! -f "$HOME/.ssh/id_rsa.pub" ]
        then
            ssh-keygen -q -N "" -f "$HOME/.ssh/id_rsa"
        fi

        # Deploy docker containers
        sudo docker run -d -p 8899:8899 -p 8800:8800 -v "$HOME/.ssh/id_rsa.pub:/home/im/id_rsa.pub" --name im grycap/im
        sudo docker run -d -p 80:80 --name im-web --link im:im grycap/im-web
    fi



done

