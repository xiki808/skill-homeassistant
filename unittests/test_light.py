from unittest import TestCase
from ha_client import HomeAssistantClient

kitchen_light = {'state': 'off', 'id': '1', 'dev_name': 'kitchen'}


class TestHaClient(TestCase):

    def test_find_entity(self):
        ha = HomeAssistantClient('167.99.144.205', 'password', 'ssl' == 'false', 'verify' == 'false')
        entity = ha.find_entity(kitchen_light['dev_name'], 'light')
        if entity['dev_name'] == 'Kitchen Lights':
            self.assertTrue(True)

    def test_turn_on_lights(self):
        ha = HomeAssistantClient('167.99.144.205', 'password', 'ssl' == 'false', 'verify' == 'false')
        entity = ha.find_entity(kitchen_light['dev_name'], 'light')
        ha_data = {'entity_id': entity['id']}
        action = 'on'
        r = ha.execute_service("homeassistant", "turn_%s" % action,
                           ha_data)
        if r.status_code == 200:
            self.assertTrue(True)



if __name__ == '__main__':
    unittest.main()



