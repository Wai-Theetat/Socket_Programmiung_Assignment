import socket
import sys
from packet import *
from protocol import *

#Macro
TIMEOUT = 5   # seconds to wait for ACK completing handshake

def handshake(sock):
	"""
	Wait for a SYN, respond with SYN-ACK, wait for ACK.
	Also accepts a DATA packet as implicit proof the handshake succeeded,
	returning both the client address and the buffered packet.
	Returns (client_addr, first_data_pkt_or_None).
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

		# Wait for ACK — also accept DATA as implicit handshake confirmation
		sock.settimeout(TIMEOUT)
		try:
			while True:
				data, addr2 = sock.recvfrom(2048)
				pkt = Packet.unpack(data)

				# Proper ACK completion
				if pkt.flags & FLAG_ACK and pkt.ack == synack.seq + 1:
					print(f"Connection established with {addr}")
					return addr, None

				# Client already moved to data transfer — handshake succeeded
				if pkt.flags & FLAG_DATA and addr2 == addr:
					print(f"Connection established with {addr}")
					return addr, pkt

				# Re-SYN from same client: resend SYN-ACK
				if pkt.flags & FLAG_SYN and addr2 == addr:
					sock.sendto(synack.pack(), addr)

		except socket.timeout:
			print("Timeout waiting for ACK, retrying handshake...")
			continue



def main():
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
		addr, first_pkt = handshake(sock)

		print("Receiving file...")
		filename, file_data = recv_file(sock, first_pkt)

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
	sys.exit(0)