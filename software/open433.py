# encoding: utf8
import time
import serial
import logging

logger = logging.getLogger(__name__)

# c_handler = logging.StreamHandler()
# c_handler.setLevel(logging.DEBUG)
# c_handler.setFormatter(logging.Formatter('[%(asctime)s] [%(levelname)s\t] %(name)s - %(message)s'))

# logger.addHandler(c_handler)

class SimplePacket(object):
	"""docstring for SimplePacket"""
	def __init__(self, value=0, bitlenght=0, protocol=-1):
		super(SimplePacket, self).__init__()
		self.value = value
		self.bitlenght = bitlenght
		self.protocol = protocol
		self.valid = True if value != 0 else False
	
	def __str__(self):
		out  = "" if self.valid else "[INVALID]"
		out += "Value:"+str(self.value)+" "
		out += "BitLength:"+str(self.bitlenght)+" "
		out += "Protocol:"+str(self.protocol)+" "
		return out

class boardv1(object):
	_CMD_HELLO             = 'H'
	_CMD_CHANGE_MODE       = 'M'
	_CMD_CHANGE_CONFIG     = 'C'

	_CMD_CONFIG_RETRYS     = 'R'

	_CMD_TX_START          = 'T'
	_CMD_COMMAND_END       = '\n'

	_RESPONSE_SUCESS       = 'S'
	_RESPONSE_FAIL         = 'F'
	_RESPONSE_ACK          = 'A'

	_MODE_ILDE             = '0'
	_MODE_MONITOR_SIMPLE   = '1'
	_MODE_MONITOR_ADVANCED = '2'
	_MODE_TRANSMITTER      = '3'

	def __init__(self, PORT, debug=True):
		super(boardv1, self).__init__()
		self.debug = debug
		self.com_port = PORT
		self.serial = None
	
	def serialtools_waitfordata(self):
		text = ""
		while text == "":
			text = self.serial.readline()
		return text

	def connect(self):
		self.serial = serial.Serial(self.com_port,9600, timeout=2, xonxoff=False, rtscts=False)
		self.serialtools_waitfordata() #Waits for the arduino to boot

		self.serial.write(self._CMD_HELLO)
		self.serial.write(self._CMD_COMMAND_END)
		line = self.serial.readline()[:-1]
		if line == None or line=="":
			logger.error("Module didn\'t respond to hello")
		else:
			logger.info("Module connected. (Version "+line.split(" ")[1]+")")

	def readAck(self):
		line = self.serial.readline()[:-1]
		if line == None or line=="":
			logger.error("Module failed to respond")
		else:
			if self._RESPONSE_ACK in line:
				logger.debug("Got ACK")
			else:
				logger.warn("Board returned womething else than ack: "+line)
		return line

	def sendCommand(self, command, args=[]):
		self.serial.write(command)
		for arg in args:
			self.serial.write(arg)
		self.serial.write(self._CMD_COMMAND_END)
		logger.debug("Sending: "+command+" "+' '.join(args)+" ")
		return self.readAck() != ""

	def setRetryCount(self,retrycount):
		if self.sendCommand(self._CMD_CHANGE_CONFIG,args=[self._CMD_CONFIG_RETRYS,str(retrycount)]):
			logger.info("Retry count set to: "+str(retrycount))

	def setMode(self,mode):
		if self.sendCommand(self._CMD_CHANGE_MODE,args=[mode]):
			logger.info("Mode set to: "+str(mode))

	def send(self, packet):
		if type(packet) == SimplePacket:
			self.serial.write(self._CMD_TX_START)
			self.serial.write(self._MODE_MONITOR_SIMPLE)
			self.serial.write("_"+str(packet.value)+"_"+str(packet.bitlenght)+"_"+str(packet.protocol))
			self.serial.write(self._CMD_COMMAND_END)
			ack = self.readAck()
			if ack !="":
				if self._RESPONSE_SUCESS in ack:
					logger.info("Sent packet is a success")
					return True
				else:
					logger.info("Failed to send packet")
					return True

		else:
			logger.error("Packet type is not supporte ("+str(type(packet))+")")
			logger.error("Supported types ares: "+str([SimplePacket]))

	def monitor(self, advanced=True):
		return self._monitor(self, advanced=advanced)
	class _monitor():
		def __init__(self,parent, advanced=True):
			self.advanced = advanced
			self.parent = parent
			self.closed = False

		def __iter__(self): 
			self.parent.setMode(self.parent._MODE_MONITOR_ADVANCED if self.advanced else self.parent._MODE_MONITOR_SIMPLE)
			return self

		def next(self):
			while True:
				if self.closed: 
					raise StopIteration 
				data = self.parent.serialtools_waitfordata().split("x")
				if( len(data) == 3):
					return SimplePacket(value=int(data[0]),bitlenght=int(data[1]),protocol=int(data[2]))
				else:
					logger.error("Board returned wrong rf value")
					logger.debug(data)