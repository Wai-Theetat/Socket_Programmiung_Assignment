import socket
from packet import *

SERVER_IP = "127.0.0.1"
SERVER_PORT = 9000

sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
sock.settimeout(2)

print("Sending SYN")

# ---------- STEP 1: Send SYN ----------
syn = Packet(seq=0, flags=FLAG_SYN)
sock.sendto(syn.pack(), (SERVER_IP, SERVER_PORT))

# ---------- STEP 2: Wait SYN-ACK ----------
data, _ = sock.recvfrom(2048)
pkt = Packet.unpack(data)

if pkt and pkt.flags & FLAG_SYN and pkt.flags & FLAG_ACK:

	print("Received SYN-ACK")

	# ---------- STEP 3: Send ACK ----------
	ack_pkt = Packet(
		seq=1,
		ack=pkt.seq + 1,
		flags=FLAG_ACK
	)

	sock.sendto(ack_pkt.pack(), (SERVER_IP, SERVER_PORT))

	print("Connection established")

	# ---------- SEND DATA WITH RETRY ----------
	msg = b"Hello from client"

	data_pkt = Packet(
		seq=1,
		flags=FLAG_DATA,
		data=msg
	)

	while True:

		print("Sending DATA")
		sock.sendto(data_pkt.pack(), (SERVER_IP, SERVER_PORT))

		try:
			data, _ = sock.recvfrom(2048)
			ack = Packet.unpack(data)

			if ack.flags & FLAG_ACK:
				print("ACK received:", ack.ack)
				break

		except socket.timeout:
			print("Timeout! Resending packet...")

else:
	print("Handshake failed")

sock.close()