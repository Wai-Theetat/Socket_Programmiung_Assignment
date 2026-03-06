import socket
from packet import *

server_ip = "0.0.0.0"
server_port = 9000

sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
sock.bind((server_ip, server_port))

print("Server listening...")

while True:

	print("Waiting for connection...")

	# ---------- HANDSHAKE ----------
	data, addr = sock.recvfrom(2048)
	pkt = Packet.unpack(data)

	if not (pkt.flags & FLAG_SYN):
		continue

	print("Received SYN")

	synack = Packet(
		seq=0,
		ack=pkt.seq + 1,
		flags=FLAG_SYN | FLAG_ACK
	)

	sock.sendto(synack.pack(), addr)

	data, addr = sock.recvfrom(2048)
	pkt = Packet.unpack(data)

	if not (pkt.flags & FLAG_ACK):
		continue

	print("Connection established")

	# ---------- DATA LOOP ----------
	while True:

		data, addr = sock.recvfrom(2048)
		pkt = Packet.unpack(data)

		if pkt.flags & FLAG_DATA:

			print("Received DATA:", pkt.data)

			ack = Packet(
				seq=0,
				ack=pkt.seq + 1,
				flags=FLAG_ACK
			)

			sock.sendto(ack.pack(), addr)
			break