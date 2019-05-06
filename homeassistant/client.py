from typing import Any, Callable, List, Dict

from .api import HomeAssistantApi


def cache(func: Callable) -> Callable:
    """
    Decorator to cache a function's result.
    This sets a property of the function itself
    to the result of the function call. This avoids
    the need to keep state in another object.
    This adds a `use_cache` parameter to the function.
    If set to False, the result will be regenerated. It
    is True by default.
    """
    func.cached_result = None

    def new_func(self, use_cache: bool = True) -> Any:
        if not use_cache or not func.cached_result:
            func.cached_result = func(self)
        return func.cached_result

    return new_func


class HomeAssistantClient():

    def __init__(self,
                 token: str,
                 hostname: str = "localhost",
                 port: int = 8123,
                 ssl: bool = False,
                 verify: bool = False):

        self._api = HomeAssistantApi(token, hostname, port, ssl, verify)

    @cache
    def services(self):
        return self._api.get_services()

    @cache
    def entities(self):
        states = self._api.get_states().json()
        return {state['entity_id']: state['attributes'].get('friendly_name')
                for state in states}

    def get_states(self, entity_id = None):
        states = self._api.get_states(entity_id).json()

        if entity_id:
            states = [states]

        return  states

    def run_services(self, domain: str, service: str, states: List[Dict]):
        # TODO Make this async
        for state in states:
            self.run_service(domain, service, state)

    def run_service(self, domain: str, service: str, data: dict):
        self._api.run_service(domain, service, data)

    def converse(self, text):
        return self._api.converse(text).json()['speech']['plain']['speech']

