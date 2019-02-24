import requests
from requests.compat import urlencode
from utils import join_urls


class TwitchAuthClient:
    """Authentication client class.

    Exposes Auth code url and requests the assess token as static functions."""
    RESPONSE_TYPE = 'code'
    SCOPE = 'user_read'
    BASE_URL = 'https://id.twitch.tv/oauth2/'
    AUTH_CODE_ENDPOINT = 'authorize'
    ACCESS_TOKEN_ENDPOINT = 'token'

    def __init__(self, client_id, client_secret, redirect_uri):
        self._client_id = client_id
        self._client_secret = client_secret
        self._redirect_uri = redirect_uri

    def get_auth_code_url(self):
        """Obtain authentication code URL address.

        :return: Auth code URL.
        :rtype: str
        """
        request_params = dict(
            client_id=self._client_id,
            redirect_uri=self._redirect_uri,
            response_type=self.RESPONSE_TYPE,
            scope=self.SCOPE
        )
        url = join_urls(self.BASE_URL, self.AUTH_CODE_ENDPOINT)
        return f'{url}?{urlencode(request_params)}'

    def _get_token_url(self, auth_code):
        request_params = dict(
            client_id=self._client_id,
            client_secret=self._client_secret,
            redirect_uri=self._redirect_uri,
            grant_type='authorization_code',
            code=auth_code,
        )
        url = join_urls(self.BASE_URL, self.ACCESS_TOKEN_ENDPOINT)
        return f'{url}?{urlencode(request_params)}'

    def get_access_token(self, auth_code):
        """Obtain access_token token using provided auth code.

        :param auth_code: Authentication code.
        :type auth_code: str.
        :return: Access token.
        :rtype: str.
        """
        token_url = self._get_token_url(auth_code)
        response = requests.post(token_url)
        response.raise_for_status()
        if 'access_token' not in response.json():
            raise ValueError('"access_token" param '
                             'not found in the response')
        access_token = response.json()['access_token']
        return access_token
