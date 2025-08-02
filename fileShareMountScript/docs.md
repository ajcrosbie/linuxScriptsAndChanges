## What it does
This is a basic script that should add the fileshare from some host on the same network (although it can be from an external one)
This requires a samba host.

## Dependencies
- cifs-utils
- avahi
- nss-mdns


## Setup
### Script Setup
This script does require a .env file with the following structure

SMB_USER= the username of the configured samaba user
SMB_PASS= the password of the configured samba user
SMB_IP = the IP of the samba host (not required unless known to be static)
SMB_SHARE= the foldernae of the shared resource

To resolve the raspberrypi.local we need to update certain config files
`/etc/nsswitch.conf`

replace the line starting with 
`hosts:`
with 
`hosts: files mdns4_minimal [NOTFOUND=return] dns mdns`


### Server Setup 
This is not too horrendous
Initially this was setup on a debian raspberry pi so the [ubuntu](https://ubuntu.com/tutorials/install-and-configure-samba#1-overview) guide wasn't too difficult to use

#


# Encounterd issues 
1. If for whatever reason your client and server (pi) have different sized subent (_._._._/X, _._._._/Y) you are likely to get Destination Host Unreachable when attempting to ping the client. The solution found to this was to simply change the size of the client's subnet with this command: 
`sudo ip addr change _._._._/X dev wlan0`. Will update this if it seems to need to be added to the mount script

2. dynamic ip addresses are annoying here
3. mount error: cifs filesystem not supported by the system. This seems to be caused by part of linux not being properl installed: As such to fix it you need to install linux and linux-headers using the preffered package manager.
