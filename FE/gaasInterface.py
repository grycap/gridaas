# pylint: disable=invalid-name,C0301
import ConfigParser
import getpass
import logging
import os
import subprocess
import sys
import time

# Global variables definition
AUTHFILE_PATH = '/home/ubuntu/GaaS-Scripts/authFile'
# CFG Variables
CFG_PATH = '/home/ubuntu/GaaS-Scripts/GaaS.cfg'
CFG_BACKUP_PATH = '/home/ubuntu/GaaS-Scripts/GaaS.bak'
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

# Config file setup
config = ConfigParser.RawConfigParser()
config.read(CFG_PATH)

# Logging setup
FORMAT = "%(asctime)s - GaaS - %(levelname)s : %(message)s"
logging.basicConfig(filename='gaas.log', level=logging.DEBUG, format=FORMAT)

# Function definitions

def checkAuthFile():
    """Check if IM authentication file exists"""
    return os.path.isfile(AUTHFILE_PATH) or os.path.isfile('./authFile')

def checkGridActive():
    """Check if grid infrastructure is gridactive"""
    return True if int(config.get(CFG_SECT_STATUS, CFG_P_STAT_ACTIVE)) == 1 else False

def backupConfigFile():
    """Method to backup config file"""
    if os.path.isfile(CFG_PATH) and not os.path.isfile(CFG_BACKUP_PATH):
        (stdout, stderr) = subprocess.Popen(['cp', CFG_PATH, CFG_BACKUP_PATH], stdout=subprocess.PIPE, stderr=subprocess.PIPE).communicate()
        if stderr:
            logging.error('Error occurred while backing up config file - ' + stderr)
        else:
            logging.info('Config file backup complete')
    else:
        logging.info('Config file backup incomplete - file not found or backup exists')

def restoreConfigFile():
    """Method to restore config file"""
    if os.path.isfile(CFG_BACKUP_PATH):
        (stdout, stderr) = subprocess.Popen(['cp', CFG_BACKUP_PATH, CFG_PATH], stdout=subprocess.PIPE, stderr=subprocess.PIPE).communicate()
        if stderr:
            logging.error('Error occurred while backing up config file - ' + stderr)
        else:
            logging.info('Config file restored successfully')
    else:
        logging.info('Config file restore incomplete - backup not found')


def injectSSHKey():
    """Function to inject FE SSH Key into nodes recipes"""
    try:
        # Read SSHKey
        with open('/home/ubuntu/.ssh/id_rsa.pub', 'r') as f:
            sshkey = f.read()

        # Process Globus recipe
        # Read GLO Recipe
        with open('/home/ubuntu/GaaS-Scripts/globusNode.radl', 'r') as f:
            globusrecipe = f.read()

        # Replace the target string
        globusrecipe = globusrecipe.replace('FESSHKEY', sshkey)

        # Write the file out again
        with open('/home/ubuntu/GaaS-Scripts/globusNode.radl', 'w') as f:
            f.write(globusrecipe)

        # Process CA recipe
        # Read GLO Recipe
        with open('/home/ubuntu/GaaS-Scripts/nodeCA.radl', 'r') as f:
            globusrecipe = f.read()

        # Replace the target string
        globusrecipe = globusrecipe.replace('FESSHKEY', sshkey)

        # Write the file out again
        with open('/home/ubuntu/GaaS-Scripts/nodeCA.radl', 'w') as f:
            f.write(globusrecipe)
    except IOError as ex:
        logging.error('Error while trying to inject SSH Key - ' + ex.strerror)



def addGlobusNodes(num):
    """Function for add Globus nodes"""
    logging.info('Started routine for add ' + str(num) + ' nodes')
    try:
        # Get some info from Config file
        infId = config.get(CFG_SECT_STATUS, CFG_P_STAT_GLOINF)
        newNodesIndex = len(config.options(CFG_SECT_NODES))

        # Generate temporary recipe for deploy <num> nodes
        # Read GLO Recipe
        with open('/home/ubuntu/GaaS-Scripts/globusNode.radl', 'r') as file:
            globusrecipe = file.read()

        # Replace the target string
        globusrecipe = globusrecipe.replace('@input.NumNodes@', num)

        # Write the file out again
        with open('/home/ubuntu/GaaS-Scripts/globusNodeAdd.radl', 'w') as file:
            file.write(globusrecipe)

        # Launch globus node adder script
        (stdout, stderr) = subprocess.Popen(['im_client.py', '-a', AUTHFILE_PATH, 'addresource', infId, '/home/ubuntu/GaaS-Scripts/globusNodeAdd.radl'], stdout=subprocess.PIPE, stderr=subprocess.PIPE).communicate()
        if stderr:
            logging.error('Error occurred while launching globus node - ' + stderr)
        # Remove temp file
        if os.path.isfile('/home/ubuntu/GaaS-Scripts/globusNodeAdd.radl'):
            os.remove('/home/ubuntu/GaaS-Scripts/globusNodeAdd.radl')

        # Register new nodes on config file
        registerInfAddress(infId)

        # Generate credentials for new nodes
        generateCredentials(num)

        # Sync credentials
        syncCredentials(num, newNodesIndex)

        # Sync hosts file
        syncHostsFile()

        # Request nodes to update its hosts file
        updateHostsGlobus()

        auxCont = newNodesIndex
        while int(auxCont) < (int(newNodesIndex)+int(num)-1):
            # Start services on new globus node
            startOneGlobusServices(auxCont)
            auxCont = auxCont + 1

    except IOError as ex:
        logging.error('Error getting globus recipes - ' + ex.strerror)

    logging.info('Adding nodes routine finished successfully')

def removeGlobusNode(nodeNum):
    """Function for remove Globus nodes"""
    logging.info('Starting routine for removing node: ' + str(nodeNum))

    # Get some info from Config file
    infId = config.get(CFG_SECT_STATUS, CFG_P_STAT_GLOINF)

    # Launch globus node remover script
    (stdout, stderr) = subprocess.Popen(['im_client.py', '-a', AUTHFILE_PATH, 'removeresource', infId, nodeNum], stdout=subprocess.PIPE, stderr=subprocess.PIPE).communicate()
    if stderr:
        logging.error('Error occurred while removing globus node - ' + stderr)

    # Unregister  node on config file
    unregisterNode(nodeNum)

    # Sync hosts file
    syncHostsFile()

    # Request nodes to update its hosts file
    updateHostsGlobus()

    logging.info('End of removing node routine')

def initialDeployment(num):
    """Method for deploy initial Globus nodes and CA node"""
    logging.info('Starting routine for initial deployment of ' + str(num) + ' nodes')

    # Launch globus nodes with IM client
    numArg = subprocess.Popen(['echo', num], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    (stdout, stderr) = subprocess.Popen(['im_client.py', '-a', AUTHFILE_PATH, 'create', '/home/ubuntu/GaaS-Scripts/globusNode.radl'], stdin=numArg.stdout, stdout=subprocess.PIPE, stderr=subprocess.PIPE).communicate()
    newId = stdout.split()[-1]
    if stderr:
        logging.error('Error occurred while launching initial globus nodes - ' + stderr)

    # Register new addresses
    registerInfAddress(newId)

    # Save Globus infrastructure id
    config.set(CFG_SECT_STATUS, CFG_P_STAT_GLOINF, newId)

    saveConfigFile()

    logging.info('Routine for initial deployment finished successfully')

def deleteInfrastructure():
    """Method for delete entire infrastructure"""
    # Clean /etc/hosts file from FE Node
    nodes = config.options(CFG_SECT_NODES)
    for node in nodes:
        removeHost(node)

    # Destroy all deployed nodes
    # Destroy globus nodes
    (stdout, stderr) = subprocess.Popen(['im_client.py', '-a', AUTHFILE_PATH, 'destroy', config.get(CFG_SECT_STATUS, CFG_P_STAT_GLOINF)], stdout=subprocess.PIPE, stderr=subprocess.PIPE).communicate()
    if stderr:
        logging.error('Error occurred while deleting globus nodes - ' + stderr)

    # Destroy CA Node
    (stdout, stderr) = subprocess.Popen(['im_client.py', '-a', AUTHFILE_PATH, 'destroy', config.get(CFG_SECT_STATUS, CFG_P_STAT_CAINF)], stdout=subprocess.PIPE, stderr=subprocess.PIPE).communicate()
    if stderr:
        logging.error('Error occurred while deleting CA node - ' + stderr)

    # Restore config file
    restoreConfigFile()

    logging.info('Infrastructure successfully deleted')

def deployCANode():
    """Method to deploy CA Node"""
    (stdout, stderr) = subprocess.Popen(['im_client.py', '-a', AUTHFILE_PATH, 'create', '/home/ubuntu/GaaS-Scripts/nodeCA.radl'], stdout=subprocess.PIPE, stderr=subprocess.PIPE).communicate()
    newId = stdout.split()[-1]
    if stderr:
        logging.error('Error occurred while launching CA node - ' + stderr)

    registerCANode(newId)
    logging.info('Deployed new CA with id: ' + newId)

    return newId

def generateCredentials(num):
    """Method for request CA Node to create credentials"""
    (stdout, stderr) = subprocess.Popen(['python', 'socketFE-CA.py', num], stdout=subprocess.PIPE, stderr=subprocess.PIPE).communicate()
    if stderr:
        logging.error('Error occurred while generating credentials - ' + stderr)

    logging.info('Credentials generated by CA Node')

def syncCredentials(num, startNode):
    """Method for synchronize credentials with globus nodes"""
    ipCA = config.get(CFG_SECT_CAS, 'nodeca'+config.get(CFG_SECT_STATUS, CFG_P_STAT_CURRENTCA))
    (stdout, stderr) = subprocess.Popen(['sh', 'syncCredentials.sh', num, startNode, ipCA], stdout=subprocess.PIPE, stderr=subprocess.PIPE).communicate()
    if stderr:
        logging.error('Error occurred while node credentials synchronization - ' + stderr)

    logging.info('Credentials synchronized with nodes from ' + startNode + ' to ' + str(int(startNode)+int(num)-1))

def startGlobusServices():
    """Method to request globus nodes to start globus toolkit services"""
    (stdout, stderr) = subprocess.Popen(['python', 'socketFE-GLO.py', 'init'], stdout=subprocess.PIPE, stderr=subprocess.PIPE).communicate()
    if stderr:
        logging.error('Error occurred while sending globus services init message - ' + stderr)

    logging.info('Globus services initialization message sent')

def startOneGlobusServices(num):
    """Method to request globus node to start globus toolkit services"""
    (stdout, stderr) = subprocess.Popen(['python', 'socketFE-GLO.py', 'init', 'nodeGlobus'+num], stdout=subprocess.PIPE, stderr=subprocess.PIPE).communicate()
    if stderr:
        logging.error('Error occurred while sending a globus services init message - ' + stderr)

    logging.info('Globus services initialization message sent')
# Config file functions

def registerInfAddress(infId):
    """Method for register all VMs IPs into Configurarion file"""

    logging.info('VMs IPs info registering routine started')

    # Get info from infrastructure
    (stdout, stderr) = subprocess.Popen(['im_client.py', '-a', AUTHFILE_PATH, 'getinfo', infId], stdout=subprocess.PIPE, stderr=subprocess.PIPE).communicate()
    if stderr:
        logging.error('Error occurred while retrieving vm info for register nodes on cfg - ' + stderr)

    newNodes = {}
    # Process VMs info
    # Split info separating by VMRC
    stdout = stdout.split('\n\n\n')

    # Process each VM info
    for vmInfo in stdout:
        if vmInfo.strip() != '':
            # Get node name
            nodeName = 'nodeGlobus' + str(len(newNodes))
            ips = []

            # Get node IP addresses
            for infoLine in vmInfo.splitlines():
                if infoLine.startswith('net_interface.0.ip') or infoLine.startswith('net_interface.1.ip'):
                    ips.append(infoLine.split()[-2].replace("'", ''))
            if len(ips) > 0:
                newNodes[nodeName] = ips

    # Check existing nodes and add new nodes
    for node in newNodes:
        config.set(CFG_SECT_NODES, node, newNodes[node][0]+'|'+newNodes[node][1])

        # Add new nodes to /etc/hosts file
        addHost(node, newNodes[node][0])

    saveConfigFile()

    logging.info('Routine for register VMs IPs info finished')

def unregisterNode(nodeNum):
    """Method to unregister node from Config file and hosts file"""
    nodeName = 'nodeGlobus'+nodeNum

    # Remove from config file
    config.remove_option(CFG_SECT_NODES, nodeName)

    # Remove from hosts file
    removeHost(nodeName)

    saveConfigFile()

    logging.info('Node ' + nodeName + ' successfully remove')

def registerCANode(infId):
    """Method to register CA Node in Configuration file"""
    logging.info('Started registerCANode method')

    # Set CA node name
    if config.has_section(CFG_SECT_CAS):
        nodeName = 'nodeCA' +  str(len(config.options(CFG_SECT_CAS)))
    else:
        config.add_section(CFG_SECT_CAS)
        nodeName = 'nodeCA0'
    nodeIP = ''

    # Get info from infrastructure
    (stdout, stderr) = subprocess.Popen(['im_client.py', '-a', AUTHFILE_PATH, 'getinfo', infId], stdout=subprocess.PIPE, stderr=subprocess.PIPE).communicate()
    if stderr:
        logging.error('Error occurred while retrieving info for CA registration on cfg - ' + stderr)

    # Get node IP addresses
    for lineStr in stdout.splitlines():
        if lineStr.startswith('net_interface.0.ip'):
            nodeIP = lineStr.split()[-2].replace("'", '')

    config.set(CFG_SECT_CAS, nodeName, nodeIP)
    saveConfigFile()

    logging.info('Registered CA Node '+nodeName+' '+nodeIP)

def saveConfigFile():
    """Method to save current config to config cfg file"""
    try:
        cfgfile = open(CFG_PATH, 'w')
        config.write(cfgfile)
        cfgfile.close()
    except IOError as ex:
        logging.error('Error trying to save config file - ' + ex.strerror)
    else:
        logging.info('Config file saved successfully')
    

# Hosts file functions

def addHost(hostName, hostIP):
    """Method to add host to /etc/hosts file"""
    (stdout, stderr) = subprocess.Popen(['bash', '/home/ubuntu/GaaS-Scripts/manageHosts.sh', 'addhost', hostName, hostIP], stdout=subprocess.PIPE, stderr=subprocess.PIPE).communicate()
    if stderr:
        logging.error('Error occurred while adding host to hosts file - ' + stderr)

    logging.info('Added node host: ' + hostName + ' ' + hostIP)

def removeHost(hostName):
    """Method to remove host from /etc/hosts file"""
    (stdout, stderr) = subprocess.Popen(['bash', '/home/ubuntu/GaaS-Scripts/manageHosts.sh', 'removehost', hostName], stdout=subprocess.PIPE, stderr=subprocess.PIPE).communicate()
    if stderr:
        logging.error('Error occurred while removing host from hosts file - ' + stderr)

    logging.info('Removed host ' + hostName)

def syncHostsFile():
    """Method to synchronize /etc/hosts file on each globus node"""
    logging.info('Started method for sync hosts file with globus nodes')
    # Get node list
    nodes = config.items(CFG_SECT_NODES)

    # Get /etc/hosts info and replace external IP with internal IP
    with open('/etc/hosts', 'r') as fileHosts:
        hostsInfo = fileHosts.read()

    for node in nodes:
        hostsInfo = hostsInfo.replace(node[1].split('|')[0], node[1].split('|')[1])

    # Create internal IPs hosts file
    with open('/home/ubuntu/hosts', 'w') as fileHosts:
        fileHosts.write(hostsInfo)

    # Iterate over nodes and sync internal hosts file
    for node in nodes:
        nodeIp = node[1].split('|')[0]
        (stdout, stderr) = subprocess.Popen(['scp', '/home/ubuntu/hosts', 'ubuntu@' + nodeIp + ':/home/ubuntu'], stdout=subprocess.PIPE, stderr=subprocess.PIPE).communicate()
        if stderr:
            logging.error('Error occurred while synchronizing hosts file - ' + stderr)

    logging.info('Finished method for sync hosts file with globus nodes')

def updateHostsGlobus():
    """Method to request globus nodes to update /etc/hosts files previously sync"""
    (stdout, stderr) = subprocess.Popen(['python', 'socketFE-GLO.py', 'update'], stdout=subprocess.PIPE, stderr=subprocess.PIPE).communicate()
    if stderr:
        logging.error('Error occurred while sending hosts file update message - ' + stderr)

    logging.info('Globus nodes called for update hosts file')

# Interface functions

def clearScreen():
    """Function for clear terminal"""
    os.system('cls' if os.name == 'nt' else 'clear')

def initialCAGuide():
    """Method to guide CA Node Initialization"""
    print '\n\n----------- User required action -----------'
    print 'For initialize CA node, you need to access via web: https://'+config.get(CFG_SECT_CAS, 'nodeCA'+config.get(CFG_SECT_STATUS, CFG_P_STAT_CURRENTCA))+'/pki/ca and follow this steps: \n  1. Login with user "admin" and pass "admin" \n  2. Go to menu "PKI Init & Config" -> "initialization" -> "DB, Key and Cert init" (Next steps are all in this menu) \n  3. First step in CA initialization is "Initialize Database" \n  4. Second step is "Generate new CA secret key" (only press OK and insert pass) \n  5. Third step is "Generate new CA Certificate Request (use generated secret key)". Here you can set a Common Name (Without spaces) for CA and Country code (Leave in blank the other fields, and continue preesing OK and inserting pass again) \n  6. Fourth step is "Self Signed CA Certificate (from altready generated request)" only press OK and enter pass \n  7. Final step is "Rebuild CA Chain". Once you finish this step, CA initialization is finished'
    print '\nWhen you finished initialization type OK: '
    caIsInit = False
    while not caIsInit:
        res = raw_input()
        if res == 'OK':
            caIsInit = True

def createAuthFile():
    """Function for create IM AuthFile"""
    logging.info('Starting method for creating auth file')
    print 'Now select a IaaS provider to deploy VMs: \n  1.OpenNebula\n  2.OpenStack\n  3.Amazon EC2\n  4.Google Compute\n  5.Azure\n  0.Exit without creating AuthFile\n'
    prov = input('Select a IaaS provider: ')

    if prov in [1, 2, 3, 4, 5]:
        # Set common info
        authFile = open('/home/ubuntu/GaaS-Scripts/authFile', 'w+')

        # Set provider info
        if prov == 1:
            host = raw_input('Insert OpenNebula host (<host>:<port>): ')
            user = raw_input('Insert user: ')
            onepass = getpass.getpass('Insert password: ')
            authFile.write('id = one; type = OpenNebula; host = '+host+'; username = '+user+'; password = '+onepass+ os.linesep)
        elif prov == 2:
            host = raw_input('Insert OpenStack host (<host>:<port>): ')
            user = raw_input('Insert user: ')
            ostpass = getpass.getpass('Insert password: ')
            tenant = raw_input('Insert tenant: ')
            authFile.write('id = ost; type = OpenStack; host = '+host+'; username = '+user+'; password = '+ostpass+'; tenant = '+tenant+ os.linesep)
        elif prov == 3:
            accessKey = raw_input('Insert access key: ')
            secretKey = raw_input('Insert secret key: ')
            authFile.write('id = ec2; type = EC2; username = '+accessKey+'; password = '+secretKey+ os.linesep)
        elif prov == 4:
            user = raw_input('Insert user: ')
            gcepass = getpass.getpass('Insert password: ')
            project = raw_input('Insert Google Compute project: ')
            authFile.write('id = gce; type = GCE; username = '+user+'.apps.googleusercontent.com; password = '+gcepass+'; project = '+project + os.linesep)
        else:
            subscription_id = raw_input('Insert user subscription id: ')
            user = raw_input('Insert user (user@domain.com): ')
            azupass = getpass.getpass('Insert password: ')
            authFile.write('id = azure; type = Azure; subscription_id = '+subscription_id+'; username = '+user+'; password = '+azupass + os.linesep)
        authFile.write('id = im; type = InfrastructureManager; username = XXX; password = XXX' + os.linesep)
        authFile.write('id = vmrc; type = VMRC; host = http://servproject.i3m.upv.es:8080/vmrc/vmrc; username = XXX; password = XXX' + os.linesep)
        authFile.close()
        logging.info('Auth file created with provider type: ' + str(prov))
        print '\nAuthFile succesfully created!'
    else:
        print '\nAuthFile not created.'
        logging.info('Authfile ')


def initialization():
    """Method launched when interface starts"""
    print '-----------------------------------'
    print '---- Welcome to GaaS Interface ----'
    print '-----------------------------------'
    sys.stdout.write('\nSetting SSH...')
    injectSSHKey()
    print '\t\tOK'
    sys.stdout.write('\nChecking IM Authentication File...')
    if not checkAuthFile():
        print '\tERROR Authentication File not found. \nProceding to create auth File...'
        createAuthFile()
    else:
        print '\t\tOK'

    # Backup config file
    backupConfigFile()

    # Check CFG sections
    if not config.has_section(CFG_SECT_NODES):
        config.add_section(CFG_SECT_NODES)
    if not config.has_section(CFG_SECT_CAS):
        config.add_section(CFG_SECT_CAS)

    # Check working directory and set if its not correct
    if os.getcwd() != '/home/ubuntu/GaaS-Scripts':
        os.chdir('/home/ubuntu/GaaS-Scripts')

def showMenu():
    """Function for printing menu and get selected option"""
    print '\nMENU:'
    print ' 1. Create/Delete infrastructure'
    print ' 2. Add nodes'
    print ' 3. Remove nodes'
    print ' 4. View grid info'
    print ' 0. Exit'
    return input('Select your option: ')

def showInfoFromVMs():
    """Method for print info about VMs on deployed infrastructure"""
    # Get IM ids for Globus nodes and CA
    infCA = config.get(CFG_SECT_STATUS, CFG_P_STAT_CAINF)
    infGLO = config.get(CFG_SECT_STATUS, CFG_P_STAT_GLOINF)

    print '--- Infrastructure Info ---'

    # Get and print info about CA
    (stdout, stderr) = subprocess.Popen(['im_client.py', '-a', AUTHFILE_PATH, 'getinfo', infCA], stdout=subprocess.PIPE, stderr=subprocess.PIPE).communicate()
    if stderr:
        logging.error('Error while retrieving info about CA - ' + stderr)
    infoCAVm = stdout.splitlines()

    # Process CA VM info
    for lineCA in infoCAVm:
        if lineCA.startswith('net_interface.0.dns_name'):
            CAName = lineCA.split()[-2].replace("'", '')
        if lineCA.startswith('net_interface.0.ip'):
            CAIP = lineCA.split()[-2].replace("'", '')
        if lineCA.startswith('state'):
            CAState = lineCA.split()[-2].replace("'", '')
        if lineCA.startswith('disk.0.os.credentials.username'):
            CAUser = lineCA.split()[-2].replace("'", '')
        if lineCA.startswith('disk.0.os.credentials.password'):
            CAPass = lineCA.split()[-1].replace("'", '')

    # Build CA info string for print
    if CAName and CAIP and CAState and CAUser and CAPass:
        print '\n  -  Node: '+CAName+'\n  -  IP: '+CAIP+'\n  -  State: '+CAState+'\n  -  User: '+CAUser+'\n  -  Pass: '+CAPass

    # Get and print info about Globus nodes
    (stdout, stderr) = subprocess.Popen(['im_client.py', '-a', AUTHFILE_PATH, 'getinfo', infGLO], stdout=subprocess.PIPE, stderr=subprocess.PIPE).communicate()
    if stderr:
        logging.error('Error while retrieving info about Globus nodes - ' + stderr)

    infoGLOVm = stdout.split('\n\n\n')

    # Process each Globus node info
    for nodeVMInfo in infoGLOVm:
        ips = []
        if nodeVMInfo != '':
            for lineGLO in nodeVMInfo.splitlines():
                if lineGLO.startswith('net_interface.0.dns_name'):
                    NodeName = lineGLO.split()[-2].replace("'", '').replace('#N#', str(infoGLOVm.index(nodeVMInfo)))
                if lineGLO.startswith('net_interface.0.ip') or lineGLO.startswith('net_interface.1.ip'):
                    ips.append(lineGLO.split()[-2].replace("'", ''))
                if lineGLO.startswith('state'):
                    NodeState = lineGLO.split()[-2].replace("'", '')
                if lineGLO.startswith('disk.0.os.credentials.username'):
                    NodeUser = lineGLO.split()[-2].replace("'", '')
                if lineGLO.startswith('disk.0.os.credentials.password'):
                    NodePass = lineGLO.split()[-1].replace("'", '')

            # Build Globus node info string for print
            if NodeName and len(ips) > 0 and NodeState and NodeUser and NodePass: 
                print '\n  -  Node: '+NodeName+'\n  -  IP: '+ips[0]+'|'+ips[1]+'\n  -  State: '+NodeState+'\n  -  User: '+NodeUser+'\n  -  Pass: '+NodePass

# Main function
if __name__ == "__main__":

    clearScreen()

    # Initialization
    initialization()

    # Config file Initialization
    config.read(CFG_PATH)

    option = showMenu()

    # Start main loop
    while option != 0:
        if option == 1:
            print '\nLooking for infrastructure state...'
            if checkGridActive():
                deleteOpt = False
                while not deleteOpt:
                    ans = raw_input('Grid is active. Do you want to delete entire infrastructure? (YES/NO): ')
                    if ans in ['YES', 'NO']:
                        deleteOpt = True

                if ans == 'YES':
                    logging.info('Grid infrastructure delete rutine selected')
                    # Launch delete infrastructure Method
                    deleteInfrastructure()

                    config.set(CFG_SECT_STATUS, CFG_P_STAT_ACTIVE, '0')
            else:
                print 'Grid is not active. \nProceding to initialize...'
                globusNum = raw_input('\nHow many globus node you want to deploy?: ')

                logging.info('Proceding to deploy grid infrastructure with '+globusNum+' globus nodes')
                start = time.time()
                # Deploy a new CA and set as default CA
                caInfId = deployCANode()
                config.set(CFG_SECT_STATUS, CFG_P_STAT_CAINF, caInfId)
                config.set(CFG_SECT_STATUS, CFG_P_STAT_CURRENTCA, '0')

                # Initial Globus node deployment
                sys.stdout.write('\nDeploying globus nodes... ')
                initialDeployment(globusNum)
                print '\t\tOK'

                print 'Waiting until CA is deployed (It will take around 15-20 minutes)'
                # Loop for wait CA to be configured
                caIsConfig = False
                while not caIsConfig:
                    (stdout, stderr) = subprocess.Popen(['im_client.py', '-a', AUTHFILE_PATH, 'getstate', caInfId], stdout=subprocess.PIPE, stderr=subprocess.PIPE).communicate()
                    infoCA = stdout.splitlines()
                    if stderr:
                        logging.error('Error occurred while retrieving info for CA Loop - ' + stderr)

                    for line in infoCA:
                        if line.startswith('The') and line.split()[-1] == 'configured':
                            caIsConfig = True

                    # If is not configured, sleep 7 seconds
                    if not caIsConfig:
                        time.sleep(7)

                # CA Node initialization by user
                sys.stdout.write('CA Node is deployed, proceding with CA initialization...')
                initialCAGuide()
                print '\t\tCA Successfully initialized'

                # CA Credentials requesting
                sys.stdout.write('Requesting CA for node credentials...')
                generateCredentials(globusNum)
                print '\t\tOK'

                # Credentials sync with Globus nodes
                sys.stdout.write('Synchronize credentials on Globus nodes... ')
                syncCredentials(globusNum, '0')
                print '\t\tOK'

                # Sync /etc/hosts file to globus nodes
                sys.stdout.write('Synchronize hosts file on Globus nodes... ')
                syncHostsFile()
                print '\t\tOK'

                # Request globus nodes to update their own /etc/hosts file
                sys.stdout.write('Updating hosts files on each node...')
                updateHostsGlobus()
                print '\t\tOK'

                # Send message to Globus nodes for start Globus services
                sys.stdout.write('Starting Globus Toolkit services on Globus nodes... ')
                startGlobusServices()
                print '\t\tOK'

                end = time.time()
                logging.info('Deployment time: '+str(end-start)+' s')

                config.set(CFG_SECT_STATUS, CFG_P_STAT_ACTIVE, '1')
                saveConfigFile()
                print 'Grid infrastructure is deployed. Globus toolkit services are running.'

        elif option == 2:
            sys.stdout.write('\nLooking for infrastructure state...')
            if checkGridActive():
                print '\t\tOK'
                numNodes = raw_input('\nNumber of Globus nodes to add: ')

                print '\nAdding '+numNodes+' new Globus nodes...'
                addGlobusNodes(numNodes)
                print 'New nodes successfully added'
            else:
                print '\t\tERROR'
                print 'Grid infrastructure is not active. Add operation is not possible.'

        elif option == 3:
            sys.stdout.write('\nLooking for infrastructure state...')
            if checkGridActive():
                print '\t\tOK'

                nodeNum = raw_input('\nEnter number of the node to remove: ')

                sys.stdout.write('Proceding to remove node... ')
                removeGlobusNode(nodeNum)
                print '\t\tOK'

            else:
                print '\t\tERROR'
                print 'Grid infrastructure is not active. Remove operation is not possible.'
        elif option == 4:
            showInfoFromVMs()
        else:
            clearScreen()
            print '\nWrong option selected'
        option = showMenu()
    # End of main loop
    print '\nGoodbye!'
