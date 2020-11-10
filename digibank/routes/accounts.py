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


@app.route("/accounts/info", methods=['GET'])
@requires_auth
def accounts_info():
    # find out who's calling this endpoint
    token = get_token_auth_header()
    user_info = get_user_info(token)
    email = user_info['email']

    logger.info(
        "{} has attempted to retrieve their Bank Accounts info".format(email))

    table = dynamodb.Table("users")
    response = table.query(
        KeyConditionExpression=Key("email").eq(email)
    )

    return response['Items'][0]

# Currently supports tBank only
# Request for Multi-factor Auth e.g. OTP


@app.route("/accounts/mfa", methods=['POST'])
@requires_auth
def accounts_mfa():
    # find out who's calling this endpoint
    token = get_token_auth_header()
    user_info = get_user_info(token)

    # then get POSTed form data
    data = request.get_json()

    # request for OTP
    serviceName = "requestOTP"
    userID = data['userId']
    PIN = data['pin']

    header = {
        "Header": {
            "serviceName": serviceName,
            "userID": userID,
            "PIN": PIN,
        }
    }

    final_url = "{0}?Header={1}".format(url(), json.dumps(header))
    response = requests.post(final_url)
    print(final_url)

    serviceRespHeader = response.json(
    )['Content']['ServiceResponse']['ServiceRespHeader']
    errorCode = serviceRespHeader['GlobalErrorID']

    if errorCode == "010000":
        logger.info("{} successfully requested for Multi-Factor Authentication".format(
            user_info['email']))
        return jsonify({"status": 200, "message": "Your OTP has been sent to the mobile number registered to your bank account."})

    elif errorCode == "010041":
        logger.error("{} triggered some unknown error in Multi-Factor Authentication".format(
            user_info['email']))
        return jsonify({"status": 401, "message": "Idk what error is this"}), 401

    return jsonify({"status": 401, "message": "Invalid user ID or PIN, we're unable to send you your OTP."}), 401

    # if can login, we save it to our db, for now...
    # (not v secure... but tBank doesn't support OAuth)

    # post data to dynamodb


@app.route("/accounts/link", methods=['POST'])
@requires_auth
def accounts_link():
    # find out who's calling this endpoint
    token = get_token_auth_header()
    user_info = get_user_info(token)

    # then get POSTed form data
    data = request.get_json()

    # verify with tBank's loginCustomer service, make sure we can login
    serviceName = "loginCustomer"
    userID = data['userId']
    PIN = data['pin']
    OTP = data['otp']
    bank = data['bank']  # get bank name e.g. tbank, ocbc, dbs

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

    serviceRespHeader = response.json(
    )['Content']['ServiceResponse']['ServiceRespHeader']
    errorCode = serviceRespHeader['GlobalErrorID']

    if errorCode == "010000":
        LoginOTPAuthenticateResponseObj = response.json(
        )['Content']['ServiceResponse']['Login_OTP_Authenticate-Response']

        logger.info("{} successfully linked their bank account. customerId {}, bankId {}, bank {}".format(
            user_info['email'], LoginOTPAuthenticateResponseObj['CustomerID'], LoginOTPAuthenticateResponseObj['BankID'], bank))

        # if can login, we save it to our db, for now...
        # (not v secure... but tBank doesn't support OAuth)

        # post data to dynamodb
        table = dynamodb.Table("users")
        # TODO add multiple
        response = table.update_item(
            Key={
                'email': user_info['email']
            },
            UpdateExpression="set #accounts.#bankName = :account_info",
            ExpressionAttributeNames={
                '#accounts': 'accounts',
                '#bankName': bank
            },
            ExpressionAttributeValues={
                ':account_info': {
                    "userId": userID,
                    "pin": PIN
                },
            },
            ReturnValues="UPDATED_NEW"
        )
        print(response)
        print("ok")

        return jsonify({"status": 200, "message": "Your bank account is now linked to SmartFIN."})

    elif errorCode == "010041":
        logger.error("OTP has expired. You will receiving a SMS")

    logger.info("{} failed to linked their bank account. bank {}".format(
        user_info['email'], bank))
    return jsonify({"status": 401, "message": "Invalid user ID, PIN or OTP."}), 401


# TODO: fix inconsistent API url, no "tbank"
@app.route("/accounts/unlink", methods=['POST'])
@requires_auth
def accounts_unlink():
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
