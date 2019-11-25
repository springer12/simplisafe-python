Websocket
#########

**NOTE:** this feature is ``experimental``. It may (1) change its API without warning and
(2) stop working at any time.

``simplipy`` provides a websocket that allows for near-real-time detection of certain
events from a user's SimpliSafe™ system. This websocket can be accessed via the
``websocket`` property of the ``API`` object:

.. code:: python

    simplisafe = await simplipy.API.login_via_credentials(
        "<EMAIL>", "<PASSWORD>", websession
    )

    simplisafe.websocket
    # >>> <simplipy.websocket.Websocket object>

Connecting to the Websocket
---------------------------

.. code:: python

    await simplisafe.websocket.async_connect()

Disconnecting from the Websocket
--------------------------------

.. code:: python

    await simplisafe.websocket.async_disconnect()

Responding to Events
--------------------

Users respond to events by defining handlers (synchronous functions *or* coroutines) and
using the appropriate registration method. The following events exist:

* ``connect``: occurs when the websocket connection is established
* ``disconnect``: occurs when the websocket connection is terminated
* ``event``: occurs when any data is transmitted from the SimpliSafe™ cloud

Note that you can only register one handler (synchronous function or coroutine) per
event; calling ``async_on_<event>`` or ``on_<event>`` more than once will override the
existing handler (again, regardless of whether the old handler was a synchronous function
or a coroutine).

``connect``
***********

Asynchronous
============

.. code:: python

    async def async_connect_handler():
        print("I connected to the websocket")

    simplisafe.websocket.async_on_connect(async_connect_handler)

Synchronous
===========

.. code:: python

    def connect_handler():
        print("I connected to the websocket")

    simplisafe.websocket.on_connect(connect_handler)

``disconnect``
**************

Asynchronous
============

.. code:: python

    async def async_disconnect_handler():
        print("I disconnected from the websocket")

    simplisafe.websocket.async_on_disconnect(async_disconnect_handler)

Synchronous
===========

.. code:: python

    def disconnect_handler():
        print("I disconnected from the websocket")

    simplisafe.websocket.on_disconnect(disconnect_handler)

``event``
**************

Asynchronous
============

.. code:: python

    async def async_event_handler(data):
        print(f"I also got some data: {data}")

    simplisafe.websocket.async_on_event(async_event_handler)

Synchronous
===========

.. code:: python

    def event_handler(data):
        print(f"I got some data: {data}")

    simplisafe.websocket.on_event(event_handler)

Response Format
===============

The ``data`` argument has the same schema as data returned from ``system.get_events()``.
For example, when the system is armed in home mode, users may expect a ``data`` argument
with this value:

.. code:: json

    {
      "eventId": 1231231231,
      "eventTimestamp": 1231231231,
      "eventCid": 1231,
      "zoneCid": "3",
      "sensorType": 0,
      "sensorSerial": "",
      "account": "xxxxxxxx",
      "userId": 123123,
      "sid": 123123,
      "info": "System Armed (Home) by Remote Management",
      "pinName": "",
      "sensorName": "",
      "messageSubject": "SimpliSafe System Armed (home mode)",
      "messageBody": "System Armed (home mode)",
      "eventType": "activity",
      "timezone": 2,
      "locationOffset": -420,
      "videoStartedBy": "",
      "video": {}
    }
