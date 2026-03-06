import socket
import sys
from packet import *
from protocol import *

#Macro
TIMEOUT = 5   # seconds to wait for ACK completing handshake

def handshake(sock):
	"""
	Wait for a SYN, respond with SYN-ACK wait for ACK.
	Returns client address, or None on failure.
	"""
	while True:
		print("Waiting for connection...")
		sock.settimeout(None)
		data, addr = sock.recvfrom(2048)
		pkt = Packet.unpack(data)

		if not (pkt.flags & FLAG_SYN):
			continue

		print(f"Received SYN from {addr}")

		synack = Packet(seq=0, ack=pkt.seq + 1, flags=FLAG_SYN | FLAG_ACK)
		sock.sendto(synack.pack(), addr)

		# Wait for ACK
		sock.settimeout(TIMEOUT)
		try:
			data, addr2 = sock.recvfrom(2048)
			pkt = Packet.unpack(data)
			if pkt.flags & FLAG_ACK and pkt.ack == synack.seq + 1:
				print(f"Connection established with {addr}")
				return addr
		
		except socket.timeout:
			print("Timeout waiting for ACK, retrying handshake...")
			continue



def	main():
	if len(sys.argv) != 3:
		print(f"Error : Invalid argument number.")
		sys.exit(1)

	server_ip = sys.argv[1]
	server_port = int(sys.argv[2])

	#-------- Start --------#
	sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
	sock.bind((server_ip, server_port))
	print(f"Server listening on {server_ip}:{server_port}")

	try:
		handshake(sock)

		print("Receiving file...")
		filename, file_data = recv_file(sock)

		if filename:
			with open(filename, "wb") as f:
				f.write(file_data)
			print(f"File '{filename}' saved ({len(file_data)} bytes)")
		else:
			print("Error: no filename received")
			sys.exit(1)

	finally:
		sock.close()


if __name__ == "__main__":
	main()