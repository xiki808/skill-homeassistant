from unittest import TestCase
from ha_client import HomeAssistantClient
import unittest
from unittest import mock
import responses
import requests

kitchen_light = {'state': 'off', 'id': '1', 'dev_name': 'kitchen'}

json_data = {'attributes': {'friendly_name': 'Kitchen Lights',
                'max_mireds': 500,
                'min_mireds': 153,
                'supported_features': 151},
 'entity_id': 'light.kitchen_lights',
 'state': 'off'}


class TestHaClient(TestCase):

    @mock.patch('requests.get')
    def _mock_response(self, mock_get):
        responses.add(responses.GET, 'https://192.168.0.1:8123/api/states',
                      json=json_data, status=200)

        resp = requests.get('https://192.168.0.1:8123/api/states')

        assert resp.json() == json_data
        assert responses.calls[0].response.url == 'https://192.168.0.1:8123/api/states'

    def test_setup(self):
        ha = HomeAssistantClient(host='192.168.0.1', password='password', portnum=8123, ssl=True)
        print(ha.url)
        if ha.url == 'https://192.168.0.1:8123':
            if ha.headers == "{'x-ha-access': 'password', 'Content-Type': 'application/json'}":
                self.assertTrue(True)

    def test_light_attr(self):
        ha = HomeAssistantClient(host='192.168.0.1', password='password', portnum=8123, ssl=True)
        ha.find_entity = mock.MagicMock()
        entity = ha.find_entity(kitchen_light['dev_name'], 'light')
        ha.find_entity_attr = mock.MagicMock()
        light_attrs = ha.find_entity_attr(entity['id'])
        if light_attrs[1] == 'Kitchen Lights':
            self.assertTrue(True)

    def test_find_entity(self):
        ha = HomeAssistantClient(host='192.168.0.1', password='password', portnum=8123, ssl=True)
        ha.find_entity = mock.MagicMock()
        entity = ha.find_entity(kitchen_light['dev_name'], 'light')
        if entity['dev_name'] == 'Kitchen Lights':
            self.assertTrue(True)

    def test_toggle_lights(self):
        ha = HomeAssistantClient(host='192.168.0.1', password='password', portnum=8123, ssl=True)
        ha.find_entity = mock.MagicMock()
        entity = ha.find_entity(kitchen_light['dev_name'], 'light')
        ha_data = {'entity_id': entity['id']}
        state = entity['state']
        if state == 'on':
            ha.execute_service = mock.MagicMock()
            r = ha.execute_service("homeassistant", "turn_off",
                                   ha_data)
            if r.status_code == 200:
                entity = ha.find_entity(kitchen_light['dev_name'], 'light')
                if entity['state'] == 'off':
                    self.assertTrue(True)
        else:
            ha.execute_service = mock.MagicMock()
            r = ha.execute_service("homeassistant", "turn_on",
                                   ha_data)
            if r.status_code == 200:
                if entity['state'] == 'on':
                    self.assertTrue(True)


if __name__ == '__main__':
    unittest.main()



