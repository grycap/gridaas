import sys
import logging
import ConfigParser
import zmq

# Global variables
CFG_PATH = '/home/ubuntu/GaaS-Scripts/GaaS.cfg'
CFG_SECT_GENERAL = 'generalConfig'
CFG_SECT_NODES = 'nodes'
CFG_P_GEN_GLOSOCKET = 'globussocket'
CFG_P_GEN_CASOCKET = 'casocket'
MSG_INIT = 'initialize services'
MSG_UPDATE = 'update hosts'

# Logging setup
FORMAT = "%(asctime)s - SocketFE-GLO - %(levelname)s : %(message)s"
logging.basicConfig(filename='socket.log', level=logging.DEBUG, format=FORMAT)

# Config file setup
config = ConfigParser.RawConfigParser()
config.read(CFG_PATH)
CFG_SOCKET_PORT = config.get(CFG_SECT_GENERAL, CFG_P_GEN_GLOSOCKET)

if len(sys.argv) == 2 and str(sys.argv[1]) in ['init', 'update']:

    # Prepare message depending on script argument
    if str(sys.argv[1]) == 'init':
        mes = MSG_INIT
    else:
        mes = MSG_UPDATE

    context = zmq.Context.instance()
    # Create and connect socket
    socketREQ = context.socket(zmq.REQ)

    # Read nodes from config file
    nodesList = config.items(CFG_SECT_NODES)

    for node in nodesList:
        socketREQ.connect("tcp://" + node[1].split('|')[0] + ":" + CFG_SOCKET_PORT)

    # Send messages to Globus nodes
    for node in nodesList:
        socketREQ.send(mes)
        logging.info('Message sent')

        # Recieve reply
        message = socketREQ.recv()
        logging.info('Message recieved. (' + message + ')')

elif len(sys.argv) == 3 and str(sys.argv[1]) == 'init':
    nodeName = sys.argv[2]
    nodeIP = config.get(CFG_SECT_NODES, nodeName).split('|')[0]
    # Set message
    mes = MSG_INIT

    context = zmq.Context.instance()
    # Create and connect socket
    socketREQ = context.socket(zmq.REQ)

    # Connect to node
    socketREQ.connect("tcp://" + nodeIP + ":" + CFG_SOCKET_PORT)
    # Send msg
    socketREQ.send(mes)

    # Recieve reply
    message = socketREQ.recv()
    logging.info('Message recieved. (' + message + ')')

else:
    logging.error('Wrong arguments execution (Arg num:' + str(len(sys.argv)) + ')')
