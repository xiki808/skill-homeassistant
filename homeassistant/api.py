import json
import requests

from mycroft.util.log import getLogger


LOGGER = getLogger(__name__)


class HomeAssistantApi():

    def __init__(self,
                 token: str,
                 hostname: str = "localhost",
                 port: int = 8123,
                 ssl: bool = False,
                 verify: bool = False):

        scheme = "https" if ssl else "http"

        self.headers = {
            'Authorization': "Bearer {}".format(token),
            'Content-Type': 'application/json'
        }

        self.base_url = "{scheme}://{hostname}:{port}/api/".format(
            scheme=scheme,
            hostname=hostname,
            port=port)

        self.verify = verify

    def _request(self, method: str, endpoint: str, data: dict = None):

        url = self.base_url + endpoint

        response = requests.request(method,
                                url,
                                data=json.dumps(data),
                                headers=self.headers,
                                verify=self.verify)

        response.raise_for_status()

        return response

    def _get(self, endpoint: str):
        return self._request('GET', endpoint)

    def _post(self, endpoint: str, data: dict):
        return self._request('POST', endpoint, data)

    def get_states(self, entity_id: str = None):
        path = "states"

        if entity_id:
            path += "/" + entity_id

        return self._get(path)

    def get_services(self):
        return self._get("services")

    def run_service(self, domain: str, service: str, data: dict):
        endpoint = "services/{domain}/{service}".format(
            domain=domain, service=service)
        LOGGER.info("Running {service} with {data}".format(service=endpoint, data=data))
        return self._post(endpoint, data)

    def converse(self, text: str):
        endpoint = "conversation/process"
        return self._post(endpoint, {"text": text})

