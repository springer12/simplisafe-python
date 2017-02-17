"""
Access to the SimpliSafe API.
"""
import uuid
import logging

import requests

from simplipy.system import SimpliSafeSystem

_LOGGER = logging.getLogger(__name__)


class SimpliSafeApiInterface(object):
    """
    Object used for talking to the SimpliSafe API.
    """

    def __init__(self):
        """
        Create the interface to the API.
        """
        self.base_url = "https://simplisafe.com/mobile"
        self.session = requests.session()
        self.session_id = None
        self.uid = None
        self.username = None
        self.password = None

    def login(self):
        """
        Log into the API using a session.
        """

        login_data = {
            'name': self.username,
            'pass': self.password,
            'device_name': 'simplisafe-python',
            'device_uuid': str(uuid.uuid1()),
            'version': '1100',
            'no_persist': '1',
            'XDEBUG_SESSION_START': 'session_name',
        }

        url_string = "{}/login/".format(self.base_url)

        response = self.session.post(url_string, data=login_data)
        if response.json()["return_code"] != 1:
            _LOGGER.error("Invalid username or password")
            return False
        response_object = response.json()

        self.session_id = response_object['session']
        self.uid = response_object['uid']

        _LOGGER.info("Logged into SimpliSafe")
        return True

    def logout(self):
        """
        Log out of the API.
        """
        _LOGGER.info("Logging out of SimpliSafe")
        url_string = "{}/logout".format(self.base_url)
        self.session.post(url_string)

    def set_device_state(self, location_id, state):
        """
        Set the state of the alaram system.

        Args:
            location_id (str): The location id to change the state of.
            state (str): The state to set. One of ['home', 'away', 'off']
        Returns (dictionary): Dictionary of the response JSON
        """
        url_string = "{}/{}/sid/{}/set-state".format(self.base_url,
                                                                            self.uid,
                                                                            location_id)

        state_data = {
            'state': state,
            'mobile': '1',
            'no_persist': '0',
            'XDEBUG_SESSION_START': 'session_name',
        }

        response = self.session.post(url_string, data=state_data)
        return response.json()

    def get_locations(self):
        """
        Gets the locations from the API.

        Returns (dictionary): Dictionary of JSON of the locations on
                              the account.
        """
        url_string = "{}/{}/locations".format(self.base_url,
                                              self.uid)
        response = self.session.post(url_string)
        return response.json()

    def get_state(self, location_id, path):
        """
        Create the PubNub connection object.

        Args:
            location_id (str): The id of the location
            path (str): The end of the URL, what state to pull.
                        One of ['events', 'dashboard']
        Returns: (dictionary): Dictionary of response from endpoint
        """
        url_string = "{}/{}/sid/{}/{}".format(self.base_url,
                                              self.uid,
                                              location_id,
                                              path)
        response = self.session.post(url_string)
        return response.json()

    def set_credentials(self, username, password):
        """
        Sets the global variables used for authentication to the API.
        """
        self.username = username
        self.password = password
        return self.login()


def get_systems(api_interface):
    """
    Gets the locations from the API and returns objects for each.

    Returns (list): Returns a list of SimpliSafeSystem objects.
    """
    locations = []

    json_locations = api_interface.get_locations()
    location_list = list(json_locations.get('locations'))
    for location in location_list:
        state = json_locations.get('locations')[location].get('system_state')
        locations.append(SimpliSafeSystem(api_interface, location, state))
    return locations
