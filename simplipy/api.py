"""Define a SimpliSafe account."""
# pylint: disable=protected-access
import logging
from datetime import datetime, timedelta
from typing import Dict, Optional, Type, TypeVar
from uuid import UUID, uuid4

from aiohttp import BasicAuth, ClientSession
from aiohttp.client_exceptions import ClientError

from .errors import InvalidCredentialsError, RequestError
from .system import System, SystemV2, SystemV3  # noqa

_LOGGER = logging.getLogger(__name__)

DEFAULT_USER_AGENT: str = "SimpliSafe/2105 CFNetwork/902.2 Darwin/17.7.0"
DEFAULT_AUTH_USERNAME: str = "{0}.2074.0.0.com.simplisafe.mobile"

SYSTEM_MAP: Dict[int, Type[System]] = {2: SystemV2, 3: SystemV3}

URL_HOSTNAME: str = "api.simplisafe.com"
URL_BASE: str = f"https://{URL_HOSTNAME}/v1"

ApiType = TypeVar("ApiType", bound="API")


class API:  # pylint: disable=too-many-instance-attributes
    """Define an API object to interact with the SimpliSafe cloud."""

    def __init__(self, websession: ClientSession) -> None:
        """Initialize."""
        self._access_token: str = ""
        self._access_token_expire: Optional[datetime] = None
        self._actively_refreshing: bool = False
        self._email: Optional[str] = None
        self._refresh_token: str = ""
        self._uuid: UUID = uuid4()
        self._websession: ClientSession = websession
        self.refresh_token_dirty: bool = False
        self.user_id: Optional[str] = None

    @property
    def refresh_token(self) -> str:
        """Return the current refresh_token."""
        if self.refresh_token_dirty:
            self.refresh_token_dirty = False

        return self._refresh_token

    @refresh_token.setter
    def refresh_token(self, value: str) -> None:
        """Set the refresh token if it has changed."""
        if value == self._refresh_token:
            return

        self._refresh_token = value
        self.refresh_token_dirty = True

    @classmethod
    async def login_via_credentials(
        cls: Type[ApiType], email: str, password: str, websession: ClientSession
    ) -> ApiType:
        """Create an API object from a email address and password."""
        klass = cls(websession)
        klass._email = email

        await klass._authenticate(
            {"grant_type": "password", "username": email, "password": password}
        )

        return klass

    @classmethod
    async def login_via_token(
        cls: Type[ApiType], refresh_token: str, websession: ClientSession
    ) -> ApiType:
        """Create an API object from a refresh token."""
        klass = cls(websession)
        await klass._refresh_access_token(refresh_token)
        return klass

    async def _authenticate(self, payload_data: dict) -> None:
        """Request token data and parse it."""
        token_resp: dict = await self.request(
            "post",
            "api/token",
            data=payload_data,
            auth=BasicAuth(
                login=DEFAULT_AUTH_USERNAME.format(self._uuid),
                password="",
                encoding="latin1",
            ),
        )

        self._access_token = token_resp["access_token"]
        self._access_token_expire = datetime.now() + timedelta(
            seconds=int(token_resp["expires_in"]) - 60
        )
        self.refresh_token = token_resp["refresh_token"]

        auth_check_resp: dict = await self.request("get", "api/authCheck")
        self.user_id = auth_check_resp["userId"]

    async def _refresh_access_token(self, refresh_token: str) -> None:
        """Regenerate an access token."""
        await self._authenticate(
            {
                "grant_type": "refresh_token",
                "username": self._email,
                "refresh_token": refresh_token,
            }
        )

        self._actively_refreshing = False

    async def get_systems(self) -> Dict[str, System]:
        """Get systems associated to this account."""
        subscription_resp: dict = await self.get_subscription_data()

        systems: Dict[str, System] = {}
        for system_data in subscription_resp["subscriptions"]:
            version = system_data["location"]["system"]["version"]
            system_class = SYSTEM_MAP[version]
            system = system_class(self, system_data["location"])
            await system.update(refresh_location=False)
            systems[system_data["sid"]] = system

        return systems

    async def get_subscription_data(self) -> dict:
        """Get the latest location-level data."""
        subscription_resp: dict = await self.request(
            "get", f"users/{self.user_id}/subscriptions", params={"activeOnly": "true"}
        )

        _LOGGER.debug("Subscription response: %s", subscription_resp)

        return subscription_resp

    async def request(
        self,
        method: str,
        endpoint: str,
        *,
        headers: dict = None,
        params: dict = None,
        data: dict = None,
        json: dict = None,
        **kwargs,
    ) -> dict:
        """Make a request."""
        if (
            self._access_token_expire
            and datetime.now() >= self._access_token_expire
            and not self._actively_refreshing
        ):
            self._actively_refreshing = True
            await self._refresh_access_token(self._refresh_token)

        url: str = f"{URL_BASE}/{endpoint}"

        if not headers:
            headers = {}
        if not kwargs.get("auth") and self._access_token:
            headers["Authorization"] = f"Bearer {self._access_token}"
        headers.update({"Host": URL_HOSTNAME, "User-Agent": DEFAULT_USER_AGENT})

        try:
            async with self._websession.request(
                method,
                url,
                headers=headers,
                params=params,
                data=data,
                json=json,
                **kwargs,
            ) as resp:
                resp.raise_for_status()
                return await resp.json(content_type=None)
        except ClientError as err:
            if "401" in str(err):
                if self._actively_refreshing:
                    _LOGGER.error("Refresh token was unsuccessful on 401")
                    raise InvalidCredentialsError
                if self._refresh_token:
                    _LOGGER.info("401 detected; attempting refresh token")
                    self._access_token_expire = datetime.now()
                    return await self.request(
                        method,
                        endpoint,
                        headers=headers,
                        params=params,
                        data=data,
                        json=json,
                        **kwargs,
                    )
                raise InvalidCredentialsError
            if "403" in str(err):
                if self.user_id:
                    _LOGGER.info("Endpoint unavailable in plan: %s", endpoint)
                    return {}
                raise InvalidCredentialsError

            raise RequestError(f"Error requesting data from {endpoint}: {err}")
