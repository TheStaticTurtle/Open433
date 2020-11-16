import logging

import voluptuous as vol

from homeassistant.components.light import LightEntity, PLATFORM_SCHEMA, SUPPORT_BRIGHTNESS, ATTR_BRIGHTNESS
from homeassistant.const import CONF_NAME, CONF_SWITCHES
import homeassistant.helpers.config_validation as cv
from . import DOMAIN, REQ_LOCK, rcswitch

_LOGGER = logging.getLogger(__name__)

CONF_BRIGHTNESS = "brightness"
CONF_LEVELS = "levels"
CONF_CODE_ON = "code_on"
CONF_CODE = "code"
CONF_PROTOCOL = "protocol"
CONF_LENGTH = "length"
CONF_SIGNAL_REPETITIONS = "signal_repetitions"
CONF_ENABLE_RECEIVE = "enable_receive"
CONF_FORCE_LEVELS = "force_levels"

BRIGHTNESS_STATES = vol.Schema(
	{
		vol.Required(CONF_BRIGHTNESS): cv.positive_int,
		vol.Required(CONF_CODE): vol.All(cv.ensure_list_csv, [cv.positive_int]),
	}
)

SWITCH_SCHEMA = vol.Schema(
	{
		vol.Required(CONF_LEVELS): vol.All(cv.ensure_list, [BRIGHTNESS_STATES]),

		vol.Optional(CONF_CODE_ON): vol.All(cv.ensure_list_csv, [cv.positive_int]),

		vol.Optional(CONF_LENGTH, default=32): cv.positive_int,
		vol.Optional(CONF_SIGNAL_REPETITIONS, default=15): cv.positive_int,
		vol.Optional(CONF_PROTOCOL, default=2): cv.positive_int,
		vol.Optional(CONF_ENABLE_RECEIVE, default=False): cv.boolean,
		vol.Optional(CONF_FORCE_LEVELS, default=False): cv.boolean,

	}
)

PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend(
	{
		vol.Required(CONF_SWITCHES): vol.Schema({cv.string: SWITCH_SCHEMA}),
	}
)


def fill_array(arr):
	setArrayTpo = None
	for i in range(0, len(arr)):
		if arr[i] != setArrayTpo and arr[i] is not None:
			setArrayTpo = arr[i]
		arr[i] = setArrayTpo
	return arr


def setup_platform(hass, config, add_entities, discovery_info=None):
	rf = hass.data[DOMAIN]

	switches = config.get(CONF_SWITCHES)
	devices = []
	for dev_name, properties in switches.items():

		levels_raw = properties.get(CONF_LEVELS)
		levels = [None] * 101

		for l in levels_raw:
			bright = l.popitem(0)[1]
			if bright < 0 or bright > 100:
				raise ValueError("Brightness value is invalid 0<" + str(bright) + "<100")

			levels[bright] = l.popitem(1)[1]

		levels = fill_array(levels)
		if None in levels:
			raise KeyError("Failed to create brightness map, may you don't have a brigthness 0 entry")

		devices.append(
			Open433Light(
				properties.get(CONF_NAME, dev_name),
				rf,
				properties.get(CONF_PROTOCOL),
				properties.get(CONF_LENGTH),
				properties.get(CONF_SIGNAL_REPETITIONS),
				levels,
				properties.get(CONF_CODE_ON),
				properties.get(CONF_ENABLE_RECEIVE),
				properties.get(CONF_FORCE_LEVELS),
			)
		)

	add_entities(devices)


class Open433Light(LightEntity):
	def __init__(self, name, rf, protocol, length, signal_repetitions, levels, code_on, enable_rx, force_levels):
		self._name = name
		self._brightness = 0
		self._rf = rf
		self._protocol = protocol
		self._length = length
		self._levels = levels
		self._code_on = code_on

		self._signal_repetitions = signal_repetitions
		self._available = True
		if enable_rx:
			self._rf.addIncomingPacketListener(self._incoming)

		self._rf.addErrorListener(self._rcSwitchError)
		self._force_levels = force_levels

	def _rcSwitchError(self, err):
		self._available = False
		self.schedule_update_ha_state()

	def _searchForCode(self, code):
		for i, level in enumerate(self._levels):
			if code in level:
				return i, code
		return None

	def _incoming(self, packet):
		if isinstance(packet, rcswitch.packets.ReceivedSignal):
			if packet.length == self._length and packet.protocol == self._protocol:
				x, _ = self._searchForCode(packet.decimal)
				if x is not None:
					self._brightness = x
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
	def supported_features(self):
		"""Flag supported features."""
		return SUPPORT_BRIGHTNESS

	@property
	def brightness(self):
		return int(self._brightness / 100 * 255)

	@property
	def is_on(self):
		return self._brightness > 0

	def turn_on(self, **kwargs) -> None:
		b = 100
		if ATTR_BRIGHTNESS in kwargs:
			b = int((kwargs[ATTR_BRIGHTNESS] / 255) * 100)

		b = max(min(b, 100), 0)

		codes_to_send = self._levels[b]

		if self._force_levels:
			b, _ = self._searchForCode(codes_to_send[0]) # Not great but works

		if self._code_on is not None:
			codes_to_send = self._code_on + codes_to_send

		if self._send_code(codes_to_send, self._protocol, self._length):
			self._brightness = b

		self.schedule_update_ha_state()

	def turn_off(self, **kwargs) -> None:
		codes_to_send = self._levels[0]
		if self._send_code(codes_to_send, self._protocol, self._length):
			self._brightness = 0
		self.schedule_update_ha_state()

	def _send_code(self, code_list, protocol, length):
		with REQ_LOCK:
			self._rf.setRepeatTransmit(self._signal_repetitions)
			for code in code_list:
				packet = rcswitch.packets.SendDecimal(value=code, length=length, protocol=protocol, delay=700)
				self._rf.send(packet)
		return True
