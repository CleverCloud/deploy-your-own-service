"""
Hello world example for addon dashboard panel provided by the add-on provider in Python
"""

import logging
import os

from flask import Flask, request
from flask_httpauth import HTTPTokenAuth

from hashlib import sha1

# Salt provided in the add-on manifest
ADDON_PROVIDER_SALT = os.getenv("ADDON_PROVIDER_SALT")

app = Flask(__name__)

auth_token = HTTPTokenAuth(scheme='Bearer')

logging.basicConfig(level=logging.DEBUG)

required_env = [ADDON_PROVIDER_SALT]
if None in required_env:
    raise Exception(
        'Missing Env Variable : {}'.format(' and '.join(required_env)))


# Based on the manifest salt and the returned timestamp. The hash must be computed and compared to
# the provided one
@auth_token.verify_token
def verify_token(arg):
    needed_arg = ['id', 'token', 'timestamp']
    for v in needed_arg:
        if v not in request.form:
            return False
    form_id = request.form['id']
    form_token = request.form['token']
    form_timestamp = request.form['timestamp']

    token = ':'.join([form_id, ADDON_PROVIDER_SALT, form_timestamp]).encode('utf-8')
    token = sha1(token).hexdigest()

    if not token == form_token:
        return False
    return True


# Provide a dashboard for the add-on
# The path is based on the provided `sso_url` from the manifest
@app.route('/', methods=['GET', 'POST'])
@auth_token.login_required
def hello_world():
    return "Hello World !!"


def main():
    app.run(host="0.0.0.0", port=8080)


if __name__ == '__main__':
    main()
