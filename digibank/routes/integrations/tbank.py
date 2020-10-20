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
