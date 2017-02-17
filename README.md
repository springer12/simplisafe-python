# simplisafe-python
Python3 interface to the SimpliSafe API.

Original source was obtained from https://github.com/greencoder/simplisafe-python

greencoder, thanks for all the hard work!

**NOTE** SimpliSafe has no official API therefore this library could stop working at any time, without warning.

```python
from simplipy.api import SimpliSafeApiInterface, get_systems

simplisafe = SimpliSafeApiInterface()
status = simplisafe.set_credentials("EMAIL", "PASSWORD")
if status:
    locations = get_systems(simplisafe)
    for location in locations:
        print("State: " + location.state())
        print("Temp: " + str(location.temperature()))
        print("Fire: " + location.fire())
        print("Flood: " + location.flood())
        print("CO: " + location.carbon_monoxide())
        print("Alarm: " + location.alarm())
        print("Last event: " + location.last_event())
        location.api.logout()
        location.update()
else:
    print("Failed to login. Invalid username or password")
```
