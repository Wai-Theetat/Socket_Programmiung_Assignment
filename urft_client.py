import socket
import sys
import os
from packet import *
from protocol import *

# Macro
TIME_OUT = 2	# seconds for handshake retries
MAX_SYN_SENT = 10


# 3-Ways Handshake Return true if success.
def handshake(sock, server_addr):
	syn = Packet(seq=0, flags=FLAG_SYN)
	raw = syn.pack()

	for _ in range(MAX_SYN_SENT):
		print("Sending SYN...")
		sock.sendto(raw, server_addr)
		sock.settimeout(TIME_OUT)
		try:
			data, _ = sock.recvfrom(2400)
			pkt = Packet.unpack(data)
			if pkt.flags & FLAG_SYN and pkt.flags & FLAG_ACK:
				print("Received SYN-ACK")
				ack = Packet(seq=1, ack=pkt.seq + 1, flags=FLAG_ACK)
				sock.sendto(ack.pack(), server_addr)
				print("Connection established")
				return True
		except socket.timeout:
			print("Timeout waiting for SYN-ACK, retrying...")
 	
	return False



def main():
	if len(sys.argv) != 4:
		print(f"Error : Invalid argument number.")
		sys.exit(1)

	#-------- File Prep --------#
	file_path = sys.argv[1]
	server_ip = sys.argv[2]
	server_port = int(sys.argv[3])
	server_addr = (server_ip, server_port)

	if not os.path.basename(file_path):
		print(f"Error : file '{file_path}' not found.")

	with open(file_path, "rb") as f:
		file_data = f.read()

	filename = os.path.basename(file_path)

	#-------- Start --------#
	sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
	try:
		if not handshake(sock, server_addr):
			print("Handshake Failed")
			sys.exit(1)
		print(f"Sending file '{filename}' ({len(file_data)} bytes)...")
		send_file(sock, server_addr, filename, file_data)
		print("File sent successfully")

	finally:
		sock.close()



if __name__ == "__main__" :
	main()