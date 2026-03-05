mini TCP

Structure:		Size(Byte)
	SEQ			4
	ACK			4
	FLAGS		1
	DATA		2

| seq | ack | flags | length | data |

! = Network Byte Order (Big Endian)
ตัวอย่าง: ค่า 1,200,000 (ในรูปแบบ_hex_ คือ 0x00124F80) จะถูกส่งในลำดับ 0x00 0x12 0x4F 0x80 บนเครือข่าย

Pack
Unpack

3-Way Handshake
SYN
SYN-ACK
ACK

Client
send SYN
wait SYN-ACK
validate
send ACK
connection established

Server
wait SYN
send SYN-ACK
wait ACK
connection established