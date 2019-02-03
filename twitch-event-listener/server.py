"""Web application server module.

The server is responsible for exposing the web pages,
reading callbacks and dispatching subscripted events to clients.
"""

from flask import (
    Flask, render_template,
    request, Response, redirect,
    session, url_for
)
from flask_socketio import SocketIO
from auth_client import AuthStaticClient


app = Flask(__name__)
socketio = SocketIO(app)


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


if __name__ == '__main__':
    socketio.run(app, debug=True, port=5000)

