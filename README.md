## Note: the package is under development.

## 1. Assets
#### 1.1 Authentication client

The client is represented by TwitchAuthClient class, which is responsible for exposing 
the authentication code url and obtaining the access token. 
In fact, the class is just a namespace for aggregating the methods,
as the both public methods of the class are static, 
which allows to prevent populating multiple instancess of the class.

Initialization:
```python
from twitch_listener import TwitchAuthClient
auth_client = TwitchAuthClient(
    <client_id>,
    <client_secret>,
    <redirect_uri>
)
```

Get auth code:
```python
auth_client.get_auth_code_url()
```
Returns str. URL string for requesting an auth code from Twitch.

Get access token:
```python
auth_client.get_auth_token()
```
Requests Twitch Authentication API to obtain the access token using an auth code.
Returns: str. Access token.


#### 1.2. Subscription client
 
TwitchSubscribeClient class provides the methods for subscribing Twitch API Webhooks.
The client uses the new [Twitch Helix API](http://google.com) for all requests, 
including obtaining logged user's id.

SubscriptionClient's constructor accepts the following parameters:
```
streamer_name: Favorite streamer's name
client_id: Twitch App client id
access_token: Obtained access token
session_id: unique socket session id
```

Initialization:

```python
from twitch_listener import TwitchSubscribeClient
client = TwitchSubscribeClient(
    streamer_name=<streamer_name>,
    client_id=<client_id>,
    access_token=<access_token>,
    session_id=<session_id>,
    callback_url=<callback_url>
)
```

The public interface:
```python
client.subscribe_to_all_events() # Subscribe all available events.

client.unsubscribe_from_all_events() # Unsubscribe all events. TODO: implement.

client.subscribe_following() # Subscribe the "Streamer starts following someone" event.

client.subscribe_followed_by() # Subscribe the "Streamer is followed by someone" event.

client.subscribe_stream_changed() # Subscribe stream changes events.

client.subscribe_user_changed() # Subscribe "user changed" event. TODO: not tested. SSL/TSL certs must be configured on server.
```
thebhooks Endpoint, subscription duration, request timeout and other properties are stored in the class.
The default subscription time: 1000 seconds.


## 2. Demo app - web-server (examples/listener-app)

The server is responsible for exposing the web pages to users,
reading callbacks and dispatching subscripted events to clients.
The server uses Flask-SocketIO to bear websocket connections with clients, 
emit and receive messages.
Flask-Session package capacities are used for storing the session data 
(access_tokens and client_session ids).
Currently the Session just uses a disk space to store the data, 
but in production some key-value store or relational database should be used.

##### Web-server API:

```
URL: '/', methods=['GET'] - Show index/landing page.
URL: '/auth', methods=['GET'] - Handle "auth code" callback and request auth token.
URL: '/enter_streamer', methods=['GET', 'POST'] - Handle "Choose streemer" form.
URL: '/stream', methods=['GET'] - Show the main stream page.
URL:'/callback/<session_id>', methods=['GET', 'POST'] - Handle requests from Twitch Webhooks Hub. 

Accept socket event: 'stream_connected' - Initiate subscriptions after client landed the stream page.
Accept socket event: 'disconnect' - Handle built-in "disconnect" event.

Emit socket event: "event_updated" - sent by Twitch Webhookscallback function handler, when streamer's event is updated.
```



#### Default workflow


1. Expose the landing page with the authentication link at "/". The auth link url generated with AuthStaticClient.

2. Redirect user to Twitch Server for authentication on "Authenticate" link click.

3. As the auth completes, the Twitch Auth API returns an authentication code as a param in request to "/auth".

4. The "/auth" route handler function requests an access token using the obtained auth code.

5. After the token is obtained, user is redirected to "Choose streamer" form at "/enter_streamer".

6. Once the streamer's form is submitted, the server redirects to "/stream" URL.

7. Client's web-browser dispatches "stream_connected" message, as soon as the corresponding JS script is loaded.

8. Web-socket message (client->server) "stream_connected" triggers 
the SubscriptionClient object initiation, which subscribes all available events.
*Note:* websocket session id is passed to Webhooks Server, so our server know the client it should expose the message to, 
as any callback is deliver.
9. The "subscription" requests caught by "/callback/<session_id" handled and and responded to  Twitch Webhooks API.

10. As soon as the subscription requests confirmed, the-web server starts catching 
Twitch Webhooks callbacks and transfer them to corresponding clients.

