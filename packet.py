import struct

HEADER_FORMAT = "!I I B H"
HEADER_SIZE = struct.calcsize(HEADER_FORMAT)

FLAG_SYN = 1
FLAG_ACK = 2
FLAG_FIN = 4
FLAG_DATA = 8


class Packet:
	def __init__(self, seq=0, ack=0, flags=0, data=b""):
		self.seq = seq
		self.ack = ack
		self.flags = flags
		self.data = data

	def pack(self):
		length = len(self.data)
		header = struct.pack(HEADER_FORMAT, self.seq, self.ack, self.flags, length)
		return header + self.data

	@staticmethod
	def unpack(raw):
		if len(raw) < HEADER_SIZE:
			raise ValueError("Packet too small")

		header = raw[:HEADER_SIZE]
		seq, ack, flags, length = struct.unpack(HEADER_FORMAT, header)

		data = raw[HEADER_SIZE:HEADER_SIZE + length]

		return Packet(seq, ack, flags, data)