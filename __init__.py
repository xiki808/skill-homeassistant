from collections import defaultdict

from mycroft.skills.common_iot_skill import CommonIoTSkill,\
    IoTRequest, Thing, Action, Attribute
from mycroft.util.log import getLogger


from .homeassistant.client import HomeAssistantClient


__author__ = 'robconnolly, btotharye, nielstron'
LOGGER = getLogger(__name__)

# Common Strings
_ACTIONS = "actions"
_ATTRIBUTES = "attributes"
_AUTOMATION = "automation"
_BRIGHTNESS = "brightness"
_CLIMATE = "climate"
_DOMAIN = "domain"
_ENTITY_ID = "entity_id"
_HIGH = "target_temp_high"
_LIGHT = "light"
_LOW = "target_temp_low"
_SCRIPT = "script"
_SERVICE = "service"
_STATES = "states"
_SWITCH = "switch"
_TEMPERATURE = "temperature"



_THING_TO_DOMAIN = {
    Thing.LIGHT: _LIGHT,
    Thing.THERMOSTAT: _CLIMATE,
    Thing.TEMPERATURE: _CLIMATE,
    Thing.HEAT: _CLIMATE,
    Thing.AIR_CONDITIONING: _CLIMATE,
    Thing.SWITCH: _SWITCH,
}


_DOMAIN_TO_THING = {v: k for k, v in _THING_TO_DOMAIN.items()}
del(_DOMAIN_TO_THING[_CLIMATE])  # Climate is ambiguous, so we remove it and use _CLIMATE_THINGS instead.

_CLIMATE_THINGS = {
    Thing.TEMPERATURE,
    Thing.THERMOSTAT,
    Thing.HEAT,
    Thing.AIR_CONDITIONING
}

_DOMAINS = {
    _AUTOMATION: {
        _ACTIONS: {
            Action.ON,
            Action.OFF,
            Action.TOGGLE,
            Action.TRIGGER
        },
        _ATTRIBUTES: {

        },
    },
    _CLIMATE: {
        _ACTIONS: {
            Action.ON,
            Action.OFF,
            Action.TOGGLE,
            Action.INCREASE,
            Action.DECREASE,
        },
        _ATTRIBUTES: {

        },
    },
    _LIGHT: {
        _ACTIONS: {
            Action.ON,
            Action.OFF,
            Action.TOGGLE,
            Action.INCREASE,
            Action.DECREASE,
        },
        _ATTRIBUTES: {
            Attribute.BRIGHTNESS,
        },

    },
    _SWITCH: {
        _ACTIONS: {
            Action.ON,
            Action.OFF,
            Action.TOGGLE,
        },
        _ATTRIBUTES: {

        },
    },
    _SCRIPT: {
        _ACTIONS: {
            Action.ON,
            Action.OFF,
            Action.TOGGLE,
            Action.TRIGGER
        },
        _ATTRIBUTES: {

        },
    }
}


_SIMPLE_ACTIONS = {
    Action.TOGGLE: "toggle",
    Action.ON: "turn_on",
    Action.OFF: "turn_off"
}


#TODO Make these settings
_BRIGHTNESS_STEP = 20
_TEMPERATURE_STEP = 2


class HomeAssistantSkill(CommonIoTSkill):

    def __init__(self):
        super().__init__(name="HomeAssistantSkill")
        self._client: HomeAssistantClient = None
        self._entities = dict()

    def initialize(self):
        self.settings.set_changed_callback(self.on_websettings_changed)
        self._setup()
        self._entities = self._build_entities_map(self._client.entities())
        self.register_entities_and_scenes()

    def _build_entities_map(self, entities: dict):
        results = defaultdict(list)
        for id, name in entities.items():
            if name:
                name = name.lower()
            if self._domain(id) in _DOMAINS:
                results[name].append(id)
        return results

    def on_websettings_changed(self):
        # Force a setting refresh after the websettings changed
        # Otherwise new settings will not be regarded
        self._force_setup()

    def _setup(self):
        portnumber = int(self.settings.get('portnum', 8123))
        self._client = HomeAssistantClient(
            token=self.settings.get('token'),
            hostname=self.settings.get('hostname', 'localhost'),
            port=portnumber,
            ssl=self.settings.get('ssl', False),
            verify=self.settings.get('verify', True)
        )

    def _force_setup(self):
        LOGGER.debug('Creating a new HomeAssistant-Client')
        self._setup()

    def _domain(self, entity_id: str):
        if entity_id is None:
            return None
        return entity_id[:entity_id.index('.')]

    def stop(self):
        pass

    def get_entities(self):
        return self._entities.keys()

    def run_request(self, request: IoTRequest, callback_data: dict):
        self._client.run_services(**callback_data)

    def can_handle(self, request: IoTRequest):
        action = request.action
        thing = request.thing
        entity = request.entity
        attribute = request.attribute
        scene = request.scene

        if scene:
            return False, None

        if not thing and not entity:
            return False, None

        if thing and thing not in _THING_TO_DOMAIN:
            return False, None

        entity_id = self._get_entity_id(entity, action, attribute, thing)
        if entity and not entity_id:
            return False, None

        domain = self._domain(entity_id) if entity_id else None
        if domain:
            if domain not in _DOMAINS:
                return False, None

            if not thing:
                thing = _DOMAIN_TO_THING.get(domain)

            if not thing == _DOMAIN_TO_THING.get(domain) and not (domain == _CLIMATE and thing in _CLIMATE_THINGS):
                return False, None

        if thing == Thing.LIGHT:
            return self._can_handle_lights(action, attribute, entity_id)

        if thing == Thing.TEMPERATURE or thing == Thing.THERMOSTAT:
            return self._can_handle_temperature(action, entity_id)

        if thing == Thing.HEAT:
            return self._can_handle_temperature(action, entity_id, _LOW)

        if thing == Thing.AIR_CONDITIONING:
            action = self._invert_action(action)
            return self._can_handle_temperature(action, entity_id, _HIGH)

        if thing == Thing.SWITCH:
            return self._can_handle_simple(action, _SWITCH, entity_id)

        if domain == _AUTOMATION:
            return self._can_handle_automation(action, entity_id)

        if domain == _SCRIPT:
            if action == Action.TRIGGER:
                action = Action.ON
            return self._can_handle_simple(action, _SCRIPT, entity_id)

        return False, None

    def _get_entity_id(self, entity: str, action: Action, attribute: Attribute, thing: Thing):
        possible_ids = self._entities.get(entity)
        if not possible_ids:
            return None

        filtered_entities = []
        for id in possible_ids:
            domain_of_id = self._domain(id)
            if action in _DOMAINS[domain_of_id][_ACTIONS] and \
                    (not attribute or attribute in _DOMAINS[domain_of_id][_ATTRIBUTES]):
                if not thing or domain_of_id == _THING_TO_DOMAIN[thing]:
                    filtered_entities.append(id)

        num_matching_entities = len(filtered_entities)
        if num_matching_entities != 1:
            if num_matching_entities > 1:
                LOGGER.warning("Multiple matching entities! Choosing to "
                               " ignore this request. Entities are: "
                               " {entities}".format(entities=filtered_entities))
            return None
        return filtered_entities[0]

    def _invert_action(self, action):
        # Invert increase/decrease - turn _up_ the AC
        # means turn _down_ the temperature.
        if action == Action.INCREASE:
            action = Action.DECREASE
        elif action == Action.DECREASE:
            action = Action.INCREASE
        return action

    def _can_handle_simple(self, action: Action, domain: str, entity_id: str):
        if action in _SIMPLE_ACTIONS:
            data = {_DOMAIN: domain, _SERVICE: _SIMPLE_ACTIONS[action]}
            states = [dict()]
            if entity_id:
                states[0][_ENTITY_ID] = entity_id
            data[_STATES] = states
            return True, data
        return False, None

    def _can_handle_automation(self, action: Action, entity_id: str):
        if not entity_id:
            return False, None

        service = None
        if action == Action.TRIGGER:
            service = "trigger"
        elif action in _SIMPLE_ACTIONS:
            service = _SIMPLE_ACTIONS[action]

        if service:
            data = {_DOMAIN: _AUTOMATION, _SERVICE: service}
            states = [{_ENTITY_ID: entity_id}]
            data[_STATES] = states
            return True, data

        return False, None

    def _can_handle_lights(self, action: Action, attribute: Attribute, entity_id: str):
        if action in _SIMPLE_ACTIONS:
            return self._can_handle_simple(action, _LIGHT, entity_id)

        states = self._client.get_states(entity_id)

        if not entity_id:
            states = (s for s in states if s[_ENTITY_ID].startswith(_LIGHT))

        if action in {Action.INCREASE, Action.DECREASE} and attribute in {Attribute.BRIGHTNESS, None}:
            states = [s for s in states if _BRIGHTNESS in s[_ATTRIBUTES]]

            if states:
                step = _BRIGHTNESS_STEP if action == Action.INCREASE \
                    else -1 * _BRIGHTNESS_STEP
                states = [{_ENTITY_ID: s[_ENTITY_ID],
                           _BRIGHTNESS: _adjust_brightness(s, step)}
                          for s in states]

                return True, {_DOMAIN : _LIGHT,
                              _SERVICE: "turn_on",
                              _STATES: states}

        return False, None

    def _can_handle_temperature(self, action: Action, entity_id: str, target_key=_TEMPERATURE):
        # TODO handle min/max temp values
        if action in (Action.INCREASE, Action.DECREASE):
            states = self._client.get_states(entity_id)

            if not entity_id:
                states = (s for s in states if s[_ENTITY_ID].startswith(_CLIMATE))

            states = [s for s in states if target_key in s[_ATTRIBUTES]]

            if states:
                step = _TEMPERATURE_STEP if action == Action.INCREASE \
                    else -1 * _TEMPERATURE_STEP

                states = [_adjust_values(s, step, target_key) for s in states]

                return True, {_DOMAIN : _CLIMATE,
                              _SERVICE: "set_temperature",
                              _STATES: states}
        return False, None


def _adjust_brightness(current_state, adjustment):
    value = current_state[_ATTRIBUTES][_BRIGHTNESS] + adjustment
    if value > 254:
        value = 254
    if value < 0:
        value = 0
    return value


def _adjust_values(current_state, adjustment, target_key):
    attributes = current_state[_ATTRIBUTES]

    if target_key == _TEMPERATURE and not attributes.get(_TEMPERATURE):
        data = {_HIGH: attributes[_HIGH] + adjustment, _LOW: attributes[_LOW] + adjustment}
    else:
        data = {target_key: attributes[target_key] + adjustment}

    if target_key == _HIGH and _LOW in attributes:
        data[_LOW] = attributes[_LOW]  # homeassistant gives a 400 if we don't provide both
    if target_key == _LOW and _HIGH in attributes:
        data[_HIGH] = attributes[_HIGH]

    entity_id = current_state[_ENTITY_ID]
    data[_ENTITY_ID] = entity_id
    return data

def create_skill():
    return HomeAssistantSkill()
