import logging

import voluptuous as vol

from homeassistant.components.switch import SwitchEntity, PLATFORM_SCHEMA
from homeassistant.const import CONF_NAME, CONF_SWITCHES
import homeassistant.helpers.config_validation as cv
from . import DOMAIN, REQ_LOCK, rcswitch

_LOGGER = logging.getLogger(__name__)

CONF_CODE_OFF = "code_off"
CONF_CODE_ON = "code_on"
CONF_PROTOCOL = "protocol"
CONF_LENGTH = "length"
CONF_SIGNAL_REPETITIONS = "signal_repetitions"
CONF_ENABLE_RECEIVE = "enable_receive"

SWITCH_SCHEMA = vol.Schema(
	{
		vol.Required(CONF_CODE_OFF): vol.All(cv.ensure_list_csv, [cv.positive_int]),
		vol.Required(CONF_CODE_ON): vol.All(cv.ensure_list_csv, [cv.positive_int]),
		vol.Optional(CONF_LENGTH, default=32): cv.positive_int,
		vol.Optional(CONF_SIGNAL_REPETITIONS, default=15): cv.positive_int,
		vol.Optional(CONF_PROTOCOL, default=2): cv.positive_int,
		vol.Optional(CONF_ENABLE_RECEIVE, default=False): cv.boolean,
	}
)

PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend(
	{
		vol.Required(CONF_SWITCHES): vol.Schema({cv.string: SWITCH_SCHEMA}),
	}
)


def setup_platform(hass, config, add_entities, discovery_info=None):
	rf = hass.data[DOMAIN]

	switches = config.get(CONF_SWITCHES)
	devices = []
	for dev_name, properties in switches.items():
		devices.append(
			Open433Switch(
				properties.get(CONF_NAME, dev_name),
				rf,
				properties.get(CONF_PROTOCOL),
				properties.get(CONF_LENGTH),
				properties.get(CONF_SIGNAL_REPETITIONS),
				properties.get(CONF_CODE_ON),
				properties.get(CONF_CODE_OFF),
				properties.get(CONF_ENABLE_RECEIVE),
			)
		)

	add_entities(devices)


class Open433Switch(SwitchEntity):
	def __init__(self, name, rf, protocol, length, signal_repetitions, code_on, code_off,enable_rx):
		self._name = name
		self._state = False
		self._rf = rf
		self._protocol = protocol
		self._length = length
		self._code_on = code_on
		self._code_off = code_off
		self._signal_repetitions = signal_repetitions
		if enable_rx:
			self._rf.addIncomingPacketListener(self._incoming)

	def _incoming(self, packet):
		if isinstance(packet, rcswitch.packets.ReceivedSignal):
			if packet.length == self._length and packet.protocol == self._protocol:
				if packet.decimal in self._code_on:
					self._state = True
					self.schedule_update_ha_state()
				if packet.decimal in self._code_off:
					self._state = False
					self.schedule_update_ha_state()

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
		with REQ_LOCK:
			_LOGGER.info("Sending code(s): %s", code_list)
			self._rf.setRepeatTransmit(self._signal_repetitions)
			for code in code_list:
				packet = rcswitch.packets.SendDecimal(value=code, length=length, protocol=protocol, delay=700)
				self._rf.send(packet)
		return True

	def turn_on(self, **kwargs):
		if self._send_code(self._code_on, self._protocol, self._length):
			self._state = True
			self.schedule_update_ha_state()

	def turn_off(self, **kwargs):
		if self._send_code(self._code_off, self._protocol, self._length):
			self._state = False
			self.schedule_update_ha_state()