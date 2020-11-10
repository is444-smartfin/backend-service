import json
import logging
import os
import time
import ast  # for ddb types
import decimal
import pytz
import uuid
from datetime import datetime

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


class DecimalEncoder(json.JSONEncoder):
    def default(self, o):
        if isinstance(o, decimal.Decimal):
            if o % 1 > 0:
                return float(o)
            else:
                return int(o)
        return super(DecimalEncoder, self).default(o)


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

    if taskName == "tbank.salary.transfer":
        accountFrom = data['accountFrom']
        accountTo = data['accountTo']
        amount = data['amount']
        creationTime = data['creationTime']
        expirationTime = data['expirationTime']

        table = dynamodb.Table("scheduled_tasks")
        response = table.update_item(
            Key={
                'email': email,
                'task_name': taskName,
            },
            UpdateExpression="set #data = :data, #creation = :creation, #expiration = :expiration",
            ExpressionAttributeNames={
                '#data': 'data',
                '#creation': 'creation_time',
                '#expiration': 'expiration_time'  # this has DynamoDB's TTL attribute
            },
            ExpressionAttributeValues={
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
    elif taskName == "smartfin.aggregated_email":
        creationTime = data['creationTime']
        expirationTime = data['expirationTime']

        table = dynamodb.Table("scheduled_tasks")
        response = table.update_item(
            Key={
                'email': email,
                'task_name': taskName,
            },
            UpdateExpression="set #data = :data, #creation = :creation, #expiration = :expiration",
            ExpressionAttributeNames={
                '#data': 'data',
                '#creation': 'creation_time',
                '#expiration': 'expiration_time'  # this has DynamoDB's TTL attribute
            },
            ExpressionAttributeValues={
                ':data': {
                    'schedule': 'every week'
                },
                ':creation': int(creationTime),
                ':expiration': int(expirationTime)
            },
            ReturnValues="ALL_NEW"
        )
        print(response)


    # Keep track of task run history
    table2 = dynamodb.Table("scheduled_tasks_history")
    table2.update_item(
            Key={
                'email': email,
                'id': uuid.uuid4(),
            },
            UpdateExpression="set #data = :data, #runTime = :runTime",
            ExpressionAttributeNames={
                '#data': 'data',
                '#runTime': 'run_time',
            },
            ExpressionAttributeValues={
                ':data': {
                    'lambda_info': 'TODO'
                },
                ':runTime': int(creationTime),
            },
            ReturnValues="ALL_NEW"
        )

    return jsonify({"status": 200, "message": "OK"}), 200


@app.route("/recipes/create", methods=['POST'])
@requires_auth
def recipes_create():
    # find out who's calling this endpoint
    token = get_token_auth_header()
    user_info = get_user_info(token)

    # then get POSTed form data
    data = request.get_json()
    taskName = data['taskName']

    table = dynamodb.Table("scheduled_tasks")

    if taskName == "tbank.salary.transfer":
        response = table.update_item(
            Key={
                'email': user_info['email'],
                'task_name': 'tbank.salary.transfer',
            },
            UpdateExpression="set #data = :data, #creation = :creation, #expiration = :expiration",
            ExpressionAttributeNames={
                '#data': 'data',
                '#creation': 'creation_time',
                '#expiration': 'expiration_time'  # this has DynamoDB's TTL attribute
            },
            ExpressionAttributeValues={
                ':data': {
                    'from': data['accountFrom'],
                    'to': data['accountTo'],
                    'amount': data['amount'],
                    'schedule': 'every month'
                },
                ':creation': int(time.time()),
                ':expiration': int(time.time()) + 60*5  # 1 week is 3600*24*7
            },
            ReturnValues="ALL_NEW"
        )
    elif taskName == "smartfin.aggregated_email":
        response = table.update_item(
            Key={
                'email': user_info['email'],
                'task_name': 'smartfin.aggregated_email',
            },
            UpdateExpression="set #data = :data, #creation = :creation, #expiration = :expiration",
            ExpressionAttributeNames={
                '#data': 'data',
                '#creation': 'creation_time',
                '#expiration': 'expiration_time'  # this has DynamoDB's TTL attribute
            },
            ExpressionAttributeValues={
                ':data': {
                    'schedule': 'every week'
                },
                ':creation': int(time.time()),
                ':expiration': int(time.time()) + 60*5  # 1 week is 3600*24*7
            },
            ReturnValues="ALL_NEW"
        )
    print(response)
    return jsonify({"status": 200, "message": "OK"}), 200


@app.route("/recipes/list", methods=['POST'])
@requires_auth
def recipes_list():
    # find out who's calling this endpoint
    token = get_token_auth_header()
    user_info = get_user_info(token)
    email = user_info['email']

    # then get POSTed form data
    table = dynamodb.Table("scheduled_tasks")
    response = table.query(
        KeyConditionExpression=Key("email").eq(email)
    )
    data = []
    tz = pytz.timezone("Asia/Singapore")

    for i in response['Items']:
        tmp = ast.literal_eval((json.dumps(i, cls=DecimalEncoder)))
        tmp['creation_time'] = datetime.fromtimestamp(
            tmp['creation_time'], tz).isoformat()
        tmp['expiration_time'] = datetime.fromtimestamp(
            tmp['expiration_time'], tz).isoformat()

        data.append(tmp)

    return jsonify({"status": 200, "data": data}), 200
