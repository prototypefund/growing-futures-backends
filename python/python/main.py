# Standard library imports
import os
import json
import base64
from datetime import datetime

# Third party imports
from flask import Flask, request, abort, send_file, make_response
from m5dbconnect import Connector
import error_codes
import pytz

# Local application imports
import delivery_tools

# local imports
# vendored dependencies


app = Flask(__name__, static_url_path='', static_folder='data')

SCHEMA_DIR = 'schemas'
DATA_SCHEMAS = SCHEMA_DIR + '/dataSchemas.json'

with open(DATA_SCHEMAS) as json_file:
    master_schema = json.load(json_file)


class cors(object):
    def __init__(self, methods: list):
        self.methods = methods

    def __call__(self, func):
        def func_wrapper(*args):

            if request.method == 'OPTIONS':
                print("sending cors request")
                return cors_request()

            if request.method not in self.methods:
                return abort(405)

            return func(*args)
        func_wrapper.__name__ = func.__name__
        return func_wrapper


@app.route("/schema", methods=['OPTIONS', 'POST'])
@cors(methods=['OPTIONS', 'POST'])
def getSchema():
    if not request.json or len(request.json) < 1:
        abort(400, "Bad request: code 100")
    schemaName = request.json['schemaName']
    print(master_schema)
    schemas = [schema for schema in master_schema
               if schema['schemaName'] == schemaName]
    if len(schemas) < 1:
        print(schemas)
        error = "No schema " + schemaName +\
                ": code " + error_codes.NO_SUCH_SCHEMA
        abort(400, error)

    if len(schemas) > 1:
        print(schemas)
        error = "Too many schemas " + schemaName +\
                ": code " + error_codes.TOO_MANY_SCHEMAS
        abort(500, error)

    filename = schemas[0]['schemaUrl'] + '.json'
    path = SCHEMA_DIR + "/" + filename
    response = make_response(send_file(path, attachment_filename=filename))
    response.headers = cors_request_header('application/json')
    print(response.headers)
    return response


@app.route("/master-schema", methods=['OPTIONS', 'GET'])
@cors(methods=['OPTIONS', 'GET'])
def getMasterSchema():
    j = json.dumps(master_schema)
    header = cors_request_header('application/json')
    return (j, 200, header)


@app.route("/retrieve", methods=['OPTIONS', 'POST'])
@cors(methods=['OPTIONS', 'POST'])
def getCollection():
    if not request.json or len(request.json) < 1:
        abort(400, "Bad request: code 100")

    collection = request.json['collection']
    mgr = get_manager(collection)
    return (mgr.data_as_json_list(), 200,
            cors_request_header('application/json'))


@app.route("/save", methods=['OPTIONS', 'POST'])
@cors(methods=['OPTIONS', 'POST'])
def saveOrUpdate():
    if len(request.json) < 1:
        abort(400, "Bad request: code 100")

    collection, data = extract_data(request.json)

    mgr = get_manager(collection)
    mgr.save_or_update("uid", data)
    return ("successfully saved", 200, cors_request_header('text/plain'))


@app.route("/save-all", methods=['OPTIONS', 'POST'])
@cors(methods=['OPTIONS', 'POST'])
def saveOrUpdateAll():
    if len(request.json) < 1:
        abort(400, "Bad request: code 100")

    collection, datas = extract_data(request.json)

    mgr = get_manager(collection)
    [mgr.save_or_update("uid", data) for data in datas]
    return ("successfully saved", 200, cors_request_header('text/plain'))


def extract_data(json):
    json = request.json
    collection = json['schemaName']
    data = json['data']
    return collection, data


@app.route("/delete", methods=['OPTIONS', 'POST'])
@cors(methods=['OPTIONS', 'POST'])
def delete():
    if len(request.json) < 1:
        abort(400, "Bad request: code 100")

    collection, data = extract_data(request.json)
    mgr = get_manager(collection)
    mgr.delete(data, "uid")
    return ("successfully deleted", 200, cors_request_header('text/plain'))


@app.route("/get-recent-deliveries", methods=['OPTIONS', 'POST'])
@cors(methods=['OPTIONS', 'POST'])
def get_deliveries():
    user_id = request.json['uid']

    mgr = get_manager('deliveries')
    all_deliveries = mgr.data_as_list()

    naive_current_date = datetime.now()
    current_date = pytz.utc.localize(naive_current_date)

    deliveries = delivery_tools.get_recent_deliveries(current_date, all_deliveries, user_id)
    return (json.dumps(deliveries), 200, cors_request_header('application/json'))


@app.route("/get-household-info", methods=['OPTIONS', 'POST'])
@cors(methods=['OPTIONS', 'POST'])
def get_household_info():
    user_id = request.json['userId']
    poll_id = request.json['pollId']

    result_manager = get_manager('poll-results')
    found_item = result_manager.find_one({'uid': user_id + '-' + poll_id})

    if found_item:
        return (json.dumps(found_item['household']), 200, cors_request_header('application/json'))
    else:
        return ({}, 200, cors_request_header('application/json'))


@app.route("/get-poll-questions", methods=['OPTIONS', 'POST'])
@cors(methods=['OPTIONS', 'POST'])
def get_poll_questions():
    user_id = request.json['userId']
    poll_id = request.json['pollId']

    mgr = get_manager('poll')
    poll_data = mgr.data_as_list()
    if (len(poll_data) > 0):
        original_poll=poll_data[0]
    else:
        return {}

    result_manager = get_manager('poll-results')
    found_item = result_manager.find_one({'uid': user_id + '-' + poll_id})

    try:
        found_item['collectData'] = original_poll['collectData']
    except:
        pass

    if found_item:
        return (json.dumps(found_item['poll']), 200, cors_request_header('application/json'))

    mgr = get_manager('poll')
    poll_data = mgr.data_as_list()

    return (original_poll, 200, cors_request_header('application/json'))

@app.route("/save-poll", methods=['OPTIONS', 'POST'])
@cors(methods=['OPTIONS', 'POST'])
def save_poll():
    if len(request.json) < 1:
            abort(400, "Bad request: code 100")

    print(request.json)
    mgr = get_manager('poll-results')
    mgr.save_or_update("uid", request.json)
    return ("successfully saved", 200, cors_request_header('text/plain'))


@app.route("/individual-share", methods=['OPTIONS', 'GET'])
@cors(methods=['OPTIONS', 'GET'])
def individual_share():
    userManager = get_manager('users')
    pollManager = get_manager('poll-results')

    users = userManager.data_as_list()
    polls = pollManager.data_as_list()

    ret_list = []
    for user in users:
        for poll in polls:
            if poll['user']['uid'] == user['uid']:
                user_data = {"uid": user['uid'],
                             "household": poll['household'],
                             "preferences": extractPreferences(poll['poll'])}
                retlist.append(item)
                break

def extractPreferences(poll):
    ret_list = []
    products = poll['products']
    for key in products.keys():
        print(products[key])
        if products[key]['category']['includeInPoll']:
            for product in category[key]:
                try:
                    ret_list.append({'product': product['uid'],
                                     'value': product['amount']})
                except KeyError:
                    try:
                        ret_list.append({'product': product['uid'],
                                         'value': category['category']['amount']})
                    except KeyError:
                        ret_list.append({'product': product['uid'],
                                         'value': 2})



@app.route("/get-next-delivery", methods=['OPTIONS', 'POST'])
@cors(methods=['OPTIONS', 'POST'])
def get_next_delivery():
    user_id = request.json['uid']
    print(user_id)

    mgr = get_manager('deliveries')
    naive_current_date = datetime.now()
    current_date = pytz.utc.localize(naive_current_date)
    all_deliveries = mgr.data_as_list()

    deliveries = delivery_tools.get_next_deliveries(current_date, all_deliveries, user_id)
    try:
        return (json.dumps(deliveries[0]), 200, cors_request_header('application/json'))
    except:
        return ("", 200, cors_request_header('application/json'))


@app.route("/login-member", methods=['OPTIONS', 'GET'])
@cors(methods=['OPTIONS', 'GET'])
def login_member():
    mgr = get_manager('users')
    try:
        auth = request.headers['Authorization']
    except KeyError:
        return ("Basic access authentication required", 400, cors_request_header('text/plain'))

    if auth:
        split_auth = auth.split()

    if split_auth[0] == "Basic":
        if split_auth[1]:
            decoded = base64.b64decode(split_auth[1])
            username, pwd = decoded.decode("utf-8").split(":")
            data = mgr.data_as_list() 
            found = [elt for elt in data if elt['username'] == username]
            if len(found) == 1:
                return (json.dumps(found[0]), 200, cors_request_header('application/json'))
            elif len(found) == 0:
                return ("unauthorized", 401, cors_request_header('text/plain'))
            else:
                return ("please contact your administrator", 400, cors_request_header('text/plain'))
        else:
            return ("Please provide username and password", 400, cors_request_header('text/plain'))
    else:
        return ("Basic access authentication required", 400, cors_request_header('text/plain'))

def get_manager(collection):
    return Connector.Connector(collection,
                               os.environ['DB_USER'],
                               os.environ['DB_PWD'],
                               os.environ['DB_HOST'],
                               os.environ['MONGO_DB'])


def cors_request_header(content_type):
    return {
             'Content-Type': content_type,
             'Access-Control-Allow-Origin': '*',
             'Access-Control-Allow-Headers': 'Content-Type',
            }


def cors_request():
    headers = {
            'Access-Control-Allow-Origin': '*',
            'Access-Control-Allow-Methods': 'POST,GET,OPTIONS,PUT,DELETE',
            'Access-Control-Allow-Headers': 'Accept, Content-Type,\
                                             Content-Length, Accept-Encoding,\
                                             X-CSRF-Token, Authorization,\
                                             X-Secret-Header, X-Auth, X-Email',
            'Access-Control-Max-Age': '3600'
            }

    return ('', 204, headers)


if __name__ == "__main__":
    app.run(debug=True, host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))
