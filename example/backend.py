"""
Toy example of a add-on provider backend to highlight Clever Cloud add-on api usage and security
"""

import os
import logging

from flask import Flask, request, jsonify, make_response
from flask_httpauth import HTTPBasicAuth
from werkzeug.security import generate_password_hash, check_password_hash

import clever_client

# add-on ID and Password provided in the add-on manifest
ADDON_PROVIDER_ID = os.getenv("ADDON_PROVIDER_ID")
ADDON_PROVIDER_PWD = os.getenv("ADDON_PROVIDER_PWD")

app = Flask(__name__)

auth_basic = HTTPBasicAuth()

logging.basicConfig(level=logging.DEBUG)

required_env = [ADDON_PROVIDER_ID, ADDON_PROVIDER_PWD]
if None in required_env:
    raise Exception(
        'Missing Env Variable : {}'.format(' and '.join(required_env)))

addon_ids = {
    ADDON_PROVIDER_ID: generate_password_hash(ADDON_PROVIDER_PWD)
}

# used Clever Cloud CLI based quickly made for the example python client
clever_cli = clever_client.CleverCloud()


# The auth is done by a basic auth. It is based on the ID field and the password field from the
# manifest
@auth_basic.verify_password
def verify_password(addon_id, password):
    if addon_id in addon_ids and \
            check_password_hash(addon_ids.get(addon_id), password):
        return addon_id


# The path is based on the provided `base_url` from the manifest
# A POST method is used to subscribe to the services. Here we create a new dedicated Python
# application.
# One env variable is returned and available for user
@app.route('/addon_management', methods=['POST'])
@auth_basic.login_required
def addon_provisioning():
    logging.debug('Provisioning')
    data = request.json
    addon_id = data["addon_id"]
    owner_id = data["owner_id"]

    ret = clever_cli.create_application(app_name=addon_id, organisation=owner_id, app_type="python")

    if ret is None:
        logging.error('Unable to provisionne application')
        return make_response('Unable to provisionne application', 500)

    response = {
        "id": ret["app_id"],
        "config": {
            "test_env_var": "test_env_value"
        },
        "message": "Great Job !"
    }

    return make_response(jsonify(response), 200)


# The DELETE methode ond the `base_url/<addon-id>` is used to delete the add-on or unsubscribe from
# the service. Here we remove the previously created application
@app.route('/addon_management/<addon_id>', methods=['DELETE'])
@auth_basic.login_required
def delete_addon(addon_id):
    logging.debug("deprovisioning")
    logging.debug("addon id : %s" % addon_id)

    ret = clever_cli.delete_application(addon_id)
    if not ret:
        logging.error("Unable to remove addon or application !")
        return make_response('Unable to remove addon or application !', 500)

    return make_response('success', 200)


def main():
    app.run(host="0.0.0.0", port=8080)


if __name__ == '__main__':
    main()
