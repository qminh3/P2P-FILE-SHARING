## P2P File Sharing 
#### an implementation of the peer-to-peer file sharing done with python 3.6

to run the scripts: 
first run the tracker script with "sh tracker.sh"
then up to 8 different instances (peers) of the directory can be created 
paste 1 file into each of the peers' shared directories
finally from each of those peer directories the following command can be executed to share the files between all peers
commmad: sh peer.sh <ip of tracker machine> <port number of tracker as in port.txt> <MIN_TIME_ALIVE in seconds> 
please note that every file must have a different filename
