import json
import logging
import os
import time

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

# tbank salary create


@app.route("/recipes/create/lambda", methods=['POST'])
# @requires_auth
def recipes_create_lambda():
    # get POSTed form data
    data = request.get_json()

    # TODO: auth check

    email = data['email']
    taskName = data['taskName']
    accountFrom = data['accountFrom']
    accountTo = data['accountTo']
    amount = data['amount']

    table = dynamodb.Table("scheduled_tasks")
    response = table.update_item(
        Key={
            'email': data
        },
        UpdateExpression="set #task_name = :task_name, #data = :data, #creation = :creation, #expiration = :expiration",
        ExpressionAttributeNames={
            '#task_name': 'task_name',
            '#data': 'data',
            '#creation': 'creation_time',
            '#expiration': 'expiration_time' # this has DynamoDB's TTL attribute
        },
        ExpressionAttributeValues={
            ':task_name': taskName,
            ':data': {
                'from': accountFrom,
                'to': accountTo,
                'amount': amount,
                'schedule': 'every month'
            },
            ':creation': int(creationTime),
            ':expiration': int(expirationTime)
        },
        ReturnValues="ALL_NEW"
    )
    print(response)
    return jsonify({"status": 200, "message": "OK"}), 200


@app.route("/recipes/create/init", methods=['GET'])
# @requires_auth
def recipes_create_init():
    # find out who's calling this endpoint
    # token = get_token_auth_header()
    # user_info = get_user_info(token)

    # then get POSTed form data
    data = request.get_json()

    table = dynamodb.Table("scheduled_tasks")
    response = table.update_item(
        Key={
            'email': 'jiajiannn@gmail.com' #user_info['email']
        },
        UpdateExpression="set #task_name = :task_name, #data = :data, #creation = :creation, #expiration = :expiration",
        ExpressionAttributeNames={
            '#task_name': 'task_name',
            '#data': 'data',
            '#creation': 'creation_time',
            '#expiration': 'expiration_time' # this has DynamoDB's TTL attribute
        },
        ExpressionAttributeValues={
            ':task_name': 'tbank.salary.transfer',
            ':data': {
                'from': '6624',
                'to': '6590',
                'amount': '1.88',
                'schedule': 'every month'
            },
            ':creation': int(time.time() // 60 * 60),
            ':expiration': int(time.time() // 60 * 60) + 10
        },
        ReturnValues="ALL_NEW"
    )
    print(response)
    return jsonify({"status": 200, "message": "OK"}), 200
