import uuid

import requests

from simplipy.system import SimpliSafeSystem


USERNAME = None
PASSWORD = None

class SimpliSafeApiInterface(object):


    def __init__(self):
        self.base_url = "https://simplisafe.com/mobile"
        self.session = requests.session()
        self.session_id = None
        self.uid = None
  
    def login(self):

        login_data = {
            'name': USERNAME,
            'pass': PASSWORD,
            'device_name': 'simplisafe-python',
            'device_uuid': str(uuid.uuid1()),
            'version': '1100',
            'no_persist': '1',
            'XDEBUG_SESSION_START': 'session_name',
        }

        url_string = "{}/login/".format(self.base_url)

        response = self.session.post(url_string, data=login_data)
        response_object = response.json() 

        self.session_id = response_object['session']
        self.uid = response_object['uid']
       
        return response_object

    def logout(self):
        url_string = "{}/logout".format(self.base_url)

        response = self.session.post(url_string)

    def set_device_state(self, system, state):
        self.login()
        url_string = "{}/{}/sid/{}/set_state".format(self.base_url,
                                                     system.uid,
                                                     system.location_id)

        state_data = {
            'state': state,
            'mobile': '1',
            'no_persist': '0',
            'XDEBUG_SESSION_START': 'session_name',
        }
                                                  
        response = self.session.post(url_string, data=state_data)
        self.logout()
        return response.json()

    def get_state(self, path):
        url_string = "{}/{}/{}".format(self.base_url,
                                       self.uid,
                                       path)
        response = self.session.post(url_string)
        return response.json()


def set_credintials(username, password):
    global USERNAME, PASSWORD
    USERNAME = username
    PASSWORD = password

def get_locations():
    locations = []
    api_interface = SimpliSafeApiInterface()

    api_interface.login()
    json_locations = api_interface.get_state("/locations")
    num_locations = json_locations.get('num_locations')
    if num_locations == 1:
        location = list(json_locations.get('locations'))[0]
        state = json_locations.get('locations')[location].get('system_state')
        locations.append(SimpliSafeSystem(api_interface, location, state))
    api_interface.logout()
    return locations
