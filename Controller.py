from Find_Commands_String import verify_query
from flask import Blueprint, jsonify, request
import glob
import os
import random
controller_api = Blueprint('controller_api', __name__)


@controller_api.route('/post_key/<query>', methods=['POST'])
def get_verify_query(query):
    # query = request.get_json()["quary"]
    result = verify_query(query)
    print(f"{os.path.dirname(os.path.abspath(__file__))}/{glob.glob('*.png')[0]}")
    result = random.sample('abcdefghijklmnopqrstuvxwyz', random.randint(5,20))
    print(result)
    return jsonify({"caminho" : f"{os.path.dirname(os.path.abspath(__file__))}/{glob.glob('*.png')[0]}", "execucao" : result}), 200
    # return "200"
