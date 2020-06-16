# import open433
import logging
import time

logging.basicConfig(level=logging.INFO, format='[%(asctime)s] [%(levelname)8s] %(name)10s - %(message)s')

import rcswitch

mySwitch = rcswitch.RCSwitch("COM3")
time.sleep(2)

# for packet in mySwitch.listen():
# 	print(packet)

packet_on  = rcswitch.packets.SendDecimal(value=2523794944, length=32, protocol=2, delay=700)
packet_off = rcswitch.packets.SendDecimal(value=2658012672, length=32, protocol=2, delay=700)

mySwitch.setRepeatTransmit(5)

t=1
while True:
	mySwitch.send(packet_on)
	mySwitch.receive_packet(timeout=0.1) #Would be great to receive an ACK
	time.sleep(t)

	mySwitch.send(packet_off)
	mySwitch.receive_packet(timeout=0.1) #Would be great to receive an ACK
	time.sleep(t)
