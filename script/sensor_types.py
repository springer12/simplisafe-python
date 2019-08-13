"""Get a list of all sensors in a system."""
import asyncio
import logging
import sys

sys.path.append(".")

from simplipy import API
from simplipy.errors import InvalidCredentialsError, SimplipyError

from aiohttp import ClientSession


_LOGGER = logging.getLogger()

SIMPLISAFE_EMAIL = "<EMAIL>"
SIMPLISAFE_PASSWORD = "<PASSWORD>"


async def main() -> None:
    """Create the aiohttp session and run the example."""
    async with ClientSession() as websession:
        logging.basicConfig(level=logging.INFO)

        try:
            simplisafe = await API.login_via_credentials(
                SIMPLISAFE_EMAIL, SIMPLISAFE_PASSWORD, websession
            )
            systems = await simplisafe.get_systems()
            for system in systems.values():
                for sensor_attrs in system.sensors.values():
                    _LOGGER.info(
                        "Sensor: (name: %s, type: %s)",
                        sensor_attrs.name,
                        sensor_attrs.type,
                    )
        except InvalidCredentialsError:
            _LOGGER.error("Invalid credentials")
        except SimplipyError as err:
            _LOGGER.error(err)


asyncio.get_event_loop().run_until_complete(main())
