import subprocess
import os
import logging
import zmq

# Functions definition
def getNextNewNodeCredentials():
    if os.path.isdir("/home/globusFiles/nodes/"):
        os.chdir("/home/globusFiles/nodes/")
        # Get all nodes credentials directories
        nodes_dirs = [d for d in os.listdir(".") if os.path.isdir(d)]

        # Get last node dir name and return its number
        nodes_dirs.sort()

        return str(int(nodes_dirs[len(nodes_dirs)-1][-1]) + 1)
    else:
        return str(0)

# Logging setup
FORMAT = "%(asctime)s - %(levelname)s : %(message)s"
logging.basicConfig(filename='socket.log', level=logging.DEBUG, format=FORMAT)

# ZMQ Setup
context = zmq.Context.instance()
socketREP = context.socket(zmq.REP)
socketREP.bind("tcp://*:8111")
logging.info('Socket binded. Starting loop...')

while True:
    # Wait until FE sends a message
    # message syntax: "Credentials request: <credNum>"
    # credNum = Number of credentials to create
    message = socketREP.recv()
    logging.info('Message recieved: ' + message)
    message = message.split()
    if len(message) == 3 and message[2] >= 1:
        credNum = message[2]
        initNum = getNextNewNodeCredentials()

        # Generate credentials
        (stdout, stderr) = subprocess.Popen(['sh', '/home/GaaS-Scripts/createNodeCredentials.sh', credNum, initNum]).communicate()
        if stderr:
            logging.error('Error occurred while creating credentials - ' + stderr)

        socketREP.send("Credentials creation: OK")
        logging.info('Credentials created and reply sent')

    else:
        socketREP.send("Credentials creation: ERROR Wrong arguments")
        logging.error('Wrong arguments in message')
