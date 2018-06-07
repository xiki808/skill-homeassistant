from unittest import TestCase
from ha_client import HomeAssistantClient
import unittest
from unittest import mock


kitchen_light = {'state': 'off', 'id': '1', 'dev_name': 'kitchen'}

json_data = {'attributes': {'friendly_name': 'Kitchen Lights',
                'max_mireds': 500,
                'min_mireds': 153,
                'supported_features': 151},
 'entity_id': 'light.kitchen_lights',
 'state': 'off'}

attr_resp = {
            "id": '1',
            "dev_name": {'attributes': {'friendly_name': 'Kitchen Lights', 'max_mireds': 500, 'min_mireds': 153, 'supported_features': 151}, 'entity_id': 'light.kitchen_lights', 'state': 'off'}}

headers = {
    'x-ha-access': 'password',
    'Content-Type': 'application/json'
}


class TestHaClient(TestCase):

    @mock.patch('ha_client.get')
    def test_connect_ssl(self, mock_get):
        portnum = None
        ssl = True
        ha = HomeAssistantClient(host='192.168.0.1', password='password', portnum=portnum, ssl=ssl)
        mock_resp = mock.Mock()
        mock_resp.status_code = 200
        mock_resp.json = mock.Mock(return_value=json_data)
        mock_get.return_value = mock_resp
        print(mock_get.return_value)
        self.assertEqual(mock_resp.json(), json_data)
        self.assertEqual(ha.portnum, 8123)

    def test_connect_nossl(self):
        portnum = None
        ssl = False
        ha = HomeAssistantClient(host='167.99.144.205', password='password', portnum=portnum, ssl=ssl)
        entity = (ha.find_entity('kitchen', 'light'))
        if entity['best_score'] >= 50:
            print(entity['best_score'])
            self.assertTrue(True)
        self.assertEqual(entity['dev_name'], 'Kitchen Lights')
        self.assertEqual(ha.ssl, False)
        self.assertEqual(ha.portnum, 8123)

    @mock.patch('ha_client.HomeAssistantClient.find_entity')
    def test_toggle_lights(self, mock_get):
        ha = HomeAssistantClient(host='192.168.0.1', password='password', portnum=8123, ssl=True)
        ha.find_entity = mock.MagicMock()
        entity = ha.find_entity(kitchen_light['dev_name'], 'light')
        mock_get.entity = {
                "id": '1',
                "dev_name": {'attributes': {'friendly_name': 'Kitchen Lights', 'max_mireds': 500, 'min_mireds': 153, 'supported_features': 151}, 'entity_id': 'light.kitchen_lights', 'state': 'off'}}
        self.assertEqual(mock_get.entity, attr_resp)
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
                if entity['best_score'] >= 50:
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



