import open433
import logging
import time

logging.basicConfig(level=logging.INFO, format='[%(asctime)s] [%(levelname)8s] %(name)10s - %(message)s')

rf = open433.boardv1("COM31")
rf.connect()
rf.setMode(open433.boardv1._MODE_ILDE)
rf.setRetryCount(4) # Normally 10 at more that 30 module don't respond in time

# for packet in rf.monitor(advanced=False):
# 	print packet

packet_on  = open433.SimplePacket(value=2473463296,bitlenght=32,protocol=2)
packet_off = open433.SimplePacket(value=2741898752,bitlenght=32,protocol=2)

t=0.5
rf.setMode(open433.boardv1._MODE_TRANSMITTER)
while True:
	rf.send(packet_on)
	time.sleep(t)
	rf.send(packet_off)
	time.sleep(t)