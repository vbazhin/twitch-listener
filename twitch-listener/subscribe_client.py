import requests
from requests.compat import urlencode
from utils import join_urls


class TwitchAPIError(Exception):
    ...


class SubscriptionClient:
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

    def __init__(self, streamer_name, client_id, access_token,
                 session_id, callback_url):
        """SubscriptionClient constructor.

        :param streamer_name: Favorite streamer's name.
        :param client_id: Twitch App client id.
        :param access_token: Access token.
        :param session_id: unique socket session id.
        :type streamer_name: str
        :type client_id: str
        :type: access_token: str
        :type: session_id: str
        """
        self._client_id = client_id
        self._access_token = access_token
        self._session_id = session_id
        self._callback_url = callback_url
        self.screamer_id = self._get_user_id(streamer_name)

    def subscribe_to_all_events(self):
        """Subscribe to all available events."""
        # TODO: make asyncrohous via async/await.
        self.subscribe_following()
        self.subscribe_followed_by()
        self.subscribe_stream_changed()
        # User changes subscrbtiotion requires TSL/SSL certs installed (https).
        # self.subscribe_user_changed()

    def unsubscribe_from_all_events(self):
        """Revoke subscription from all events."""
        # TODO: Implement events unsubscription for production.
        ...

    def subscribe_following(self):
        """Subscribe the "Streamer starts following someone" event."""
        topic_url = join_urls(self.BASE_URL, 'users/follows')
        params = dict(to_id=self.screamer_id)
        return self._subscribe(topic_url, params)

    def subscribe_followed_by(self):
        """Subscribe the "Streamer is followed by someone" event."""
        topic_url = join_urls(self.BASE_URL, 'users/follows')
        params = dict(from_id=self.screamer_id)
        return self._subscribe(topic_url, params)

    def subscribe_stream_changed(self):
        """Subscribe stream changes events."""
        topic_url = join_urls(self.BASE_URL, 'streams')
        params = dict(user_id=self.screamer_id)
        return self._subscribe(topic_url, params)

    def subscribe_user_changed(self):
        """Subscribe "user changed" event.
        TODO: This will not work, when callback server uses unsecure connection."""
        topic_url = join_urls(self.BASE_URL, 'users')
        params = dict(id=self.screamer_id)
        return self._subscribe(topic_url, params)

    def _subscribe(self, topic_url, params):
        """Subscribe certain topic with the given params.

        :param: topic_url. Twitch topic url.
        :param: params. Subscription params.
        :type: topic_url: str.
        :type: params: dict.

        :return: Obtained response:
        :rtype: requests.Request.response
        """
        return self._webhooks_hub_request(topic_url, self.RequestMode.SUBSCRIBE, params=params)

    def _unsubscribe(self, topic_url, params):
        """Unsubscribe topic.

        :param: topic_url. Subscribing topic url.
        :param: params. Subscription params.
        :type: topic_url: str.
        :type: params: dict.

        :return: Received response.
        :rtype: requests.Response
        """
        return self._webhooks_hub_request(topic_url, self.RequestMode.UNSUBSCRIBE, params=params)

    def _webhooks_hub_request(self, topic_url, mode, params=None, method='POST'):
        """Send request to Twitch Webhooks Hub.

        :param: topic_url: Subscribing topic url.
        :param mode: Suscription mode.
        :param params: Subscription params.
        :param method: Request method.
        :type topic_url: str.
        :type mode: str.
        :type params: dict.
        :type method: str.

        :return: Received response.
        :rtype: requests.Response
        """
        url = join_urls(self.BASE_URL, self.WEBHOOKS_HUB_ENDPOINT)
        urlencoded_params = urlencode(params)
        cb_url = join_urls(
                self._callback_url,
                self._session_id
            )
        return requests.request(method, url, data={
            'hub.mode': mode,
            'hub.topic': '{}?{}'.format(
                topic_url,
                urlencoded_params
            ),
            'hub.callback': cb_url,
            'hub.lease_seconds': self.LEASE_SECONDS
            # TODO: support hub.secret for production
            # "hub.secret":"s3cRe7",
        }, headers=self._headers)

    @property
    def _bearer_token(self):
        return 'Bearer {token}'.format(token=self._access_token)

    @property
    def _headers(self):
        return {
            'Authorization': self._bearer_token,
            'Client-ID': self._client_id
        }

    def _get_user_id(self, username):
        """Get streamer's ID by username.

        :param: username.
        :type: str.

        :return: Obtained streamer's ID.
        :rtype: str.
        """
        response = self._base_request('users/?login={}'.format(username))
        # Raise corresponding error, if error code returned.
        response.raise_for_status()
        try:
            user_id = response.json()['data'][0]['id']
        except IndexError:
            raise TwitchAPIError('Failed to obtain user id.')
        return user_id

    def _base_request(self, endpoint, method='GET', params=None):
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
