from Find_Commands_String import verify_query
from flask import Blueprint, jsonify, request

controller_api = Blueprint('controller_api', __name__)


@controller_api.route('/verify_query', methods=['POST'])
def get_verify_query():
    query = request.get_json()["quary"]
    result = verify_query(query)
    return jsonify(result), 200
