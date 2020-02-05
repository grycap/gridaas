#!/bin/bash
# Create credentials folders
mkdir /home/globusFiles
mkdir /home/globusFiles/CA
mkdir /home/globusFiles/nodes


# Get certificate subject data and split in lines
str=$(openssl x509 -in /opt/openca/var/openca/crypto/chain/cacert.crt -noout -subject | tr '/' $'\n')
hash=$(openssl x509 -hash -noout < /opt/openca/var/openca/crypto/cacerts/cacert.txt)
C=""
O=""
for line in $str
do
    # Get first argument of each line and process it
    p1=$(echo $line | cut -d '=' -f1)
    if [ $p1 != "subject" ]
    then
        p2=$(echo $line | cut -d '=' -f2)
        case $p1 in
            "C") C=$p2;;
            "O") O=$p2;;
        esac 
    fi
done
# Create signing_policy file
echo "access_id_CA   X509   '/C=$C/O=$O/CN=MasterCPD CA'" >> /home/globusFiles/CA/"$hash".signing_policy
echo "pos_rights     globus CA:sign" >> /home/globusFiles/CA/"$hash".signing_policy
echo "cond_subjects  globus '"/C=$C/O=$O/*"'" >> /home/globusFiles/CA/"$hash".signing_policy

# Copy CA cert file to credentials directory
cp /opt/openca/var/openca/crypto/chain/"$hash".0 /home/globusFiles/CA/"$hash".0

# Prepare openssl config file
echo "#################################################################" >> /opt/openca/etc/openca/openssl/openssl.cnf
echo "[ user_cert ]" >> /opt/openca/etc/openca/openssl/openssl.cnf
echo "basicConstraints=CA:FALSE" >> /opt/openca/etc/openca/openssl/openssl.cnf
echo "nsCertType = client, email" >> /opt/openca/etc/openca/openssl/openssl.cnf
echo "keyUsage = nonRepudiation, digitalSignature, keyEncipherment" >> /opt/openca/etc/openca/openssl/openssl.cnf
echo 'nsComment		= "OpenCA User Certificate"' >> /opt/openca/etc/openca/openssl/openssl.cnf
echo "subjectKeyIdentifier=hash" >> /opt/openca/etc/openca/openssl/openssl.cnf
echo "authorityKeyIdentifier=keyid,issuer:always" >> /opt/openca/etc/openca/openssl/openssl.cnf
echo "issuerAltName=issuer:copy" >> /opt/openca/etc/openca/openssl/openssl.cnf
echo "nsCaRevocationUrl	= https://www.openca.org/cgi-bin/getcrl" >> /opt/openca/etc/openca/openssl/openssl.cnf
echo "nsRevocationUrl	= https://www.openca.org/cgi-bin/getcrl" >> /opt/openca/etc/openca/openssl/openssl.cnf
echo "nsRenewalUrl		= https://www.openca.org:4443/renewal" >> /opt/openca/etc/openca/openssl/openssl.cnf

sed -ie 's/subjectAltName/#subjectAltName/' /opt/openca/etc/openca/openssl/openssl.cnf

# Copy openssl config files to credentials directory
cp /opt/openca/etc/openca/openssl/openssl.cnf /home/globusFiles/CA/globus-host-ssl.conf."$hash"
cp /opt/openca/etc/openca/openssl/openssl.cnf /home/globusFiles/CA/globus-user-ssl.conf."$hash"

# Create grid-security file in credentials directory
echo "#################################################################" >> /home/globusFiles/CA/grid-security.conf."$hash"
echo "#" >> /home/globusFiles/CA/grid-security.conf."$hash"
echo "# File: grid-security.conf" >> /home/globusFiles/CA/grid-security.conf."$hash"
echo "#" >> /home/globusFiles/CA/grid-security.conf."$hash"
echo "# Purpose: This file contains the configuration information" >> /home/globusFiles/CA/grid-security.conf."$hash"
echo "#          for the Grid Security Infrastructure" >> /home/globusFiles/CA/grid-security.conf."$hash"
echo "#" >> /home/globusFiles/CA/grid-security.conf."$hash"
echo "#################################################################" >> /home/globusFiles/CA/grid-security.conf."$hash"
echo "" >> /home/globusFiles/CA/grid-security.conf."$hash"
echo "# These values are set by globus-setup" >> /home/globusFiles/CA/grid-security.conf."$hash"
echo '_domain=`${bindir}/globus-domainname`' >> /home/globusFiles/CA/grid-security.conf."$hash"
echo 'SETUP_GSI_HOST_BASE_DN=" o=MasterCPD, C=ES"' >> /home/globusFiles/CA/grid-security.conf."$hash"
echo 'SETUP_GSI_USER_BASE_DN="ou=${_domain}, o=MasterCPD, C=ES"' >> /home/globusFiles/CA/grid-security.conf."$hash"
echo 'SETUP_GSI_CA_NAME="MasterCPD CA"' >> /home/globusFiles/CA/grid-security.conf."$hash"
echo 'SETUP_GSI_CA_EMAIL_ADDR="jesus@example.es"' >> /home/globusFiles/CA/grid-security.conf."$hash"
echo "" >> /home/globusFiles/CA/grid-security.conf."$hash"
echo '_domain=`${bindir}/globus-domainname`' >> /home/globusFiles/CA/grid-security.conf."$hash"
echo 'DEFAULT_GSI_HOST_BASE_DN=" o=MasterCPD, C=ES"' >> /home/globusFiles/CA/grid-security.conf."$hash"
echo 'DEFAULT_GSI_USER_BASE_DN="ou=${_domain}, o=MasterCPD, C=ES"' >> /home/globusFiles/CA/grid-security.conf."$hash"
echo 'DEFAULT_GSI_CA_NAME="MasterCPD CA"' >> /home/globusFiles/CA/grid-security.conf."$hash"
echo 'DEFAULT_GSI_CA_EMAIL_ADDR="jesus@example.es"' >> /home/globusFiles/CA/grid-security.conf."$hash"
echo "" >> /home/globusFiles/CA/grid-security.conf."$hash"
echo "# Distinguish Name (DN) of the Host" >> /home/globusFiles/CA/grid-security.conf."$hash"
echo 'GSI_HOST_BASE_DN="${SETUP_GSI_HOST_BASE_DN:-${DEFAULT_GSI_HOST_BASE_DN}}"' >> /home/globusFiles/CA/grid-security.conf."$hash"
echo "" >> /home/globusFiles/CA/grid-security.conf."$hash"
echo "# Distinguish Name (DN) of the User" >> /home/globusFiles/CA/grid-security.conf."$hash"
echo 'GSI_USER_BASE_DN="${SETUP_GSI_USER_BASE_DN:-${DEFAULT_GSI_USER_BASE_DN}}"' >> /home/globusFiles/CA/grid-security.conf."$hash"
echo "" >> /home/globusFiles/CA/grid-security.conf."$hash"
echo "# CA Name for the organization" >> /home/globusFiles/CA/grid-security.conf."$hash"
echo 'GSI_CA_NAME="${SETUP_GSI_CA_NAME:-${DEFAULT_GSI_CA_NAME}}"' >> /home/globusFiles/CA/grid-security.conf."$hash"
echo "" >> /home/globusFiles/CA/grid-security.conf."$hash"
echo "# CA Email address for the organization" >> /home/globusFiles/CA/grid-security.conf."$hash"
echo 'GSI_CA_EMAIL_ADDR="${SETUP_GSI_CA_EMAIL_ADDR:-${DEFAULT_GSI_CA_EMAIL_ADDR}}"' >> /home/globusFiles/CA/grid-security.conf."$hash"
echo "" >> /home/globusFiles/CA/grid-security.conf."$hash"
echo "export GSI_HOST_BASE_DN" >> /home/globusFiles/CA/grid-security.conf."$hash"
echo "export GSI_USER_BASE_DN" >> /home/globusFiles/CA/grid-security.conf."$hash"
echo "export GSI_CA_NAME" >> /home/globusFiles/CA/grid-security.conf."$hash"
echo "export GSI_CA_EMAIL_ADDR" >> /home/globusFiles/CA/grid-security.conf."$hash"
echo "" >> /home/globusFiles/CA/grid-security.conf."$hash"
