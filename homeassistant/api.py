import json
import requests


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

    def get_states(self):
        return self._get("states")

    def get_services(self):
        return self._get("services")

    def run_service(self, domain: str, service: str, data: dict):
        endpoint = "services/{domain}/{service}".format(
            domain=domain, service=service)
        return self._post(endpoint, data)




