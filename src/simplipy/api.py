"""
Access to the SimpliSafe API.
"""
import logging
import json

import requests

from simplipy.system import SimpliSafeSystem

_LOGGER = logging.getLogger(__name__)

BASE_URL = "https://api.simplisafe.com/v1/"
# Requires BasicAuth
TOKEN_URL = BASE_URL + "api/token"
AUTH_CHECK_URL = BASE_URL + "api/authCheck"
USERS_SUBSCRIPTIONS_URL = BASE_URL + "users/{}/subscriptions?activeOnly=true"
SUBSCRIPTION_URL = BASE_URL + "subscriptions/{}/"
V3_SENSORS_URL = BASE_URL + "ss3/subscriptions/{}/"

DEVICE_ID = "ANDROID; UserAgent=unknown Android SDK built for x86; Serial=unknown; ID=e36659c47cce2843;:"
USER_AGENT = "SimpliSafe Android App Build 20207"
CONTENT_TYPE = "application/json; charset=UTF-8"

HEADERS = {"User-Agent": USER_AGENT, "Content-Type": CONTENT_TYPE}
OAUTH_HEADERS = dict(HEADERS)

BASIC_AUTH_STRING = "NWYwNmY1YzktMDJkOS00ZDY2LTg3ZmUtZWRiZWQ2N2ZiMDE0LjIwMjA3LmFuZHJvaWQuc2ltcGxpc2FmZS5jb206"
BASIC_AUTH_HEADERS = dict(HEADERS)


class SimpliSafeApiInterface(object):
    """
    Object used for talking to the SimpliSafe API.
    """

    def __init__(self, username, password, basic_auth=None):
        """
        Create the interface to the API.
        """
        self.username = username
        self.password = password
        self.access_token = None
        self.refresh_token = None
        self.user_id = None
        self.sids = {}
        self.sensors = {}
        if basic_auth is not None:
            BASIC_AUTH_HEADERS["Authorization"] = "Basic " + basic_auth
        else:
            BASIC_AUTH_HEADERS["Authorization"] = "Basic " + BASIC_AUTH_STRING
        if self._get_token() and self.get_subscriptions():
            _LOGGER.info("Setup complete")
        else:
            _LOGGER.error("Failed to complete setup")

    def _get_token(self):
        """
        Get an Oauth token from the API.
        """

        login_data = {
            'device_id': DEVICE_ID,
            'grant_type': "password",
            'username': self.username,
            'password': self.password
        }

        response = requests.post(TOKEN_URL, data=json.dumps(login_data),
                                 headers=BASIC_AUTH_HEADERS)
        _LOGGER.debug(response.content)
        if response.status_code != 200:
            _LOGGER.error("Invalid username or password")
            return False
        try:
            _json = response.json()
        except ValueError:
            _LOGGER.error("Failed to decode JSON")
            return False

        self.access_token = _json.get("access_token")
        self.refresh_token = _json.get("refresh_token")

        if self._get_user_id():
            _LOGGER.info("Logged into SimpliSafe")
            return True
        return False

    def _refresh_token(self):
        """
        Attempt to refresh the token.
        """

        refresh_data = {
            'grant_type': "refresh_token",
            'refresh_token': self.refresh_token
        }

        response = requests.post(TOKEN_URL, data=json.dumps(refresh_data),
                                 headers=BASIC_AUTH_HEADERS)
        _LOGGER.debug(response.content)
        if response.status_code != 200:
            _LOGGER.error("Failed to get refresh token, logging in again")
            self._get_token()
            return False
        try:
            _json = response.json()
        except ValueError:
            _LOGGER.error("Failed to decode JSON")
            return False

        self.access_token = _json.get("access_token")
        self.refresh_token = _json.get("refresh_token")
        self._get_user_id()

        _LOGGER.info("Token was refreshed")
        return True

    def _get_user_id(self):
        """Get user ID."""

        OAUTH_HEADERS["Authorization"] = "Bearer {}".format(self.access_token)

        response = requests.get(AUTH_CHECK_URL, headers=OAUTH_HEADERS)
        _LOGGER.debug(response.content)
        if response.status_code == 401:
            _LOGGER.error("Token expired, getting new token")
            self._refresh_token()
            return False
        if response.status_code != 200:
            _LOGGER.error("Failed to get user ID")
        try:
            _json = response.json()
        except ValueError:
            _LOGGER.error("Failed to decode JSON")
            return False

        self.user_id = _json.get("userId")
        return True

    def get_subscriptions(self):
        """Get a list of a sids."""

        response = requests.get(USERS_SUBSCRIPTIONS_URL.format(self.user_id), headers=OAUTH_HEADERS)
        _LOGGER.debug(response.content)
        if response.status_code == 401:
            _LOGGER.error("Token expired, getting new token")
            self._refresh_token()
            return False
        if response.status_code != 200:
            _LOGGER.error("Failed to get subscriptions")
        try:
            _json = response.json()
        except ValueError:
            _LOGGER.error("Failed to decode JSON")
            return False

        self.sids = _json.get("subscriptions")
        return True

    def set_system_state(self, location_id, state):
        """
        Set the state of the alarm system.

        Args:
            location_id (int): The location id to change the state of.
            state (str): The state to set. One of ['home', 'away', 'off']
        Returns (boolean): True or False (Was the command successful)
        """
        _version = 2
        for subscription in self.sids:
            if subscription["sid"] == location_id:
                _version = subscription["location"]["system"]["version"]

        if _version != 3:
            _url = SUBSCRIPTION_URL.format(location_id) + "state?state=" + state
        else:
            _url = V3_SENSORS_URL.format(location_id) + "state/" + state

        response = requests.post(_url, headers=OAUTH_HEADERS)
        _LOGGER.debug(response.content)
        for subscription in self.sids:
            if subscription["sid"] == location_id:
                _log_string = "Failed to set {} state to {}".format(subscription["location"]["street1"], state)
        if response.status_code == 401:
            _LOGGER.error("Token expired, getting new token")
            self._refresh_token()
            return False
        if response.status_code != 200:
            _LOGGER.error(_log_string)
            return False
        try:
            _json = response.json()
        except ValueError:
            _LOGGER.error("Failed to decode JSON")
            return False

        if _json.get("success") or response.status_code == 200:
            return True
        _log_string = _log_string + " " + _json.get("reason")
        _LOGGER.error(_log_string)
        return False

    def _get_systems_devices_states(self, location_id, cached=True):
        """
        Get the systmes devices states.

        Args:
            location_id (int): The location id to get states for.
            cached (boolean): Weather or not the base station should be
                              polled for the updated state. True(v2) or False
                              (v3) will force an update but makes the base station
                              speak that a sync occured. False will pull
                              results from last update.
        Returns (boolean): True or False (Was the command successful)
        """

        _version = 2

        for subscription in self.sids:
            if subscription["sid"] == location_id:
                _version = subscription["location"]["system"]["version"]

        if _version != 3:
            _url = SUBSCRIPTION_URL.format(location_id) + "settings?settingsType=all&cached=" + str(cached).lower()
        else:
            _url = V3_SENSORS_URL.format(location_id) + "sensors?forceUpdate=" + str(not cached).lower()

        response = requests.get(_url, headers=OAUTH_HEADERS)
        _LOGGER.debug(response.content)
        if response.status_code == 401:
            _LOGGER.error("Token expired, getting new token")
            self._refresh_token()
            return False
        try:
            _json = response.json()
            if response.status_code != 200:
                if _json.get("errorType") == "NoRemoteManagement":
                    _LOGGER.error("No monthly monitoring on account, only system status is availble")
                    self.sensors[location_id] = {}
                    return True
                _LOGGER.error("Failed to pull updated sensor states")
                return False
        except ValueError:
            _LOGGER.error("Failed to decode JSON")
            return False

        if _json.get("success"):
            if _version != 3:
                _sensors = _json["settings"]["sensors"]
                self.sensors[location_id] = _sensors
            else:
                _sensors = _json["sensors"]
                self.sensors[location_id] = _sensors
            return True
        else:
            _LOGGER.error("Something went wrong...")
            return False

    def get_system_state(self, location_id):
        """
        Get the location_id's current system state.

        Args:
            location_id (str): The id of the location
        Returns: (dictionary): System
        """
        for subscription in self.sids:
            if subscription["sid"] == location_id:
                return subscription["location"]["system"]
        return {}

    def get_systems(self):
        """
        Gets the locations from the API and returns objects for each system.

        Returns (list): SimpliSafeSystem objects.
        """
        systems = []

        for subscription in self.sids:
            _location_id = subscription["sid"]
            self._get_systems_devices_states(_location_id)
            _system_state = self.get_system_state(_location_id)
            if _system_state:
                _system_state["sid"] = _location_id
                _system = SimpliSafeSystem(self, _system_state, self.sensors[_location_id])
                systems.append(_system)
            else:
                _LOGGER.error("Empty system state")

        return systems
