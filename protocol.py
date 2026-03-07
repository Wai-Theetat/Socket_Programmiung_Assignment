import socket
import time
import threading
from packet import Packet, FLAG_ACK, FLAG_DATA, FLAG_FIN

# Macro
TIME_OUT = 0.5			# sec before retransmit
MAX_PAYLOAD = 1000		# byte / data chunk
WINDOW_SIZE = 32


#---------- Sender ----------#
def send_file(sock, dest, filename, file_data):
	# Build chunk list
	chunks = [(FLAG_DATA, filename.encode())] 	#convert filename into b"filename"
	offset = 0

	while offset < len(file_data):
		chunk = file_data[offset:offset + MAX_PAYLOAD]
		chunks.append((FLAG_DATA, chunk))
		offset += len(chunk)
	chunks.append((FLAG_FIN,b""))

	total		= len(chunks)			# total number of packets to send
	base		= 0						# oldest unACKed seq
	next_seq	= 0						# next packet allowed to send
	acked		= [False] * total		# whether packet i is ACKed
	send_times	= [0.0] * total			# last send time (used for timeout retransmission)

	lock		= threading.Lock()
	done		= threading.Event()		# thread stop signal

	# Receiver thread : Collecting ACKs
	def ack_receiver():
		nonlocal base
		while not done.is_set():
			try:
				sock.settimeout(0.1)	
				raw, _ = sock.recvfrom(2048)
				pkt = Packet.unpack(raw)
				if not (pkt.flags & FLAG_ACK):
					continue

				seq = pkt.ack - 1
				with lock:
					if 0 <= seq < total:
						acked[seq] = True
					#Slide base
					while base < total and acked[base]:
						base += 1

			except socket.timeout:
				continue

			except Exception:
				break
		
	receiver_thread = threading.Thread(target=ack_receiver, daemon=True)
	receiver_thread.start()

	# Sender Loop: fill window + selective retransmit
	while True:
		with lock:
			current_base = base

		if current_base >= total:
			break		# all packet ACKed

		now = time.time()

		with lock:
			# Send new packet within window
			while next_seq < total and next_seq < current_base + WINDOW_SIZE:
				if not acked[next_seq]:
					flags, data = chunks[next_seq]
					pkt = Packet(seq=next_seq, flags=flags, data=data)
					sock.sendto(pkt.pack(), dest)
					send_times[next_seq] = now
				next_seq += 1
	
			#Selective Retransmit
			for i in range(current_base, min(next_seq, current_base + WINDOW_SIZE)):
				if not acked[i] and (now - send_times[i] > TIME_OUT):
					flags, data = chunks[i]
					pkt = Packet(seq=i, flags=flags, data=data)
					sock.sendto(pkt.pack(), dest)
					send_times[i] = now					# reset timer
     
	done.set()
	receiver_thread.join()
	print(f"Transfer complete: {total} packets sent")


#---------- Reciver ----------#
def recv_file(sock):
	expected_seq	= 0			# next seq
	recv_buffer		= {}		# seq -> Packet
	filename		= None
	chunks			= []
	fin_seq			= None
 
	sock.settimeout(None)
 
	while True:
		raw, addr = sock.recvfrom(MAX_PAYLOAD + 64)
		pkt = Packet.unpack(raw)
		seq = pkt.seq
  
		# Always ACK every valid received packet
		ack = Packet(seq=0, ack=seq + 1, flags=FLAG_ACK)
		sock.sendto(ack.pack(), addr)
  
		# Buffer if in received window
		if seq >= expected_seq and seq not in recv_buffer:
			recv_buffer[seq] = pkt
   
		# Deliver Packet
		while expected_seq in recv_buffer:
			deliver = recv_buffer.pop(expected_seq)

			if deliver.flags & FLAG_FIN:
				fin_seq = expected_seq
				expected_seq += 1
				break

			if deliver.flags & FLAG_DATA:
				if expected_seq == 0:        # seq 0 = filename
					filename = deliver.data.decode()
				else:
					chunks.append(deliver.data)
				expected_seq += 1

		# ── Done when FIN delivered ──
		if fin_seq is not None:
			break

	return filename, b"".join(chunks)