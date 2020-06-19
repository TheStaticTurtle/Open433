"""Support for binary sensor using RPi GPIO."""
import logging
from threading import Timer

import voluptuous as vol

from homeassistant.components.binary_sensor import PLATFORM_SCHEMA, BinarySensorEntity
from homeassistant.const import CONF_NAME, CONF_SWITCHES, DEVICE_DEFAULT_NAME
import homeassistant.helpers.config_validation as cv
from . import DOMAIN, REQ_LOCK, rcswitch

_LOGGER = logging.getLogger(__name__)

CONF_CODE_OFF = "code_off"
CONF_CODE_ON = "code_on"
CONF_PROTOCOL = "protocol"
CONF_LENGTH = "length"
CONF_SIGNAL_REPETITIONS = "signal_repetitions"
CONF_ON_TIMEOUT = "on_timeout"

SWITCH_SCHEMA = vol.Schema(
	{
		vol.Required(CONF_CODE_OFF): vol.All(cv.ensure_list_csv, [cv.positive_int]),
		vol.Required(CONF_CODE_ON): vol.All(cv.ensure_list_csv, [cv.positive_int]),
		vol.Optional(CONF_LENGTH, default=32): cv.positive_int,
		vol.Optional(CONF_SIGNAL_REPETITIONS, default=15): cv.positive_int,
		vol.Optional(CONF_PROTOCOL, default=2): cv.positive_int,
		vol.Optional(CONF_PROTOCOL, default=2): cv.positive_int,
		vol.Optional(CONF_ON_TIMEOUT, default=0): cv.positive_int,
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
			Open433BinarySensor(
				properties.get(CONF_NAME, dev_name),
				rf,
				properties.get(CONF_PROTOCOL),
				properties.get(CONF_LENGTH),
				properties.get(CONF_CODE_ON),
				properties.get(CONF_CODE_OFF),
				properties.get(CONF_ON_TIMEOUT),
			)
		)

	add_entities(devices, True)


class Open433BinarySensor(BinarySensorEntity):
	def __init__(self, name, rf, protocol, length, code_on, code_off, on_timeout):
		self._name = name
		self._state = False
		self._rf = rf
		self._protocol = protocol
		self._length = length
		self._code_on = code_on
		self._code_off = code_off
		self._on_timeout = on_timeout
		self._available = True
		self._rf.addIncomingPacketListener(self._incoming)

		self._rf.addErrorListener(self._rcSwitchError)

	def _rcSwitchError(self, err):
		self._available = False
		self.schedule_update_ha_state()

	def _turn_off(self):
		self._state = False
		self.schedule_update_ha_state()

	def _incoming(self, packet):
		if isinstance(packet, rcswitch.packets.ReceivedSignal):
			if packet.length == self._length and packet.protocol == self._protocol:
				if packet.decimal in self._code_on:
					self._state = True
					self.schedule_update_ha_state()
					if self._on_timeout != 0:
						Timer(self._on_timeout, self._turn_off).start()

				if packet.decimal in self._code_off:
					self._state = False
					self.schedule_update_ha_state()

	@property
	def available(self):
		return self._available

	@property
	def should_poll(self):
		return False

	@property
	def name(self):
		return self._name

	@property
	def is_on(self):
		return self._state

	def update(self):
		pass
