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

@app.route("/integrations/tbank/transaction_history", methods=['GET'])
# @requires_auth
def accounts_sync():
    # then get data
    data = request.get_json()
    # post data to dynamodb

    # tbank
    serviceName = "getTransactionHistory"
    userID = "goijiajian"
    PIN = "123456"
    OTP = "999999"
    # Content
    accountID = "6624"
    startDate = "2020-08-01 00:00:00"
    endDate = "2020-12-30 00:00:00"
    numRecordsPerPage = "15"
    pageNum = "1"

    header = {
        "Header": {
            "serviceName": serviceName,
            "userID": userID,
            "PIN": PIN,
            "OTP": OTP
        }
    }
    content = {
        "Content": {
            "accountID": accountID,
            "startDate": startDate,
            "endDate": endDate,
            "numRecordsPerPage": numRecordsPerPage,
            "pageNum": pageNum
        }
    }
    final_url = "{0}?Header={1}&Content={2}".format(
        url(), json.dumps(header), json.dumps(content))
    print(final_url)

    response = requests.post(final_url)
    serviceResp = response.json()['Content']['ServiceResponse']
    serviceRespHeader = serviceResp['ServiceRespHeader']
    errorCode = serviceRespHeader['GlobalErrorID']

    if errorCode == "010000":
        logger.info("{} successfully requested for their Transaction History".format(
            "user")) # user_info['email']
        transactions = serviceResp['CDMTransactionDetail']['transaction_Detail']
        return jsonify({"status": 200, "data": transactions})

    return jsonify({"status": 401, "message": "Unknown error."}), 401

    return response.json()


@app.route("/integrations/tbank/credit_transfer", methods=['GET'])
# @requires_auth
def tbank_credit_transfer():
    # find out who's calling this endpoint
    # token = get_token_auth_header()
    # user_info = get_user_info(token)

    # then get POSTed form data
    data = request.get_json()

    # then get tBank account deets from DynamoDB

    # request for OTP
    serviceName = "creditTransfer"
    userID = "goijiajian" # get from DynamoDB using
    accountFrom = "0000006624"
    accountTo = "0000006590"
    transactionAmount = "1.80"
    transactionReferenceNumber = "TRF5000"
    narrative = "Automatic Transfer via Smartly API"
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

    content = {
        "Content": {
            "accountFrom": accountFrom,
            "accountTo": accountTo,
            "transactionAmount": transactionAmount,
            "transactionReferenceNumber": transactionReferenceNumber,
            "narrative": narrative
        }
    }

    final_url = "{0}?Header={1}&Content={2}".format(url(), json.dumps(header), json.dumps(content))
    response = requests.post(final_url)
    print(final_url)

    serviceResp = response.json()['Content']['ServiceResponse']
    serviceRespHeader = serviceResp['ServiceRespHeader']
    errorCode = serviceRespHeader['GlobalErrorID']

    if errorCode == "010000":
        logger.info("{} successfully requested for their Accounts List".format(
            "user")) # user_info['email']
        return jsonify({"status": 200, "data": serviceResp})

    return jsonify({"status": 401, "message": "Unhandled error."}), 401

    # if can login, we save it to our db, for now...
    # (not v secure... but tBank doesn't support OAuth)

    # post data to dynamodb
