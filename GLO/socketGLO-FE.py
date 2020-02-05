import subprocess

import os
import logging
import zmq

# Global variables
MSG_INIT = 'initialize services'
MSG_UPDATE = 'update hosts'

# Logging setup
FORMAT = "%(asctime)s - %(levelname)s : %(message)s"
logging.basicConfig(filename='socket.log', level=logging.DEBUG, format=FORMAT)

# ZMQ Setup
context = zmq.Context.instance()
socketREP = context.socket(zmq.REP)
socketREP.bind("tcp://*:8112")
logging.info('Socket binded. Starting loop...')

while True:
    # Wait until FE sends a message (init or update)
    message = socketREP.recv()
    logging.info('Message recieved: ' + message)

    # Initialization method
    if message == MSG_INIT:

        #  Create proxy for globus
        (stdout, stderr) = subprocess.Popen(['grid-proxy-init', '-valid', '8760:0', '-cert', '/etc/grid-security/certificates/usercert.pem', '-key', '/etc/grid-security/certificates/userkey.pem', '-out', '/tmp/x509up_u1000'], stdout=subprocess.PIPE, stderr=subprocess.PIPE).communicate()
        if stdout:
            logging.info('Grid-proxy-init out:' + stdout)
        if stderr:
            logging.error('Error occurred while creating globus proxy - ' + stderr)

        # Fix globus-gatekeeper log permissions
        (stdout, stderr) = subprocess.Popen(['sudo', 'chown', 'ubuntu.ubuntu', '/var/log/globus-gatekeeper.log'], stdout=subprocess.PIPE, stderr=subprocess.PIPE).communicate()
        if stderr:
            logging.error('Error occurred while fixing globus-gatekeeper permissions - ' + stderr)


        # Initialize globus-gatekeeper service
        (stdout, stderr) = subprocess.Popen(['/etc/init.d/globus-gatekeeper', 'start'], stdout=subprocess.PIPE, stderr=subprocess.PIPE).communicate()
        if stderr:
            logging.error('Error occurred while starting globus-gatekeeper service - ' + stderr)

        socketREP.send("Globus initialization: OK")
        logging.info('Globus initialized and message replied')
    # Hostnames update method
    elif message == MSG_UPDATE:
        # Update hosts file
        (stdout, stderr) = subprocess.Popen(['bash', '/home/ubuntu/GaaS-Scripts/manageHosts.sh', 'updateHosts'], stdout=subprocess.PIPE, stderr=subprocess.PIPE).communicate()
        if stderr:
            logging.error('Error occurred while executing update hosts script - ' + stderr)

        # Update grid-mapfile file if exists
        if os.path.isfile('/home/grid-mapfile'):
            (stdout, stderr) = subprocess.Popen(['cp', '/home/grid-mapfile', '/etc/grid-security/grid-mapfile'], stdout=subprocess.PIPE, stderr=subprocess.PIPE).communicate()
            if stderr:
                logging.error('Error occurred while copying modded grid-mapfile file - ' + stderr)

        socketREP.send('OK Hosts updated')
        logging.info('Hosts updated and message replied')
    else:
        socketREP.send("ERROR Wrong message")
        logging.error('Wrong message recieved')
 
