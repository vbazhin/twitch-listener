"""Web application server module.

The server is responsible for exposing the web pages,
reading callbacks and dispatching subscripted events to clients.
"""

# Applying monkey-patch to allow sockets connection.
from gevent import monkey
monkey.patch_all()

from flask import (
    Flask, render_template,
    request, Response, redirect,
    session, url_for
)
from flask_socketio import SocketIO
import settings
from auth_client import AuthStaticClient
from subscribe_client import SubscriptionClient

app = Flask(__name__)
socketio = SocketIO(app)


# Store current client sessions ids, to verify session,
# before sending streamer's event callbacks.
# In production Redis storage (or some other k/v store) can be used.
client_sessions = set()


@app.route('/', methods=['GET'])
def show_landing():
    return render_template(
        'landing.html',
        auth_url=AuthStaticClient.get_auth_code_url()
    )


@app.route('/auth')
def get_token():
    if 'code' not in request.args:
        return Response(status=400)
    code = request.args['code']
    access_token = AuthStaticClient.get_access_token(code)
    session['access_token'] = access_token
    return redirect(url_for('streamer_form'))


@app.route('/enter_streamer', methods=['GET', 'POST'])
def streamer_form():
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
    streamer_name = session['streamer_name']
    return render_template(
        'stream.html',
        streamer_name=streamer_name
    )

@socketio.on('stream_connected')
def stream_connected_event(msg):
    session_id = request.sid
    client_sessions.add(session_id)
    streamer_name = session['streamer_name']
    access_token = session['access_token']
    client = SubscriptionClient(
        streamer_name=streamer_name,
        client_id=settings.CLIENT_ID,
        access_token=access_token,
        session_id=session_id
    )
    client.subscribe_to_all_events()

@socketio.on('disconnect')
def disconnect():
    """Handle "disconnect" event.

    The signal is default and dispatched by client automatically."""
    session_id = request.sid
    if session_id in client_sessions:
        client_sessions.remove(session_id)


if __name__ == '__main__':
    socketio.run(app, debug=True, port=5000)
