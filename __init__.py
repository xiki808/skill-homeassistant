from mycroft.skills.common_iot_skill import CommonIoTSkill,\
    IoTRequest, Thing, Action
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
        self._setup(True)

    def _domain(self, entity_id: str):
        return entity_id[:entity_id.index('.')]

    def stop(self):
        pass

    def get_entities(self):
        return self._entities.keys()

    def run_request(self, request: IoTRequest, callback_data: dict):
        action = request.action
        thing = request.thing
        entity = request.entity

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

        if action in _THING_ACTION_SERVICE[thing]:
            return True, None

        return False, None












def create_skill():
    return HomeAssistantSkill()
