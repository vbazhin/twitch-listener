import requests
from requests.compat import urlencode
from . import settings


class AuthStaticClient:
    """Authentication client class.

    Exposes Auth code url, and requests the assess token."""
    REDIRECT_URI = settings.AUTH_REDIRECT_URI
    CLIENT_ID = settings.CLIENT_ID
    CLIENT_SECRET = settings.CLIENT_SECRET
    RESPONSE_TYPE = 'code'
    SCOPE = 'user_read'

    @classmethod
    def get_auth_code_url(cls):
        """Obtain authentication code URL address.

        :return: Auth code URL.
        :rtype: str
        """
        request_params = dict(
            client_id=cls.CLIENT_ID,
            redirect_uri=cls.REDIRECT_URI,
            response_type=cls.RESPONSE_TYPE,
            scope=cls.SCOPE
        )
        return 'https://id.twitch.tv/oauth2/authorize?{}' \
               ''.format(urlencode(request_params))

    @classmethod
    def _get_token_url(cls, auth_code):
        request_params = dict(
            client_id=cls.CLIENT_ID,
            client_secret=cls.CLIENT_SECRET,
            code=auth_code,
            redirect_uri=cls.REDIRECT_URI,
            grant_type='authorization_code'
        )
        return 'https://id.twitch.tv/oauth2/token?{}' \
               ''.format(urlencode(request_params))

    @classmethod
    def get_access_token(cls, auth_code):
        """Obtain access_token token using provided auth code.

        :param auth_code: Authentication code.
        :type auth_code: str.
        :return: Access token.
        :rtype: str.
        """
        token_url = cls._get_token_url(auth_code)
        response = requests.post(token_url)
        if 'access_token' not in response.json():
            raise ValueError('"access_token" param '
                             'not found in the response')
        access_token = response.json()['access_token']
        return access_token
