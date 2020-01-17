"""Define a v3 (new) SimpliSafe sensor."""
import logging
from typing import Optional

from simplipy.entity import EntityTypes, EntityV3

_LOGGER: logging.Logger = logging.getLogger(__name__)


class SensorV3(EntityV3):
    """A V3 (new) sensor.

    Note that this class shouldn't be instantiated directly; it will be
    instantiated as appropriate via :meth:`simplipy.API.get_systems`.
    """

    @property
    def trigger_instantly(self) -> bool:
        """Return whether the sensor will trigger instantly.

        :rtype: ``bool``
        """
        return self.entity_data["setting"].get("instantTrigger", False)

    @property
    def triggered(self) -> bool:
        """Return whether the sensor has been triggered.

        :rtype: ``bool``
        """
        if self.type in (
            EntityTypes.carbon_monoxide,
            EntityTypes.entry,
            EntityTypes.glass_break,
            EntityTypes.leak,
            EntityTypes.motion,
            EntityTypes.smoke,
            EntityTypes.temperature,
        ):
            return self.entity_data["status"].get("triggered", False)

        return False

    @property
    def temperature(self) -> Optional[int]:
        """Return the temperature of the sensor (as appropriate).

        If the sensor isn't a temperature sensor, an ``AttributeError`` will be raised.

        :rtype: ``int``
        """
        if self.type != EntityTypes.temperature:
            raise AttributeError("Non-temperature sensor cannot have a temperature")

        return self.entity_data["status"]["temperature"]
