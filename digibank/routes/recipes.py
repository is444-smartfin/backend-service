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

def get_user_info(token):
    response = requests.get(
        "https://smu-digibank.us.auth0.com/userinfo",
        headers={'Authorization': 'Bearer ' + token})
    user_info = response.json()
    return user_info

@app.route("/recipes/create", methods=['POST'])
@requires_auth
def recipes_create():
    # find out who's calling this endpoint
    token = get_token_auth_header()
    user_info = get_user_info(token)

    # then get POSTed form data
    data = request.get_json()

    table = dynamodb.Table("users")
    response = table.update_item(
        Key={
            'email': user_info['email']
        },
        UpdateExpression="remove #accounts.#bank",
        ExpressionAttributeNames={
            '#accounts': 'accounts',
            '#bank': data['name']
        },
        ReturnValues="ALL_NEW"
    )
    print(response)
    return jsonify({"status": 200, "message": "OK"}), 200
