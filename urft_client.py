import socket
from packet import Packet, FLAG_SYN, FLAG_ACK

SERVER_IP = "127.0.0.1"
SERVER_PORT = 9000

# Create UDP socket
sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

print("Sending SYN")

## STEP 1: Send SYN to server
# Create SYN packet
syn = Packet(seq=0, flags=FLAG_SYN)

# Send SYN packet to server
sock.sendto(syn.pack(), (SERVER_IP, SERVER_PORT))

# STEP 2: Wait for SYN-ACK from server
data, _ = sock.recvfrom(2048)

# Convert received data into Packet
pkt = Packet.unpack(data)

# If packet failed 
if pkt is None:
	print("Corrupted packet")
	exit()

# Check if packet contains both SYN and ACK flags
if pkt.flags & FLAG_SYN and pkt.flags & FLAG_ACK:
	print("Received SYN-ACK")

	## STEP 3: Send final ACK
 	# Acknowledge server sequence
	ack = Packet(seq=1, ack=pkt.seq + 1, flags=FLAG_ACK)
	
 	# Send ACK to server
	sock.sendto(ack.pack(), (SERVER_IP, SERVER_PORT))

	print("Connection established")

sock.close()