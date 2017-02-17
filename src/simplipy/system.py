"""
SimpliSafe Alarm object.
"""
import logging

_LOGGER = logging.getLogger(__name__)


class SimpliSafeSystem(object):
    """
    Represents a SimpliSafe alarm system.
    """

    def __init__(self, api_interface, location_id, state):
        """
        Alarm object.

        Args:
            api_interfce (object): The API object to handle communication
                                   to and from the API.
            location_id (str): The location id to change the state of.
            state (str): The the initial state of the system.
        """
        self.api = api_interface
        self.location_id = location_id
        self.session_id = None
        self.uid = None
        self.system_state = state
        self.update()

    def state(self):
        """
        Return the current state of the system. (str)
        """
        return self.system_state

    def temperature(self):
        """
        Return the current temperature of the system.
        Will return null if API doesn't return an int.
        """
        api_temp = self.sensors.get("freeze").get("temp")
        try:
            return int(api_temp)
        except ValueError:
            return None

    def carbon_monoxide(self):
        """
        Current state of CO sensor.
        """
        return self.sensors.get("recent_co").get("text")

    def flood(self):
        """
        Current state of flood sensor.
        """
        return self.sensors.get("recent_flood").get("text")

    def fire(self):
        """
        Current state of fire detector.
        """
        return self.sensors.get("recent_fire").get("text")

    def alarm(self):
        """
        Current state of recent alarm.
        """
        return self.sensors.get("recent_alarm").get("text")

    def last_event(self):
        """
        Return the last event sent by the system.
        """
        return self.events.get("events")[0].get("event_desc")

    def update(self, retry=True):
        """
        Fetch all of the latest states from the API.
        """
        try:
            dashboard = self.api.get_state(self.location_id, "dashboard")
            self.sensors = dashboard["location"]["monitoring"]
            self.events = self.api.get_state(self.location_id, "events")
            locations = self.api.get_locations()
            location = locations.get('locations').get(self.location_id)
            self.system_state = location.get('system_state')
        except ValueError:
            if retry:
                _LOGGER.error("Invalid response from API. Attempting to log in again.")
                self.api.login()
                self.update(False)

    def set_state(self, state, retry=True):
        """
        Set the state of the alarm system.
        """
        try:
            self.api.set_device_state(self.location_id, state)
        except ValueError:
            if retry:
                _LOGGER.error("Invalid response from API. Attempting to log in again.")
                self.api.login()
                self.set_state(state, False)
