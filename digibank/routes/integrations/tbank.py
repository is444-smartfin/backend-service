import json
import logging
import os
import time
from datetime import datetime

import boto3
import jwt
import requests
from boto3.dynamodb.conditions import Key
from dateutil.relativedelta import relativedelta
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
    email = user_info['email']

    # Step 1: lookup database for tBank login details first
    table = dynamodb.Table("users")
    response = table.query(
        KeyConditionExpression=Key("email").eq(email)
    )
    accounts = response['Items'][0]['accounts']

    # Step 1a: check if tbank exists first
    if "tbank" not in accounts:
        return jsonify({"status": 404, "message": "No tBank account was found for the current user."}), 404

    # Step 2: prepare login details
    serviceName = "getCustomerAccounts"
    userID = accounts['tbank']['userId']
    PIN = accounts['tbank']['pin']
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


@app.route("/integrations/tbank/transaction_history", methods=['GET', 'POST'])
# @requires_auth
def tbank_transaction_history():
    # then get data
    data = request.get_json()
    # post data to dynamodb

    # tbank
    serviceName = "getTransactionHistory"
    userID = "goijiajian"
    PIN = "123456"
    OTP = "999999"
    # Content
    accountID = "6624"  # data['accountId']
    startDate = "2020-11-15T12:00:00"
    endDate = "2020-11-15T13:00:00"
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
            "user"))  # user_info['email']
        transactions = serviceResp['CDMTransactionDetail']['transaction_Detail']
        return jsonify({"status": 200, "data": transactions})

    return jsonify({"status": 401, "message": "Unknown error."}), 401


# Gets the MOST recent transaction with narrative that matches the keyword
@app.route("/integrations/tbank/lookup_transaction_history", methods=['GET', 'POST'])
# @requires_auth
def tbank_lookup_transaction_history():
    # then get data
    data = request.get_json()
    # post data to dynamodb

    keyword = "salary"  # get from data['keyword']

    # tbank
    serviceName = "getTransactionHistory"
    userID = "goijiajian"
    PIN = "123456"
    OTP = "999999"
    # Content
    accountID = "6624"  # data['accountId']
    startDate = "2020-11-14T20:00:00"  # hardcoded lulz
    endDate = "2020-11-15T13:00:00"
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
            "user"))  # user_info['email']
        transactions = serviceResp['CDMTransactionDetail']['transaction_Detail']

        # print(serviceResp['CDMTransactionDetail'])
        for txn in transactions:
            # from dbtt: text processing, strip spaces then lower them
            processed_narrative = txn['narrative'].replace(" ", "").lower()

            if keyword in processed_narrative:
                # print(keyword, processed_narrative)
                return jsonify({"status": 200, "data": txn})
        return jsonify({"status": 200, "message": "Unable to find transactions in the past 7 days with keyword {}".format(keyword)})
    return jsonify({"status": 401, "message": "Unknown error."}), 401


@app.route("/integrations/tbank/credit_transfer", methods=['POST'])
# @requires_auth
def tbank_credit_transfer():
    # find out who's calling this endpoint
    # token = get_token_auth_header()
    # user_info = get_user_info(token)

    # then get POSTed form data
    data = request.get_json()
    email = data['email']  # posted from recipe API endpoint

    # Step 1: get tBank account deets from DynamoDB
    table = dynamodb.Table("users")
    response = table.query(
        KeyConditionExpression=Key("email").eq(email)
    )
    logger.info("{} triggered credit transfer, found tBank UserID".format(email))
    accounts = response['Items'][0]['accounts']

    # Step 1a: check if tbank exists first
    if "tbank" not in accounts:
        return jsonify({"status": 404, "message": "No tBank account was found for the current user."}), 404

    # Step 2: prepare creditTransfer params
    serviceName = "creditTransfer"
    userID = accounts['tbank']['userId']  # get from DynamoDB using
    PIN = accounts['tbank']['pin']
    OTP = "999999"
    accountFrom = data['accountFrom']
    accountTo = data['accountTo']
    transactionAmount = data['amount']
    transactionReferenceNumber = data['transactionId']
    narrative = data['narrative']

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

    final_url = "{0}?Header={1}&Content={2}".format(
        url(), json.dumps(header), json.dumps(content))
    response = requests.post(final_url)
    print(final_url)

    serviceResp = response.json()['Content']['ServiceResponse']
    serviceRespHeader = serviceResp['ServiceRespHeader']
    errorCode = serviceRespHeader['GlobalErrorID']

    if errorCode == "010000":
        logger.info("{} successfully requested for their Accounts List".format(
            "user"))  # user_info['email']
        return jsonify({"status": 200, "data": serviceResp})

    return jsonify({"status": 401, "message": "Unhandled error."}), 401

    # if can login, we save it to our db, for now...
    # (not v secure... but tBank doesn't support OAuth)

    # post data to dynamodb


@app.route("/integrations/tbank/recipe_salary_transfer", methods=['POST'])
def tbank_recipe_salary_transfer():
    # get posted JSON data from AWS Lambda
    data = request.get_json()

    if data['apiKey'] != "randomKey":
        return jsonify({"status": 401, "message": "Unauthorised."}), 401

    eventId = data['eventId']
    payload = data['payload']

    email = payload['email']['S']
    taskName = payload['task_name']['S']

    # putting it here to save costs, since AWS Lambda will call this endpoint
    if taskName != "tbank.salary.transfer":
        return jsonify({"status": 403, "message": "Forbidden. Wrong task name provided."}), 403

    taskData = payload['data']['M']  # to
    taskSchedule = taskData['schedule']['S']
    amount = taskData['amount']['S']
    accountFrom = taskData['from']['S']
    accountTo = taskData['to']['S']

    # print(taskSchedule, amount, accountFrom, accountTo, email, taskName)
    creationTime = int(time.time())

    # use relative delta time, todo: find a way to format/parse schedule
    expirationTime = datetime.now() + relativedelta(minutes=+1)
    # convert to epoch, see https://stackoverflow.com/a/23004143/950462
    expirationTime = int(expirationTime.timestamp())

    # Let's continue...

    # First, find out transaction history using keyword search for "salary"
    response1 = requests.post(
        "https://api.ourfin.tech/integrations/tbank/lookup_transaction_history")
    txn = response1.json()
    salary = 0
    if "data" in txn:
        salary = float(txn['data']['transactionAmount'])
        logger.info("{} found an incoming salary transfer for task {} with amount SGD {}".format(
            email, taskName, salary))

    amountToTransfer = salary * (float(amount) / 100)  # calc % of salary
    logger.info("{} calculated amount to transfer, {}% of SGD {} is SGD {}".format(
        email, amount, salary, amountToTransfer))

    # Next, if can find, do a transfer of x% of that transaction's amount
    # response2 = requests.post("http://localhost:5000/integrations/tbank/credit_transfer", json={
    response2 = requests.post("https://api.ourfin.tech/integrations/tbank/credit_transfer", json={
        "transactionId": eventId,
        "email": email,
        "narrative": "Automated task by SmartFIN ({}, SGD {})".format("salary", salary),
        "accountFrom": accountFrom,
        "accountTo": accountTo,
        "amount": amountToTransfer,
    })
    logger.info("{} successfully completed {} {}".format(
        email, taskName, response2))

    loggingData = {}

    if "data" in txn:
        loggingData['transactionAmount'] = txn['data']['transactionAmount']
        loggingData['transactionID'] = txn['data']['transactionID']
        loggingData['narrative'] = txn['data']['narrative']

    # Finally, re-queue with the new expiration time (TTL) e.g. current time + 1 month
    # response3 = requests.post("http://localhost:5000/recipes/create/lambda", json={
    response3 = requests.post("https://api.ourfin.tech/recipes/create/lambda", json={
        "email": email,
        "taskName": taskName,
        "accountFrom": accountFrom,
        "accountTo": accountTo,
        "amount": amount,
        "creationTime": creationTime,
        "expirationTime": expirationTime,
        "taskSchedule": taskSchedule,
        "eventId": eventId,
        "loggingData": loggingData
        # to add in schedule
    })
    logger.info("{} requeued recurring DynamoDB TTL task through Lambda for {} {}".format(
        email, taskName, response3))

    return jsonify({"status": 200, "message": "OK"}), 200

# for unit testing only


@app.route("/integrations/tbank/transaction_history/test", methods=['GET'])
# @requires_auth
def tbank_transaction_history_test():
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
    endDate = "2020-12-31 00:00:00"
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
        logger.info("{} successfully requested for their Transaction History (Test Endpoint)".format(
            "user"))  # user_info['email']
        transactions = serviceResp['CDMTransactionDetail']['transaction_Detail']
        return jsonify({"status": 200, "data": transactions})

    return jsonify({"status": 401, "message": "Unknown error."}), 401
