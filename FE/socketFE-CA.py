import sys
import logging
import ConfigParser
import zmq


# message syntax: "Credentials request: <credNum>"
# credNum = Number of credentials to create

# Global variables
CFG_PATH = '/home/ubuntu/GaaS-Scripts/GaaS.cfg'
CFG_SECT_GENERAL = 'generalConfig'
CFG_SECT_NODES = 'nodes'
CFG_SECT_CAS = 'cas'
CFG_SECT_STATUS = 'status'
CFG_P_GEN_GLOSOCKET = 'globussocket'
CFG_P_GEN_CASOCKET = 'casocket'
CFG_P_STAT_ACTIVE = 'gridactive'
CFG_P_STAT_GLOINF = 'globusinfid'
CFG_P_STAT_CAINF = 'cainfid'
CFG_P_STAT_CURRENTCA = 'currentca'

# Logging setup
FORMAT = "%(asctime)s - SocketFE-CA - %(levelname)s : %(message)s"
logging.basicConfig(filename='socket.log', level=logging.DEBUG, format=FORMAT)

# Config file setup
config = ConfigParser.RawConfigParser()
config.read(CFG_PATH)
CFG_SOCKET_PORT = config.get(CFG_SECT_GENERAL, CFG_P_GEN_CASOCKET)
CFG_OPENCA_IP = config.get(CFG_SECT_CAS, 'nodeCA'+config.get(CFG_SECT_STATUS, CFG_P_STAT_CURRENTCA))

if len(sys.argv) == 2:

    context = zmq.Context.instance()
    # Create and connect socket
    socketREQ = context.socket(zmq.REQ)
    socketREQ.connect("tcp://"+CFG_OPENCA_IP+":"+CFG_SOCKET_PORT)

    # Send message to CA
    socketREQ.send("Credentials request: " + sys.argv[1])
    logging.info('Message sent to CA')

    # Recieve reply
    message = socketREQ.recv()
    logging.info('Message recieved from CA. (' + message + ')')

else:
    print 'Wrong number of arguments'
    logging.error('Wrong number arguments execution')
