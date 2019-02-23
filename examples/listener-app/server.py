"""Web application server module.

The server is responsible for exposing the web pages,
reading callbacks and dispatching subscripted events to clients.
"""
# Applying monkey-patch to allow sockets connection.
from gevent import monkey
monkey.patch_all()

import uuid
import datetime as dt
from requests.exceptions import HTTPError
from flask import (
    Flask, render_template,
    request, Response, redirect,
    session, url_for
)
from flask_socketio import SocketIO
from flask_session import Session
import settings
from twitch_listener import TwitchAuthClient
from twitch_listener import TwitchSubscribeClient


app = Flask(__name__)
# Use Flask-Session for storing session data secure.
# Some key value store like redis, can be used in production. Use "filesystem" storage for the demo app.
app.config['SECRET_KEY'] = uuid.uuid4()
app.config['SESSION_TYPE'] = 'filesystem'
Session(app)

socketio = SocketIO(app)


# Store current client sessions ids, to verify session,
# before sending streamer's event callbacks.
# In production Redis storage (or some other k/v store) can be used.
client_sessions = set()


auth_client = TwitchAuthClient(
    settings.CLIENT_ID,
    settings.CLIENT_SECRET,
    settings.REDIRECT_URI
)


@app.route('/', methods=['GET'])
def show_landing():
    """Show index/landing page."""
    return render_template(
        'landing.html',
        auth_url=auth_client.get_auth_code_url()
    )


@app.route('/auth')
def get_token():
    """Handle "auth code" callback and request auth token."""
    if 'code' not in request.args:
        return Response('No authentication code received', status=400)
    code = request.args['code']
    try:
        access_token = auth_client.get_access_token(code)
    except HTTPError:
        return Response('Failed to obtain access token', status=400)
    session['access_token'] = access_token
    return redirect(url_for('streamer_form'))


@app.route('/enter_streamer', methods=['GET', 'POST'])
def streamer_form():
    """Handle "Choose streemer" form."""
    # TODO: add crfs_token.
    if request.method == 'POST':
        username = request.form.get('username')
        session['streamer_name'] = username
        # TODO: reimplement
        return redirect(url_for('show_stream'))
    else:
        return render_template('streamer_form.html')


@app.route('/stream', methods=['GET'])
def show_stream():
    """Show the main stream page."""
    streamer_name = session['streamer_name']
    return render_template(
        'stream.html',
        streamer_name=streamer_name
    )


@socketio.on('stream_connected')
def stream_connected_event():
    """Initiate subscriptions.

    Triggered after receiving a "connected"
    socket message, from the "stream" page.
    """
    session_id = request.sid
    client_sessions.add(session_id)
    if 'streamer_name' not in session:
        # TODO: handle the case more compehensive.
        return
    streamer_name = session['streamer_name']
    access_token = session['access_token']
    client = TwitchSubscribeClient(
        streamer_name=streamer_name,
        client_id=settings.CLIENT_ID,
        access_token=access_token,
        session_id=session_id,
        callback_url=settings.CALLBACK_URL
    )
    client.subscribe_to_all_events()


@socketio.on('disconnect')
def disconnect():
    """Handle "disconnect" event.

    The signal is default and dispatched by client automatically."""
    session_id = request.sid
    if session_id in client_sessions:
        client_sessions.remove(session_id)


@app.route('/callback/<session_id>', methods=['POST', 'GET'])
def catch_callback(session_id):
    """Handle callbacks from Twitch Webhooks Hub.

    :param: session_id: Client connection (socket) session id.
    :type: session_id: str.
    """
    # It must be base on username - e.g. add session IDs after login somehow
    # 'hub.mode', 'denied'
    if 'hub.challenge' in request.args:
        return Response(request.args['hub.challenge'], status=200)
    if session_id not in client_sessions:
        return Response(status=404)
    current_time_str = dt.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    if 'hub.mode' in request.args and request.args['hub.mode'] == 'denied':
        message = 'Failed to sibscibe to topic: {}. Reason: {}'.format(
                request.args['hub.topic'], request.args['hub.reason'])
    else:
        message = request.data.decode()
        message = '{}: {}'.format(current_time_str, message)
    event_data = {'data': message}
    socketio.emit('event_updated', event_data, room=session_id)
    return Response(status=200)


if __name__ == '__main__':
    socketio.run(app, debug=True, port=5000)
