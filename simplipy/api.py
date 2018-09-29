"""Define a SimpliSafe account."""
# pylint: disable=import-error,protected-access,unused-import

from datetime import datetime, timedelta
from typing import List, Type, TypeVar, Union  # noqa

from aiohttp import BasicAuth, ClientSession, client_exceptions

from .errors import RequestError
from .system import System, SystemV2, SystemV3  # noqa

DEFAULT_USER_AGENT = 'SimpliSafe/2105 CFNetwork/902.2 Darwin/17.7.0'
DEFAULT_AUTH_USERNAME = 'a9c490a5-28c7-48c8-a8c3-1f1d7faa1394.2074.0.0.com.' \
    'simplisafe.mobile'

URL_HOSTNAME = 'api.simplisafe.com'
URL_BASE = 'https://{0}/v1'.format(URL_HOSTNAME)

SYSTEM_MAP = {2: SystemV2, 3: SystemV3}

ApiType = TypeVar('ApiType', bound='API')


class API:
    """Define an API object to interact with the SimpliSafe cloud."""

    def __init__(self, websession: ClientSession) -> None:
        """Initialize."""
        self._access_token = None
        self._access_token_expire = None  # type: Union[None, datetime]
        self._actively_refreshing = False
        self._email = None  # type: Union[None, str]
        self._websession = websession
        self.refresh_token = None
        self.user_id = None

    @classmethod
    async def login_via_credentials(
            cls: Type[ApiType], email: str, password: str,
            websession: ClientSession) -> ApiType:
        """Create an API object from a email address and password."""
        klass = cls(websession)
        klass._email = email

        await klass._authenticate({
            'grant_type': 'password',
            'username': email,
            'password': password,
        })

        return klass

    @classmethod
    async def login_via_token(
            cls: Type[ApiType], refresh_token: str,
            websession: ClientSession) -> ApiType:
        """Create an API object from a refresh token."""
        klass = cls(websession)
        await klass._refresh_access_token(refresh_token)
        return klass

    async def _authenticate(self, payload_data: dict) -> None:
        """Request token data and parse it."""
        token_resp = await self.request(
            'post',
            'api/token',
            data=payload_data,
            auth=BasicAuth(
                login=DEFAULT_AUTH_USERNAME, password='', encoding='latin1'))
        self.refresh_token = token_resp['refresh_token']

        auth_check_resp = await self.request('get', 'api/authCheck')
        self.user_id = auth_check_resp['userId']
        self._access_token = token_resp['access_token']
        self._access_token_expire = datetime.now() + timedelta(
            seconds=int(token_resp['expires_in']))

    async def _refresh_access_token(self, refresh_token: str) -> None:
        """Regenerate an access token."""
        await self._authenticate({
            'grant_type': 'refresh_token',
            'username': self._email,
            'refresh_token': refresh_token,
        })

        self._actively_refreshing = False

    async def get_systems(self) -> list:
        """Get systems associated to this account."""
        subscription_resp = await self.get_subscription_data()

        systems = []  # type: List[System]
        for system_data in subscription_resp['subscriptions']:
            version = system_data['location']['system']['version']
            system_class = SYSTEM_MAP[version]
            system = system_class(self, system_data['location'])
            await system.update(refresh_location=False)
            systems.append(system)

        return systems

    async def get_subscription_data(self) -> dict:
        """Get the latest location-level data."""
        return await self.request(
            'get',
            'users/{0}/subscriptions'.format(self.user_id),
            params={'activeOnly': 'true'})

    async def request(
            self,
            method: str,
            endpoint: str,
            *,
            headers: dict = None,
            params: dict = None,
            data: dict = None,
            json: dict = None,
            **kwargs) -> dict:
        """Make a request."""
        if (self._access_token_expire
                and datetime.now() >= self._access_token_expire
                and not self._actively_refreshing):
            self._actively_refreshing = True
            await self._refresh_access_token(  # type: ignore
                self.refresh_token)

        url = '{0}/{1}'.format(URL_BASE, endpoint)

        if not headers:
            headers = {}
        if not kwargs.get('auth') and self._access_token:
            headers['Authorization'] = 'Bearer {0}'.format(self._access_token)
        headers.update({
            'Content-Type': 'application/x-www-form-urlencoded',
            'Host': URL_HOSTNAME,
            'User-Agent': DEFAULT_USER_AGENT,
        })

        async with self._websession.request(method, url, headers=headers,
                                            params=params, data=data,
                                            json=json, **kwargs) as resp:
            try:
                resp.raise_for_status()
                return await resp.json(content_type=None)
            except client_exceptions.ClientError as err:
                raise RequestError(
                    'Error requesting data from {0}: {1}'.format(
                        endpoint, err)) from None
