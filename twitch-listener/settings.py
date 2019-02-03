DEBUG = True

API_BASE_URL = 'https://api.twitch.tv/helix/'

if DEBUG:
    AUTH_REDIRECT_URI = 'http://127.0.0.1:5000/auth'
else:
    AUTH_REDIRECT_URL = '206.189.173.10:5000/auth'

CLIENT_ID = 'vvg1sdkexkza9ctnnqs9v12re2qxkl'

CLIENT_SECRET = 'wruq66igz3sqnb5kneim8kk0u5y8xo'

CALLBACK_URL = 'http://206.189.173.10:5000/callback'