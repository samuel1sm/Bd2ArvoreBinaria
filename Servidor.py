from flask import Flask
from flask_cors import CORS
from flask_restful import Api

from Controller import controller_api

app = Flask(__name__)
api = Api(app)
CORS(app)
app.register_blueprint(controller_api)

if __name__ == '__main__':
    app.run(port=5000, host="localhost")
