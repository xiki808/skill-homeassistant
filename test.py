from unittest import TestCase, main
from mycroft.skills.core import MycroftSkill
from mycroft.skills.common_iot_skill import IoTRequest, Action, Thing, State
from mock import MagicMock

from . import HomeAssistantSkill


class TestHomeAssistantSkill(TestCase):
    """
    Test the HomeAssistantSkill.

    This currently provides very minimal testing of the skill. The expectation
    is that full coverage initially is unnecessary, but that bugs should result
    in fixes that should always be accompanied by a test. Thus this lays the
    groundwork necessary to implement more tests over time, if/when they are
    necessary.
    """

    def setUp(self) -> None:
        MycroftSkill.__init__ = MagicMock()
        self.ha_skill = HomeAssistantSkill()
        self.ha_skill._client = MagicMock()
        self.ha_skill._client.domains = MagicMock(return_value={"light", "switch"})

    def can_handle(self, request: IoTRequest):
        return self.ha_skill.can_handle(request)[0]

    def test_can_handle(self):
        self.assertTrue(self.can_handle(IoTRequest(Action.ON, Thing.LIGHT)))
        self.assertTrue(self.can_handle(IoTRequest(Action.OFF, Thing.LIGHT)))
        self.assertTrue(self.can_handle(IoTRequest(Action.ON, Thing.SWITCH)))
        self.assertTrue(self.can_handle(IoTRequest(Action.OFF, Thing.SWITCH)))
        self.assertTrue(self.can_handle(IoTRequest(Action.BINARY_QUERY, Thing.SWITCH, state=State.POWERED)))

        self.assertFalse(self.can_handle(IoTRequest(Action.INCREASE, Thing.HEAT)))
        self.assertFalse(self.can_handle(IoTRequest(Action.DECREASE, Thing.HEAT)))
        self.assertFalse(self.can_handle(IoTRequest(Action.INCREASE, Thing.AIR_CONDITIONING)))
        self.assertFalse(self.can_handle(IoTRequest(Action.DECREASE, Thing.AIR_CONDITIONING)))


if __name__ == '__main__':
    main()