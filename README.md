## 1. Assumptions


1.1. First, I got a bit of confusion with the definition of "Streamer's event". 
First I thought that it's something that's shown at the "events" tab, but after reading 
the Twitch API docs, I've realized that webhook subscriptions most likely was meant by "event". 
So, I've proceeded taking that assumption into an account.


1.2. I thought that it doesn't worth to spend time on prettifying the Webhooks callbacks output in browser (Streamer's events),
and displayed it as is (raw received data). It's easy to make the messages human-readable, but, I've assumed, 
the point of the assignment was different. Same for the html templates - they are super basic.



## 2. Implementation

### 2.1. Technology stack
The project is implemented on Python3.6 using Flask and Flask-SocketIO.
Flask-SocketIO is responsible for bearding the websocket connection with the clients.
The socket transport is supplied by gevent.

*Note:* The implementation is generally quite raw and there is a large room to improve it, 
which may require a bit of extra time. There is a bunch of TODOs left in the code 
to indicate some of the must-have features.

### 2.2. Components.

The implementation itself consists of 3 main components:
* Authentication client;
* Subscription client;
* Web-server, which handles the user routes and Twitch Webhooks Hub callbacks.


#### 2.2.1. Authentication client

The client is represented by AuthStaticClient class, which is responsible for exposing 
the authentication code url and obtaining the access token. 
In fact, the class is just a namespace for aggregating the methods,
as the both public methods of the class are static, 
which allows to prevent populating multiple instancess of the class.

Get auth code:
```python
AuthStaticClient.get_auth_code_url()
```
Returns str. URL string for requesting an auth code from Twitch.

Get access token:
```python
AuthStaticClient.get_auth_token()
```
Requests Twitch Authentication API to obtain the access token using an auth code.
Returns: str. Access token.


#### 2.2.2. Subscription client

SubscriptionClient class provides the methods for subscribing Twitch API Webhooks.
The client uses the new [Twitch Helix API](http://google.com) for all requests, 
including obtaining logged user's id.

SubscriptionClient's constructor accepts the following parameters:
```
streamer_name: Favorite streamer's name
client_id: Twitch App client id
access_token: Obtained access token
session_id: unique socket session id
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


#### 2.2.3. Web-server

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



## 3 Default workflow


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

*Note:* [Twitch embedded livestream](https://dev.twitch.tv/docs/embed/) is used displaying the video and chat,
which allows to receive the video and chat directly to Twitch servers, bypassing our
server capacities.

## 4. Demo

A video demo that demonstrates the entire process is available via the following link: https://youtu.be/bf1pH9t2vvE

Demo server: http://206.189.173.10:5000

## 5. Improvements. High load.

*Question:* Where do you see bottlenecks in your proposed architecture and how would you approach scaling this app starting from 100 reqs/day to 900MM reqs/day over 6 months?

1. Store secure session data in key-value memory store.
Redis is a good choice here. Sharding can be used for reducing response's delays.
2. Use asynchronous model. 
Currently it's implemented in synchonous and single thread-mode. 
The asyncronous model will helf a lot in the subscription workflow,
 as there is no need to subscribe to events in a precise order synchorously.
3. Basically, our web-server currently does 3 jobs - the authentication process, subscription and events handling.
 Those processes are highly-independent, so they can be delivered as stand-alone microservices, 
 what simplifies high-load management and load-balancing.
4. Because of large number of users expecting, we may assume, that some (actually, a lot) 
of the users will subscribe the same channels (choose the same favorite streamer).
Considering that, we can keep hashmap-based pools of active subscriptions 
(e.g. in a memory key-value storage mentioned above), 
and re-use the existing subscription, so the reduncant subscription process 
can be avoided, which reduces a load for the subscription service.
Also, we can take some assumptions regarding data sharding strategy. 
e.g. we can expect that interesets of users located nearby 
(e.g. in a same country) are more similar than interests of users
from different parts of the world, i.e. we can keep the persistent data 
and requests cache considering that. 
Beside that we can apply some similar location-based strategies for load-balancing, 
e.g. use Weighted Least-Connection and Geographic Load Balancing.

## 6. AWS Deployment.

*Question:* How would you deploy the above on AWS? (ideally a rough architecture diagram will help)

Unfortunately, some time ago I've faced with a problem with AWS - 
Amazon doesn't want to register my account, as it can't 
verify my address due to my country and region, 
so I don't have to say much about AWS deployment, 
which is unfortunate for me, as I have an interest to AWS.

After just 10-15 minutes of googling I came up with a simple suggestion to use EC2 instance, which is configured 
to be used be web-apps. I could retell the [docs](https://docs.aws.amazon.com/elasticbeanstalk/latest/dg/create-deploy-python-flask.html) or [multiple available tutorials](https://medium.com/@rodkey/deploying-a-flask-application-on-aws-a72daba6bb80,
), but it will not make much sense, as I've not be able to touch it by myself.
I could just summarize the basic AWS deployment process for my application as:
1. Create an instance using AWS Elastic Beanstalk tool.
2. Create EB CLI repository to automate the deployment and configuration process.
3. Configure the enviroment. EB allows to configure the VM instance, load balances, security groups,
code source storage, domain name and others.

