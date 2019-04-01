from mycroft.skills.common_iot_skill import CommonIoTSkill,\
    IoTRequest, Thing, Action, Attribute
from mycroft.util.log import getLogger


from .homeassistant.client import HomeAssistantClient


__author__ = 'robconnolly, btotharye, nielstron'
LOGGER = getLogger(__name__)


_THING_TO_DOMAIN = {
    Thing.LIGHT: "light",
    Thing.THERMOSTAT: "climate",
    Thing.SWITCH: "switch"
}


_DOMAIN_TO_THING = {v: k for k, v in _THING_TO_DOMAIN.items()}


_THING_ACTION_SERVICE = {
    Thing.LIGHT: {
        Action.TOGGLE: "toggle",
        Action.ON: "turn_on",
        Action.OFF: "turn_off"
    },
    Thing.THERMOSTAT: {
        Action.SET: "set_temperature"
    },
    Thing.SWITCH: {
        Action.TOGGLE: "toggle",
        Action.ON: "turn_on",
        Action.OFF: "turn_off"
    }
}


class HomeAssistantSkill(CommonIoTSkill):

    def __init__(self):
        super().__init__(name="HomeAssistantSkill")
        self.ha : HomeAssistantClient = None
        self._entities = dict()

    def initialize(self):
        self.settings.set_changed_callback(self.on_websettings_changed)
        self._setup()
        self._entities = {k: v for k, v in self.ha.entities().items() if
                          self._domain(v) in _DOMAIN_TO_THING}
        self.register_entities_and_scenes()

    def on_websettings_changed(self):
        # Force a setting refresh after the websettings changed
        # Otherwise new settings will not be regarded
        self._force_setup()

    def _setup(self):
        portnumber = int(self.settings.get('portnum', 8123))
        self.ha = HomeAssistantClient(
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
        action = request.action
        thing = request.thing
        entity = request.entity

        if callback_data:
            self.ha.run_services(**callback_data)
            return

        if entity:
            entity = self._entities[entity]

        domain = self._domain(entity) if entity else _THING_TO_DOMAIN[thing]

        if not thing:
            thing = _DOMAIN_TO_THING[domain]

        service = _THING_ACTION_SERVICE[thing][action]

        self.ha.run_service(domain, service, dict())

    def can_handle(self, request: IoTRequest):
        action = request.action
        thing = request.thing
        entity = request.entity
        attribute = request.attribute

        if not thing and not entity:
            return False, None

        if thing and thing not in _THING_TO_DOMAIN:
            return False, None

        if entity and entity not in self._entities:
            return False, None

        if entity:
            entity = self._entities[entity]

        domain = self._domain(entity) if entity else None
        if domain not in _DOMAIN_TO_THING:
            return False, None

        if not thing:
            thing = _DOMAIN_TO_THING[domain]

        if thing != _DOMAIN_TO_THING[domain]:
            return False, None

        if action in _THING_ACTION_SERVICE[thing]:
            return True, None

        if thing == Thing.LIGHT:
            return self._can_handle_lights(action, attribute, entity)

        return False, None

    def _can_handle_lights(self, action: Action, attribute: Attribute, entitiy_id: str):

        LOGGER.info("_can_handle_lights: {}, {}, {}".format(action, attribute, entitiy_id))
        if action in {Action.ON, Action.OFF, Action.TOGGLE}:
            return True, None

        if action in (Action.INCREASE, Action.DECREASE) and attribute in (Attribute.BRIGHTNESS, None):
            states = self.ha.get_states(entitiy_id)

            LOGGER.info("States: " + str(states))

            states = (s for s in states if 'brightness' in s['attributes'])

            if not entitiy_id:
                states = \
                    (s for s in states if s['entity_id'.startswith('light')])

            if states:
                step = 20 if action == Action.INCREASE else -20
                states = ({"entity_id": s["entity_id"],
                           "brightness": _adjust_brightness(s, step)}
                          for s in states)

                return True, {"domain" : "light",
                              "service": "turn_on",
                              "states": list(states)}

        return False, None


def _adjust_brightness(current_state, adjustment):
    value = current_state['attributes']['brightness'] + adjustment
    if value > 254:
        value = 254
    if value < 0:
        value = 0
    return value


def create_skill():
    return HomeAssistantSkill()
