import time
import serial
import logging
import struct

root_logger = logging.getLogger(__name__)


def zero_cut(raw):
	if type(raw) != str:
		raw = raw.decode("utf-8")
	try:
		return raw[:raw.index('\x00')]
	except ValueError:
		return raw

def getPacketType(raw):
	if raw == "timeout":
		return raw
	fmt = "16s"
	size = struct.calcsize(fmt)
	data = struct.unpack(fmt, raw[:size])
	return zero_cut(data[0].decode("utf-8"))

class packets(object):
	def __init__(self):
		super(packets, self).__init__()
		self.ReceiveTypes = [self.ReceivedSignal, self.ReceivedAck]
		self.SendTypes = [self.SendDecimal, self.SendConfig]

	class ReceivedSignal(object):
		"""docstring for received_signal_packet_t"""

		def __init__(self):
			super(packets.ReceivedSignal, self).__init__()
			self.format = "<17sIIHHH"

			self.time = -1
			self.decimal = -1
			self.length = -1
			self.delay = -1
			# self.raw     = None
			self.protocol = 0

		def __str__(self):
			return "<ReceivedSignal time=" + str(self.time) + " decimal=" + str(
				self.decimal) + " length=" + str(
				self.length) + " delay=" + str(self.delay) + " protocol=" + str(self.protocol) + ">"

		def parse(self, raw):
			unpacked = struct.unpack(self.format, bytearray(raw))
			self.time = unpacked[1]
			self.decimal = unpacked[2]
			self.length = unpacked[3]
			self.delay = unpacked[4]
			self.protocol = unpacked[5]
			return self

	class ReceivedAck(object):
		"""docstring for received_signal_packet_t"""

		def __init__(self):
			super(packets.ReceivedAck, self).__init__()
			self.format = "<17sI32s"

			self.time = -1
			self.msg = ""

		def __str__(self):
			return "<ReceivedSignal time=" + str(self.time) + " msg=\"" + self.msg + "\">"

		def parse(self, raw):
			unpacked = struct.unpack(self.format, bytearray(raw))
			self.time = unpacked[1]
			self.msg = unpacked[2].decode("utf-8")
			return self

	class SendDecimal(object):
		"""This packet is used to send a decimal code over the air"""

		def __init__(self, value, length, delay, protocol):
			super(packets.SendDecimal, self).__init__()
			self.format = "<16sIHHH"

			self.value = value
			self.length = length
			self.delay = delay
			self.protocol = protocol

		def __str__(self):
			return "<SendDecimal value=" + str(self.value) + " length=" + str(self.length) + " delay=" + str(
				self.delay) + " protocol=" + str(self.protocol) + "> "

		def pack(self):
			packed = struct.pack(
				self.format,
				b"send_decimal",
				self.value,
				self.length,
				self.delay,
				self.protocol
			)
			return packed

	class SendConfig(object):
		"""This packet is used to send a decimal code over the air"""

		def __init__(self, signal_reapeat, receive_tolerance=60):
			super(packets.SendConfig, self).__init__()
			self.format = "<16sHH"

			self.signal_reapeat = signal_reapeat
			self.receive_tolerance = receive_tolerance

		def __str__(self):
			return "<SendConfig signal_reapeat=" + str(self.signal_reapeat) + " receive_tolerance=" + str(
				self.receive_tolerance) + "> "

		def pack(self):
			packed = struct.pack(
				self.format,
				b"rcswitch_conf",
				self.signal_reapeat,
				self.receive_tolerance,
			)
			return packed




class RCSwitch(object):
	"""docstring for RCSwitch"""

	def __init__(self, port, logger=root_logger):
		super(RCSwitch, self).__init__()
		self.logger = logger
		self.signal_repeat = 3
		self.receive_tolerance = 60
		self.com_port = port
		self._shouldWaitForAck = False
		self._timeout = 0.1
		self.serial = serial.Serial(self.com_port, 9600, timeout=0.1, xonxoff=False, rtscts=False)

	def serial_sync(self, sync_word, timeout: float = -1, should_print_timeout_error=True):
		tstart = time.time()
		buf = bytes()
		while buf[-len(sync_word):] != bytes(sync_word.encode("ascii")):
			buf += bytes(self.serial.read())
			if timeout != -1 and (tstart + timeout < time.time()):
				if should_print_timeout_error:
					self.logger.error("Timeout while reading start sync")
				return "timeout"
		self.serial.read(2)

	def serial_sync_end(self, sync_word, timeout: float = -1, should_print_timeout_error=True):
		time_start = time.time()
		buf = bytes()
		while buf[-len(sync_word):] != bytes(sync_word.encode("ascii")):
			buf += bytes(self.serial.read())
			if timeout != -1 and (time_start + timeout < time.time()):
				if should_print_timeout_error:
					self.logger.error("Timeout while reading end sync")
				return "timeout"
		return buf[:-len(sync_word)]

	def receive_packet(self, timeout: float = -1):
		time_start = time.time()
		while (timeout == -1) or (time_start + timeout > time.time()):
			self.serial_sync("START", timeout=timeout, should_print_timeout_error=False)
			raw = self.serial_sync_end("END", timeout=timeout, should_print_timeout_error=False)
			packet_type = getPacketType(raw)
			if packet_type == "receive_signal":
				self.logger.info("Received packet " + str(packet_type))
				return packets.ReceivedSignal().parse(raw)
			if packet_type == "ack":
				self.logger.info("Received ACK message")
				return packets.ReceivedAck().parse(raw)
		return None

	def listen(self, timeout=-1):
		return self._listen(self, timeout=timeout)

	class _listen:
		def __init__(self, parent, timeout=-1):
			self.parent = parent
			self.timeout = timeout
			self.closed = False

		def __iter__(self):
			return self

		def next(self):
			return self.__next__()

		def __next__(self):
			time_start = time.time()
			while True:
				if self.closed or (self.timeout != -1 and (time_start + self.timeout < time.time())):
					raise StopIteration

				data = self.parent.receive_packet(timeout=0.5 if self.timeout == -1 else self.timeout)
				if data is None:
					return data

	def libWaitForAck(self, shouldwait, timeout=0.1):
		self._shouldWaitForAck = shouldwait
		self._timeout = timeout

	def setRepeatTransmit(self, repeat):
		if self.signal_repeat == repeat:
			# No need it's the same
			return
		self.signal_repeat = max(repeat, 1)
		self.send(packets.SendConfig(self.signal_repeat, self.receive_tolerance))
		if self._shouldWaitForAck:
			while True:
				p = self.receive_packet(timeout=self._timeout)
				if p is None:
					return False
				if isinstance(p, packets.ReceivedAck):
					return True
		else:
			return True

	def setReceiveTolerance(self, tol):
		if self.receive_tolerance == tol:
			# No need it's the same
			return
		self.receive_tolerance = min(max(tol, 0), 100)
		self.send(packets.SendConfig(self.signal_repeat, self.receive_tolerance))
		if self._shouldWaitForAck:
			while True:
				p = self.receive_packet(timeout=self._timeout)
				if p is None:
					return False
				if isinstance(p, packets.ReceivedAck):
					return True
		else:
			return True

	def send(self, packet):
		if type(packet) in packets().SendTypes:
			self.serial.write(b"START\r\n")
			self.serial.write(packet.pack())
			self.serial.write(b"END\r\n")
			logging.info("Sending packet: " + str(packet))
			if self._shouldWaitForAck:
				while True:
					p = self.receive_packet(timeout=self._timeout)
					if p is None:
						return False
					if isinstance(p, packets.ReceivedAck):
						return True
			else:
				return True
		else:
			self.logger.error("Passed packet can't be sent " + str(type(packet)))
			raise ValueError("Passed packet can't be sent " + str(type(packet)))

	def cleanup(self):
		self.serial.close()
