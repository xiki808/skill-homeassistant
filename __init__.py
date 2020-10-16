from collections import defaultdict

from mycroft.skills.common_iot_skill import CommonIoTSkill,\
    IoTRequest, IoTRequestVersion, Thing, Action, Attribute, State
from mycroft.skills.core import FallbackSkill
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
_DEVICE_TRACKER = "device_tracker"
_ENTITY_ID = "entity_id"
_HIGH = "target_temp_high"
_LIGHT = "light"
_LOW = "target_temp_low"
_SCENE = "scene"
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
            Action.INFORMATION_QUERY,
        },
        _ATTRIBUTES: {
            Attribute.TEMPERATURE,
        },
    },
    _DEVICE_TRACKER: {
        _ACTIONS: {
            Action.LOCATE,
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
    _SCENE: {
        _ACTIONS: {
            Action.ON,
        },
        _ATTRIBUTES: {

        },
    },
    _SWITCH: {
        _ACTIONS: {
            Action.ON,
            Action.OFF,
            Action.TOGGLE,
            Action.BINARY_QUERY
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


_MAX_BRIGHTNESS = 254


class HomeAssistantSkill(CommonIoTSkill, FallbackSkill):

    def __init__(self):
        super().__init__(name="HomeAssistantSkill")
        self._client: HomeAssistantClient = None
        self._entities = dict()
        self._scenes = dict()

    def initialize(self):
        self.settings_change_callback = self.on_websettings_changed
        self.on_websettings_changed()
        # TODO: If a user toggles this setting off, it will not de-register 
        # the fallback. Should be moved to on_websettings_changed()
        # Needs higher priority than general fallback skills
        if self.settings.get('enable_fallback'):
            self.register_fallback(self.handle_fallback, 2)

    def on_websettings_changed(self):
        # Force a setting refresh after the websettings changed
        # Otherwise new settings will not be regarded
        self._brightness_step = self.settings.get("brightness_step")
        self._temperature_step = self.settings.get("temperature_step")
        self._create_client()

    def _create_client(self):
        """Create the Home Assistant Client from Skill settings.
        
        :param None
        :return None
        """
        host = self.settings.get('host')
        token = self.settings.get('token')
        if not host: 
            # Assume settings haven't been entered.
            return
        if not token:
            # Ensure access token exists if other settings have been entered
            self.speak_dialog('error.no.token')
            return
        try:
            # Ensure port number is an integer. Default value assumed.
            port_number = int(self.settings.get('portnum'))
        except TypeError:
            self.speak_dialog('error.parsing.number',
                              {'port_number': port_number})
            return

        try:
            self._client = HomeAssistantClient(
                token=token,
                hostname=host,
                port=port_number,
                ssl=self.settings.get('ssl'),
                verify=self.settings.get('verify')
            )
        except ConnectionError:
            self.speak_dialog('error.connection')

        self._entities = self._build_entities_map(self._client.entities())
        self._scenes = self._build_scenes_map(self._client.entities())
        self.register_entities_and_scenes()

    def _build_entities_map(self, entities: dict):
        results = defaultdict(list)
        for id, name in entities.items():
            if name:
                name = name.lower()
            domain = self._domain(id)
            if domain in _DOMAINS and domain != _SCENE:
                results[name].append(id)
        return results

    def _build_scenes_map(self, entities: dict):
        results = dict()
        for id, name in entities.items():
            if not name:
                continue
            name = name.lower()
            if self._domain(id) == _SCENE:
                results[name] = id
        return results

    def _domain(self, entity_id: str):
        if entity_id is None:
            return None
        return entity_id[:entity_id.index('.')]

    def stop(self):
        pass

    @property
    def supported_request_version(self) -> IoTRequestVersion:
        return IoTRequestVersion.V3

    def get_entities(self):
        return self._entities.keys()

    def get_scenes(self):
        return self._scenes.keys()

    def run_request(self, request: IoTRequest, callback_data: dict):
        if request.action == Action.BINARY_QUERY:
            self._run_binary_state_query(request, callback_data)
        elif request.action == Action.INFORMATION_QUERY:
            dialog = callback_data['dialog']
            del(callback_data['dialog'])
            self.speak_dialog(dialog, callback_data)
        elif request.action == Action.LOCATE:
            self._locate(callback_data['entity_id'])
        else:
            self._client.run_services(**callback_data)

    def _locate(self, entity_id: str):
        state = self._client.get_states(entity_id)[0]
        name = state['attributes']['friendly_name']
        location = state['state'].split(' - ')[-1]  # location format is: 'username device_id - zone'
        self.speak_dialog("entity.location", {"entity": name, "location": location})

    def _run_binary_state_query(self, request: IoTRequest, callback_data: dict):
        """
        Currently supports POWERED/UNPOWERED queries
        """
        device_state = self._client.get_states(callback_data['entity_id'])[0]
        friendly_name = device_state['attributes']['friendly_name']
        status = device_state['state']
        queried_state = State[callback_data['state']]

        if status == "unavailable":
            self.speak_dialog("entity.unavailable", {"name": friendly_name})

        elif ((queried_state == State.POWERED and status == "on")
                or (queried_state == State.UNPOWERED and status == "off")):
            self.speak_dialog('affirmative.state',{'friendly_name': friendly_name, 'state': status})

        elif ((queried_state == State.POWERED and status == "off")
                or (queried_state == State.UNPOWERED and status == "on")):
            self.speak_dialog('negative.state', {'friendly_name': friendly_name, 'state': status})

        else:
            raise Exception("Unsupported state query! Queried state was"
                            " {queried_state}. Device state was {device_state}"
                            .format(queried_state=queried_state,
                                    device_state=device_state))

    def can_handle(self, request: IoTRequest):
        action = request.action
        thing = request.thing
        entity = request.entity
        attribute = request.attribute
        scene = request.scene
        value = request.value
        state = request.state

        if scene:
            return self._can_handle_scene(scene, action, thing, entity, attribute)

        if not thing and not entity:
            return False, None

        if thing and (thing not in _THING_TO_DOMAIN
                or _THING_TO_DOMAIN[thing] not in self._client.domains()):
            return False, None

        entity_id = self._get_entity_id(entity, action, attribute, thing)
        if entity and not entity_id:
            return False, None

        domain = self._domain(entity_id) if entity_id else None
        if domain:
            if domain not in _DOMAINS or domain not in self._client.domains():
                return False, None

            if not thing:
                thing = _DOMAIN_TO_THING.get(domain)

            if not thing == _DOMAIN_TO_THING.get(domain) and not (domain == _CLIMATE and thing in _CLIMATE_THINGS):
                return False, None

        if value and thing not in {Thing.LIGHT} | _CLIMATE_THINGS:  # Only lights and heat/ac can handle a value
            return False, None

        if thing == Thing.LIGHT:
            return self._can_handle_lights(action, attribute, entity_id, value=value)

        if thing == Thing.TEMPERATURE or thing == Thing.THERMOSTAT:
            return self._can_handle_temperature(action, entity_id, value=value, attribute=attribute)

        if thing == Thing.HEAT:
            return self._can_handle_temperature(action, entity_id, attribute=attribute, target_key=_LOW, value=value)

        if thing == Thing.AIR_CONDITIONING:
            action = self._invert_action(action)
            return self._can_handle_temperature(action, entity_id, attribute=attribute, target_key=_HIGH, value=value)

        if thing == Thing.SWITCH:
            return self._can_handle_switch(action, entity_id, state)

        if action == Action.LOCATE and domain == _DEVICE_TRACKER:
            return True, {'entity_id': entity_id}

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

    def _can_handle_switch(self, action, entity_id, state):
        if action in _SIMPLE_ACTIONS:
            return self._can_handle_simple(action, _SWITCH, entity_id)
        if action in [Action.BINARY_QUERY] and state in [State.POWERED, State.UNPOWERED]:
            return True, {'entity_id': entity_id, 'state': state.name}
        return False, None

    def _can_handle_scene(self, scene, action, thing, entity, attribute):
        if thing or entity or attribute:
            return False, None
        if action not in _DOMAINS[_SCENE][_ACTIONS]:
            return False, None
        if scene not in self._scenes:
            return False, None
        return self._can_handle_simple(action, _SCENE, self._scenes[scene])

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

    def _can_handle_lights(self, action: Action, attribute: Attribute, entity_id: str, value=None):
        if action in _SIMPLE_ACTIONS:
            return self._can_handle_simple(action, _LIGHT, entity_id)

        states = self._client.get_states(entity_id)

        if not entity_id:
            states = (s for s in states if s[_ENTITY_ID].startswith(_LIGHT))

        if (action in {Action.INCREASE, Action.DECREASE}
                or (action == Action.SET and value)
                and attribute in {Attribute.BRIGHTNESS, None}):
            states = [s for s in states if _BRIGHTNESS in s[_ATTRIBUTES]]

            if not states:
                return False, None

            if action == Action.SET:
                states = [{_ENTITY_ID: s[_ENTITY_ID],
                           _BRIGHTNESS: _get_value_from_percent(value, _MAX_BRIGHTNESS)}
                          for s in states]
            else:
                step = self._brightness_step if action == Action.INCREASE \
                    else -1 * self._brightness_step
                states = [{_ENTITY_ID: s[_ENTITY_ID],
                           _BRIGHTNESS: _adjust_brightness(s, step)}
                          for s in states]

            return True, {_DOMAIN : _LIGHT,
                          _SERVICE: "turn_on",
                          _STATES: states}

        if action == Action.BINARY_QUERY:
            return True, None

        return False, None

    def _can_handle_temperature(self, action: Action, entity_id: str, attribute: Attribute, target_key=_TEMPERATURE, value=None):
        # TODO handle min/max temp values
        if (
                action not in (Action.INCREASE, Action.DECREASE)
                and not (action == Action.SET and value)
                and not (action == Action.INFORMATION_QUERY
                         and attribute == Attribute.TEMPERATURE
                         and target_key == _TEMPERATURE)
        ):
            return False, None

        states = self._client.get_states(entity_id)

        if not entity_id:
            states = (s for s in states if s[_ENTITY_ID].startswith(_CLIMATE))

        states = [s for s in states if target_key in s[_ATTRIBUTES]]

        if not states:
            return False, None

        if action == Action.INFORMATION_QUERY:
            if len(states) != 1:
                return False, None
            current_temperature = states[0]['attributes'].get('current_temperature')
            if not current_temperature:
                return False, None
            return True, {'dialog': 'temperature.query.response',
                          'friendly_name': states[0]['attributes']['friendly_name'],
                          'temperature': current_temperature}

        if action == Action.SET:
            if not value:
                return False, None
            states = [self._set_temperature(s, value, target_key) for s in states]
        else:
            step = self._temperature_step if action == Action.INCREASE \
                else -1 * self._temperature_step

            states = [_adjust_temperature(s, step, target_key) for s in states]

        return True, {_DOMAIN : _CLIMATE,
                      _SERVICE: "set_temperature",
                      _STATES: states}

    def _set_temperature(self, current_state, value, target_key):
        attributes = current_state[_ATTRIBUTES]

        if target_key == _TEMPERATURE and not attributes.get(_TEMPERATURE):
            data = {_HIGH:  value + self._temperature_step, _LOW: value - self._temperature_step}
        else:
            data = {target_key: value}

        if target_key == _HIGH and _LOW in attributes:
            data[_LOW] = attributes[_LOW]  # homeassistant gives a 400 if we don't provide both
        if target_key == _LOW and _HIGH in attributes:
            data[_HIGH] = attributes[_HIGH]

        entity_id = current_state[_ENTITY_ID]
        data[_ENTITY_ID] = entity_id
        return data

    def handle_fallback(self, message):
        utterance = message.data.get('utterance')
        answer = self._client.converse(utterance)
        if answer == "Sorry, I didn't understand that" or answer.endswith("?"):
            LOGGER.info("Can't handle '{utterance}'".format(utterance=utterance))
            return False
        self.speak(answer)
        LOGGER.info("Can handle '{utterance}'".format(utterance=utterance))
        return True

    def shutdown(self):
        self.remove_fallback(self.handle_fallback)
        super(HomeAssistantSkill, self).shutdown()


def _adjust_brightness(current_state, adjustment):
    value = current_state[_ATTRIBUTES][_BRIGHTNESS] + adjustment
    if value > _MAX_BRIGHTNESS:
        value = _MAX_BRIGHTNESS
    if value < 0:
        value = 0
    return value


def _get_value_from_percent(percentage, max_value):
    value = percentage / 100 * max_value
    return value if value < max_value else max_value


def _adjust_temperature(current_state, adjustment, target_key):
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
