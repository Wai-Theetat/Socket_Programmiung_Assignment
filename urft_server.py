import socket
from packet import Packet, FLAG_SYN, FLAG_ACK

server_ip = "0.0.0.0"
server_port = 9000

# Create UDP socket
sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

# Bind the socket to the IP and port
sock.bind((server_ip, server_port))

print("Server listening...")


## STEP 1: Wait for client to send SYN
# Receive packet from client
data, addr = sock.recvfrom(2048)	#max bytes to receive

# Convert raw bytes into Packet object
pkt = Packet.unpack(data)

# Check if packet exists and contains SYN flag
if pkt and pkt.flags & FLAG_SYN:
	print("Received SYN")


## STEP 2: Send SYN + ACK back to client
# Create SYN-ACK packet
# seq = server sequence number
# ack = client seq + 1 (acknowledging client SYN)
synack = Packet(seq=0, ack=pkt.seq + 1, flags=FLAG_SYN | FLAG_ACK)

# Send SYN-ACK packet to the client address
sock.sendto(synack.pack(), addr)


## STEP 3: Wait for final ACK from client
data, addr = sock.recvfrom(2048)

# Unpack received packet
pkt = Packet.unpack(data)

# Verify this is an ACK packet
if pkt and pkt.flags & FLAG_ACK:
	if pkt.ack == 1:
		print("Connection established")