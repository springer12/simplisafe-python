"""Define a SimpliSafe lock."""
from enum import Enum
import logging

from simplipy.entity import EntityV3

_LOGGER: logging.Logger = logging.getLogger(__name__)


class LockStates(Enum):
    """States that a lock can be in."""

    unlocked = 0
    locked = 1
    jammed = 2
    unknown = 99


SET_STATE_MAP = {LockStates.locked: "lock", LockStates.unlocked: "unlock"}


class Lock(EntityV3):
    """A lock that works with V3 systems.

    Note that this class shouldn't be instantiated directly; it will be
    instantiated as appropriate via :meth:`simplipy.API.get_systems`.
    """

    @property
    def disabled(self) -> bool:
        """Return whether the lock is disabled.

        :rtype: ``bool``
        """
        return self.entity_data["status"]["lockDisabled"]

    @property
    def lock_low_battery(self) -> bool:
        """Return whether the lock's battery is low.

        :rtype: ``bool``
        """
        return self.entity_data["status"]["lockLowBattery"]

    @property
    def pin_pad_low_battery(self) -> bool:
        """Return whether the pin pad's battery is low.

        :rtype: ``bool``
        """
        return self.entity_data["status"]["pinPadLowBattery"]

    @property
    def pin_pad_offline(self) -> bool:
        """Return whether the pin pad is offline.

        :rtype: ``bool``
        """
        return self.entity_data["status"]["pinPadOffline"]

    @property
    def state(self) -> LockStates:
        """Return the current state of the lock.

        :rtype: :meth:`simplipy.lock.LockStates`
        """
        if bool(self.entity_data["status"]["lockJamState"]):
            return LockStates.jammed

        raw_state = self.entity_data["status"]["lockState"]

        try:
            return LockStates(raw_state)
        except ValueError:
            _LOGGER.error("Unknown raw lock state: %s", raw_state)
            return LockStates.unknown

    async def _set_lock_state(self, state: LockStates) -> None:
        """Set the lock state."""
        await self._request(
            "post",
            f"doorlock/{self._system_id}/{self.serial}/state",
            json={"state": SET_STATE_MAP[state]},
        )

        self.entity_data["status"]["lockState"] = state.value

    async def lock(self) -> None:
        """Lock the lock."""
        await self._set_lock_state(LockStates.locked)

    async def unlock(self) -> None:
        """Unlock the lock."""
        await self._set_lock_state(LockStates.unlocked)
