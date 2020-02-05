
#!/bin/sh

HOSTNAME=$2
IP_ADDRS=$3

function removehost() {
    if [ -n "$(grep $HOSTNAME /etc/hosts)" ]
    then
        echo "$HOSTNAME Found in hosts file, Removing now...";
        sudo sed -i".bak" "/$HOSTNAME/d" /etc/hosts
    else
        echo "$HOSTNAME was not found in hosts file";
    fi
    
}

function addhost() {
    HOSTS_LINE="$IP_ADDRS $HOSTNAME"
    if [ -n "$(grep $HOSTNAME /etc/hosts)" ]
        then
            echo "$HOSTNAME already exists : $(grep $HOSTNAME /etc/hosts)"
        else
            echo "Adding $HOSTNAME to hosts file";
            sudo -- sh -c -e "echo '$HOSTS_LINE' >> /etc/hosts";

            if [ -n "$(grep $HOSTNAME /etc/hosts)" ]
                then
                    echo "$HOSTNAME was added succesfully - $(grep $HOSTNAME /etc/hosts)";
                else
                    echo "Failed to Add $HOSTNAME";
            fi
    fi
}

function updateHosts(){
    if [ -f "/home/ubuntu/hosts" ]
    then
        echo "Updating local hosts file in /etc/hosts";
        sudo -- sh -c -e "cp /home/ubuntu/hosts /etc/hosts";
    else
        echo "Hosts file for update not found"
    fi
}

$@
