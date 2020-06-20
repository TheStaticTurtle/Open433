import logging

import serial
from homeassistant.const import EVENT_HOMEASSISTANT_START, EVENT_HOMEASSISTANT_STOP
import homeassistant.helpers.config_validation as cv
import voluptuous as vol
import threading

from homeassistant.exceptions import PlatformNotReady

from . import rcswitch

_LOGGER = logging.getLogger(__name__)

DOMAIN = "open433"

CONF_COMPORT = "port"
CONF_COMSPEED = "speed"

REQ_LOCK = threading.Lock()
CONFIG_SCHEMA = vol.Schema(
	{
		DOMAIN: vol.Schema({
			vol.Required(CONF_COMPORT): cv.string,
			vol.Optional(CONF_COMSPEED, default=9600): cv.positive_int,
		})
	},
	extra=vol.ALLOW_EXTRA,
)



def setup(hass, config):
	conf = config[DOMAIN]
	comport = conf.get(CONF_COMPORT)
	comspeed = conf.get(CONF_COMSPEED)

	failure = None
	try:
		rf = rcswitch.RCSwitch(comport, speed=comspeed)
		rf.libWaitForAck(True, timeout=1)

		def cleanup(event):
			rf.cleanup()

		def packet_listener(packet):
			if isinstance(packet, rcswitch.packets.ReceivedSignal):
				hass.bus.fire("open433_rx", {"code": packet.decimal, "protocol": packet.protocol, "bitlength": packet.length, "delay": packet.delay})

		def handle_event(event):
			code = int(event.data.get("code")) if event.data.get("code") else 2658012672
			protocol = int(event.data.get("protocol")) if event.data.get("protocol") else 1
			bitlength = int(event.data.get("bitlength")) if event.data.get("bitlength") else 32
			packet = rcswitch.packets.SendDecimal(value=code, length=bitlength, protocol=protocol, delay=700)
			rf.send(packet)

		def prepare(event):
			rf.prepare()
			rf.startReceivingThread()
			rf.addIncomingPacketListener(packet_listener)
			hass.bus.listen("open433_tx", handle_event)
			hass.bus.listen_once(EVENT_HOMEASSISTANT_STOP, cleanup)

		hass.bus.listen_once(EVENT_HOMEASSISTANT_START, prepare)
		hass.data[DOMAIN] = rf
		return True

	except serial.serialutil.SerialException as e:
		failure = e

	if failure is not None:
		raise PlatformNotReady(failure)
