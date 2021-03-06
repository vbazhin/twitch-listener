import requests
from requests.compat import urlencode
from errors import TwitchAPIError
from utils import join_urls


class TwitchSubscribeClient:
    """Streamer event subscriptions manager.

    Allows to subscribe to streamer's updates.
    Subscribable events:
        * Streamer starts following some channe;;
        * Streamer got followed by someone;
        * Streamer's stream changed;
        * TODO: Streamer profile changed (seems, subscribing
            that requires TSL certs configure. To investigate).
    """

    BASE_URL = 'https://api.twitch.tv/helix/'
    WEBHOOKS_HUB_ENDPOINT = join_urls('webhooks', 'hub')
    LEASE_SECONDS = 1000
    REQUEST_TIMEOUT_SECONDS = 90

    class RequestMode:
        SUBSCRIBE = 'subscribe'
        UNSUBSCRIBE = 'unsubscribe'

    def __init__(self, streamer_name: str, client_id: str,
                 access_token: str, session_id: str, callback_url: str):
        """SubscriptionClient constructor.

        :param streamer_name: Favorite streamer's name.
        :param client_id: Twitch App client id.
        :param access_token: Access token.
        :param session_id: unique socket session id.
        """
        self._client_id = client_id
        self._access_token = access_token
        self._session_id = session_id
        self._callback_url = callback_url
        self.streamer_id = self._get_user_id(streamer_name)

    def subscribe_to_all_events(self) -> None:
        """Subscribe to all available events."""
        # TODO: make asyncrohous via async/await.
        self.subscribe_following()
        self.subscribe_followed_by()
        self.subscribe_stream_changed()
        # User changes subscrbtiotion requires TSL/SSL certs installed (https).
        # self.subscribe_user_changed()

    def unsubscribe_from_all_events(self) -> None:
        """Revoke subscription from all events."""
        # TODO: Implement events unsubscription for production.
        ...

    def subscribe_following(self) -> requests.Response:
        """Subscribe the "Streamer starts following someone" event."""
        topic_url = join_urls(self.BASE_URL, 'users/follows')
        params = dict(to_id=self.streamer_id)
        return self._subscribe(topic_url, params)

    def subscribe_followed_by(self) -> requests.Response:
        """Subscribe the "Streamer is followed by someone" event."""
        topic_url = join_urls(self.BASE_URL, 'users/follows')
        params = dict(from_id=self.streamer_id)
        return self._subscribe(topic_url, params)

    def subscribe_stream_changed(self) -> requests.Response:
        """Subscribe stream changes events."""
        topic_url = join_urls(self.BASE_URL, 'streams')
        params = dict(user_id=self.streamer_id)
        return self._subscribe(topic_url, params)

    def subscribe_user_changed(self) -> requests.Response:
        """Subscribe "user changed" event.
        TODO: This will not work, when callback server uses unsecure connection."""
        topic_url = join_urls(self.BASE_URL, 'users')
        params = dict(id=self.streamer_id)
        return self._subscribe(topic_url, params)

    def _subscribe(self, topic_url: str, params: dict) -> requests.Response:
        """Subscribe certain topic with the given params.

        :param: topic_url. Twitch topic url.
        :param: params. Subscription params.

        :return: Obtained response:
        """
        return self._webhooks_hub_request(
            topic_url,
            self.RequestMode.SUBSCRIBE,
            params=params
        )

    def _unsubscribe(self, topic_url: str, params: dict) -> requests.Response:
        """Unsubscribe topic.

        :param: topic_url. Subscribing topic url.
        :param: params. Subscription params.

        :return: Received response.
        """
        return self._webhooks_hub_request(
            topic_url,
            self.RequestMode.UNSUBSCRIBE,
            params=params
        )

    def _webhooks_hub_request(self, topic_url: str, mode: str,
                              params: dict=None, method: str='POST') -> requests.Response:
        """Send request to Twitch Webhooks Hub.

        :param: topic_url: Subscribing topic url.
        :param mode: Suscription mode.
        :param params: Subscription params.
        :param method: Request method.

        :return: Received response.
        """
        url = join_urls(self.BASE_URL, self.WEBHOOKS_HUB_ENDPOINT)
        urlencoded_params = urlencode(params)
        cb_url = join_urls(
                self._callback_url,
                self._session_id
            )
        return requests.request(method, url, data={
            'hub.mode': mode,
            'hub.topic': f'{topic_url}?{urlencoded_params}',
            'hub.callback': cb_url,
            'hub.lease_seconds': self.LEASE_SECONDS
            # TODO: support hub.secret for production
            # "hub.secret":"s3cRe7",
        }, headers=self._headers)

    @property
    def _bearer_token(self) -> str:
        return f'Bearer {self._access_token}'

    @property
    def _headers(self) -> dict:
        return {
            'Authorization': self._bearer_token,
            'Client-ID': self._client_id
        }

    def _get_user_id(self, username: str) -> requests.Response:
        """Get streamer's ID by username.

        :param: username.

        :return: Obtained streamer's ID.
        """
        response = self._base_request(f'users/?login={username}')
        # Raise corresponding error, if error code returned.
        response.raise_for_status()
        try:
            user_id = response.json()['data'][0]['id']
        except IndexError:
            raise TwitchAPIError('Failed to obtain user id.')
        return user_id

    def _base_request(self, endpoint: str, method: str='GET', params: dict=None):
        if params is None:
            params = ''
        else:
            params = '?' + urlencode(params)
        url = join_urls(self.BASE_URL, endpoint, params)
        response = requests.request(method, url, headers=self._headers,
                                    timeout=self.REQUEST_TIMEOUT_SECONDS)
        # Raise corresponding error, if error code returned.
        response.raise_for_status()
        return response
