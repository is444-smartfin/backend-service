import json
import logging
import os

import boto3
import jwt
import requests
from boto3.dynamodb.conditions import Key
from digibank import (ALGORITHMS, API_AUDIENCE, AUTH0_DOMAIN, AuthError, app,
                      get_token_auth_header, requires_auth, requires_scope)
from dotenv import load_dotenv
from flask import jsonify, request
from six.moves.urllib.request import urlopen

load_dotenv()
logger = logging.getLogger(__name__)

dynamodb = boto3.resource("dynamodb")


def url():
    return "https://tbankonline.com/SMUtBank_API/Gateway"

# See Auth0 userinfo for a sample JSON response


def get_user_info(token):
    response = requests.get(
        "https://smu-digibank.us.auth0.com/userinfo",
        headers={'Authorization': 'Bearer ' + token})
    user_info = response.json()
    return user_info

@app.route("/integrations/tbank/user_accounts", methods=['GET'])
@requires_auth
def tbank_list_user_accounts():
    # find out who's calling this endpoint
    token = get_token_auth_header()
    user_info = get_user_info(token)

    # then get POSTed form data
    data = request.get_json()

    # request for OTP
    serviceName = "getCustomerAccounts"
    userID = "goijiajian"
    PIN = "123456"
    OTP = "999999"

    header = {
        "Header": {
            "serviceName": serviceName,
            "userID": userID,
            "PIN": PIN,
            "OTP": OTP
        }
    }

    final_url = "{0}?Header={1}".format(url(), json.dumps(header))
    response = requests.post(final_url)
    print(final_url)

    serviceResp = response.json()['Content']['ServiceResponse']
    serviceRespHeader = serviceResp['ServiceRespHeader']
    errorCode = serviceRespHeader['GlobalErrorID']

    if errorCode == "010000":
        logger.info("{} successfully requested for their Accounts List".format(
            user_info['email']))
        accountsList = serviceResp['AccountList']['account']
        return jsonify({"status": 200, "data": accountsList})


    return jsonify({"status": 401, "message": "Unknown error."}), 401

    # if can login, we save it to our db, for now...
    # (not v secure... but tBank doesn't support OAuth)

    # post data to dynamodb
