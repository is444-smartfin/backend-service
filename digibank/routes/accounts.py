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


@app.route("/accounts/tbank/mfa", methods=['POST'])
@requires_auth
def accounts_tbank_mfa():
    # find out who's calling this endpoint
    token = get_token_auth_header()
    user_info = get_user_info(token)

    # then get POSTed form data
    data = request.get_json()

    # request for OTP
    serviceName = "requestOTP"
    userID = data['userId']
    PIN = data['pin']

    headerObj = {
        'Header': {
            'serviceName': serviceName,
            'userID': userID,
            'PIN': PIN,
        }
    }

    final_url = "{0}?Header={1}".format(url(), json.dumps(headerObj))
    response = requests.post(final_url)
    print(final_url)

    serviceRespHeader = response.json(
    )['Content']['ServiceResponse']['ServiceRespHeader']
    errorCode = serviceRespHeader['GlobalErrorID']

    if errorCode == "010000":
        logger.info("{} successfully requested for tBank MFA".format(
            user_info['email']))
        return jsonify({"status": 200, "message": "Your OTP has been sent to the mobile number registered to your tBank account."})

    elif errorCode == "010041":
        logger.error("{} triggered some unknown error in tBank MFA".format(
            user_info['email']))
        return jsonify({"status": 401, "message": "Idk what error is this"}), 401

    return jsonify({"status": 401, "message": "Invalid user ID or PIN, we're unable to send you your OTP."}), 401

    # if can login, we save it to our db, for now...
    # (not v secure... but tBank doesn't support OAuth)

    # post data to dynamodb


# Currently supports tBank only
@app.route("/accounts/tbank/link", methods=['POST'])
@requires_auth
def accounts_tbank_link():
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

    headerObj = {
        'Header': {
            'serviceName': serviceName,
            'userID': userID,
            'PIN': PIN,
            'OTP': OTP
        }
    }

    final_url = "{0}?Header={1}".format(url(), json.dumps(headerObj))
    response = requests.post(final_url)
    print(final_url)

    serviceRespHeader = response.json(
    )['Content']['ServiceResponse']['ServiceRespHeader']
    errorCode = serviceRespHeader['GlobalErrorID']

    if errorCode == "010000":
        LoginOTPAuthenticateResponseObj = response.json(
        )['Content']['ServiceResponse']['Login_OTP_Authenticate-Response']

        logger.info("{} successfully linked their tBank account. customerId {}, bankId {}".format(
            user_info['email'], LoginOTPAuthenticateResponseObj['CustomerID'], LoginOTPAuthenticateResponseObj['BankID']))

        # if can login, we save it to our db, for now...
        # (not v secure... but tBank doesn't support OAuth)

        # post data to dynamodb
        table = dynamodb.Table("users")
        response = table.update_item(
            Key={
                'email': user_info['email']
            },
            UpdateExpression="set #accounts = :account_info",
            ExpressionAttributeNames={
                '#accounts': 'accounts'
            },
            ExpressionAttributeValues={
                ':account_info': {
                    "tBank": {
                        "userId": userID,
                        "pin": PIN
                    }
                },
            },
            ReturnValues="UPDATED_NEW"
        )
        print(response)
        print("ok")

        return jsonify({"status": 200, "message": "Your tBank account is now linked to (idk what we're called haha)."})

    elif errorCode == "010041":
        logger.error("OTP has expired. You will receiving a SMS")

    return jsonify({"status": 401, "message": "Invalid user ID, PIN or OTP."}), 401


# TODO: fix inconsistent API url, no "tbank"
@app.route("/accounts/unlink", methods=['POST'])
@requires_auth
def accounts_tbank_unlink():
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


@app.route("/accounts/tbank/sync", methods=['GET'])
# @requires_auth
def accounts_tbank_sync():
    # then get data
    data = request.get_json()
    # post data to dynamodb

    # tbank
    serviceName = 'getTransactionHistory'
    userID = 'goijiajian'
    PIN = '123456'
    OTP = '999999'
    # Content
    accountID = '6624'
    startDate = '2020-08-01 00:00:00'
    endDate = '2020-10-10 00:00:00'
    numRecordsPerPage = '15'
    pageNum = '1'

    headerObj = {
        'Header': {
            'serviceName': serviceName,
            'userID': userID,
            'PIN': PIN,
            'OTP': OTP
        }
    }
    contentObj = {
        'Content': {
            'accountID': accountID,
            'startDate': startDate,
            'endDate': endDate,
            'numRecordsPerPage': numRecordsPerPage,
            'pageNum': pageNum
        }
    }
    final_url = "{0}?Header={1}&Content={2}".format(
        url(), json.dumps(headerObj), json.dumps(contentObj))
    response = requests.post(final_url)
    return response.json()
