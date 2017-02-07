DASHBOARD_URL = '/$UID$/sid/$LID$/dashboard'
EVENTS_URL = '/$UID$/sid/$LID$/events'
STATE_URL = '/$UID$/sid/$LID$/set-state'

class SimpliSafeSystem(object):

    def __init__(self, api_interface, location_id, state):
        self.api = api_interface
        self.location_id = location_id
        self.session_id = None
        self.uid = None
        self.system_state = state
        # self.update_state()

    def state(self):
        return self.system_state

    def update_state(self):
        result_codes = {
            '2': 'off',
            '4': 'home',
            '5': 'away',
        }

        response = self.api.login()
