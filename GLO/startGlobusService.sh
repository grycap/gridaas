#!/bin/bash

# Create grid proxy using CA 
grid-proxy-init -valid 8760:0 -cert /etc/grid-security/certificates/usercert.crt -key /etc/grid-security/certificates/userkey.pem

# Initialize globus-gatekeeper service
/etc/init.d/globus-gatekeeper start 
