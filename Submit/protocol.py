import socket
import time
import threading
from packet import Packet, FLAG_ACK, FLAG_DATA, FLAG_FIN

# Macro
TIME_OUT        = 0.2       # sec before retransmit
MAX_PAYLOAD     = 1024      # byte / data chunk
WINDOW_SIZE     = 512
MAX_FIN_RETRIES = 10


#---------- Sender ----------#
def send_file(sock, dest, filename, file_data):
	# Build chunk list
	chunks = [(FLAG_DATA, filename.encode())]
	offset = 0

	while offset < len(file_data):
		chunk = file_data[offset:offset + MAX_PAYLOAD]
		chunks.append((FLAG_DATA, chunk))
		offset += len(chunk)
	chunks.append((FLAG_FIN, b""))

	total		= len(chunks)
	base		= 0
	next_seq	= 0
	acked		= [False] * total
	send_times	= [0.0] * total
	fin_seq		= total - 1
	fin_retries	= 0
	fin_acked	= False

	lock		= threading.Lock()
	done		= threading.Event()

	# ACK Receiver Thread
	def ack_receiver():
		nonlocal base, fin_acked
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
					if seq == fin_seq:
						fin_acked = True
					while base < total and acked[base]:
						base += 1

			except socket.timeout:
				continue
			except Exception:
				break

	receiver_thread = threading.Thread(target=ack_receiver, daemon=True)
	receiver_thread.start()

	fin_acked_time = None

	# Sender Main Loop
	while True:
		now = time.time()
		to_send = []

		with lock:
			current_base = base

			# Send new packets within window
			while next_seq < total and next_seq < current_base + WINDOW_SIZE:
				if not acked[next_seq]:
					to_send.append(next_seq)
					send_times[next_seq] = now
				next_seq += 1

			# Selective retransmit
			fresh = set(to_send)
			for i in range(current_base, min(next_seq, current_base + WINDOW_SIZE)):
				if not acked[i] and i not in fresh and (now - send_times[i] > TIME_OUT):
					to_send.append(i)
					send_times[i] = now
					if i == fin_seq:
						fin_retries += 1

		# Guard clauses
		with lock:
			if fin_acked and fin_acked_time is None:
				fin_acked_time = time.time()

			if fin_acked and base >= total:
				print("FIN ACKed - transfer complete.")
				break

			if fin_acked and fin_acked_time is not None and (time.time() - fin_acked_time) > 2.0:
				print("FIN ACKed - transfer complete (residual ACKs lost).")
				break

			if fin_retries >= MAX_FIN_RETRIES:
				print("FIN ACK not received after retries - server likely closed. Exiting.")
				break

		if current_base >= total:
			break

		for i in to_send:
			flags, data = chunks[i]
			pkt = Packet(seq=i, flags=flags, data=data)
			sock.sendto(pkt.pack(), dest)

		time.sleep(0.001)

	done.set()
	receiver_thread.join()
	print(f"Transfer complete: {total} packets sent")


#---------- Receiver ----------#
def recv_file(sock, first_pkt=None):
	expected_seq	= 0
	recv_buffer		= {}
	delivered		= set()
	filename		= None
	chunks			= []
	fin_seq			= None
	addr			= None

	sock.settimeout(None)

	pending = [first_pkt] if first_pkt is not None else []

	# Receiver Main Loop
	while True:
		if pending:
			pkt = pending.pop(0)
			seq = pkt.seq
		else:
			raw, addr = sock.recvfrom(MAX_PAYLOAD + 64)
			pkt = Packet.unpack(raw)
			seq = pkt.seq

			# Always ACK every received packet
			ack = Packet(seq=0, ack=seq + 1, flags=FLAG_ACK)
			sock.sendto(ack.pack(), addr)

		# Buffer only DATA/FIN packets that are in-window and not yet delivered.
		# Reject stray ACKs (e.g. reordered handshake ACK) to prevent corruption.
		if (pkt.flags & (FLAG_DATA | FLAG_FIN)
				and expected_seq <= seq < expected_seq + WINDOW_SIZE * 2
				and seq not in recv_buffer
				and seq not in delivered):
			recv_buffer[seq] = pkt

		# Deliver in-order packets
		while expected_seq in recv_buffer:
			deliver = recv_buffer.pop(expected_seq)
			delivered.add(expected_seq)

			if deliver.flags & FLAG_FIN:
				fin_seq = expected_seq
				expected_seq += 1
				break

			if deliver.flags & FLAG_DATA:
				if expected_seq == 0:
					filename = deliver.data.decode()
				else:
					chunks.append(deliver.data)
				expected_seq += 1

		if fin_seq is not None:
			break

	return filename, b"".join(chunks)