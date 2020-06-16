"""Support for a switch using a 433MHz module via GPIO on a Raspberry Pi."""
import logging
from threading import RLock

import voluptuous as vol

from homeassistant.components.switch import PLATFORM_SCHEMA, SwitchEntity
from homeassistant.const import CONF_NAME, CONF_SWITCHES, EVENT_HOMEASSISTANT_STOP
import homeassistant.helpers.config_validation as cv
from . import rcswitch

_LOGGER = logging.getLogger(__name__)

CONF_COMPORT = "port"

CONF_CODE_OFF = "code_off"
CONF_CODE_ON = "code_on"
CONF_PROTOCOL = "protocol"
CONF_LENGTH = "length"
CONF_SIGNAL_REPETITIONS = "signal_repetitions"

SWITCH_SCHEMA = vol.Schema(
	{
		vol.Required(CONF_CODE_OFF): vol.All(cv.ensure_list_csv, [cv.positive_int]),
		vol.Required(CONF_CODE_ON): vol.All(cv.ensure_list_csv, [cv.positive_int]),
		vol.Optional(CONF_LENGTH, default=32): cv.positive_int,
		vol.Optional(CONF_SIGNAL_REPETITIONS, default=15): cv.positive_int,
		vol.Optional(CONF_PROTOCOL, default=2): cv.positive_int,
	}
)

PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend(
	{
		vol.Required(CONF_COMPORT): cv.string,
		vol.Required(CONF_SWITCHES): vol.Schema({cv.string: SWITCH_SCHEMA}),
	}
)


def setup_platform(hass, config, add_entities, discovery_info=None):
	comport = config.get(CONF_COMPORT)
	mySwitch = rcswitch.RCSwitch(comport,logger=_LOGGER)
	mySwitch.libWaitForAck(True, timeout=0.25)

	mySwitch_lock = RLock()

	switches = config.get(CONF_SWITCHES)

	devices = []
	for dev_name, properties in switches.items():
		devices.append(
			Open433Device(
				properties.get(CONF_NAME, dev_name),
				mySwitch,
				mySwitch_lock,
				properties.get(CONF_PROTOCOL),
				properties.get(CONF_LENGTH),
				properties.get(CONF_SIGNAL_REPETITIONS),
				properties.get(CONF_CODE_ON),
				properties.get(CONF_CODE_OFF),
			)
		)

	add_entities(devices)

	hass.bus.listen_once(EVENT_HOMEASSISTANT_STOP, lambda event: mySwitch.cleanup())




class Open433Device(SwitchEntity):
	def __init__(self, name, mySwitch, lock, protocol, length, signal_repetitions, code_on, code_off):
		"""Initialize the switch."""
		self._name = name
		self._state = False
		self._mySwitch = mySwitch
		self._lock = lock
		self._protocol = protocol
		self._length = length
		self._code_on = code_on
		self._code_off = code_off
		self._signal_repetitions = signal_repetitions

	@property
	def should_poll(self):
		return False

	@property
	def name(self):
		return self._name

	@property
	def is_on(self):
		return self._state

	def _send_code(self, code_list, protocol, length):
		with self._lock:
			_LOGGER.info("Sending code(s): %s", code_list)
			self._mySwitch.setRepeatTransmit(self._signal_repetitions)
			for code in code_list:
				packet = rcswitch.packets.SendDecimal(value=code, length=length, protocol=protocol, delay=700)
				self._mySwitch.send(packet)
		return True

	def turn_on(self, **kwargs):
		"""Turn the switch on."""
		if self._send_code(self._code_on, self._protocol, self._length):
			self._state = True
			self.schedule_update_ha_state()

	def turn_off(self, **kwargs):
		"""Turn the switch off."""
		if self._send_code(self._code_off, self._protocol, self._length):
			self._state = False
			self.schedule_update_ha_state()
