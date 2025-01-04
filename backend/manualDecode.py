# server.py
from flask import Flask, request, jsonify
from flask_cors import CORS
from flask_jwt_extended import JWTManager, create_access_token, jwt_required, get_jwt_identity, decode_token
from pythonLLM.LLM import get_response
from dotenv import load_dotenv
import os
import traceback

app = Flask(__name__)

load_dotenv()

jwt_key = os.getenv('JWT_SECRET_KEY')


# Configure database
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://chatbot_user:password@localhost/chatbot_db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['JWT_SECRET_KEY'] = jwt_key
app.config['JWT_TOKEN_LOCATION'] = ['headers']
app.config['JWT_HEADER_NAME'] = 'Authorization'
app.config['JWT_HEADER_TYPE'] = 'Bearer'

try:
    decoded = decode_token("eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJmcmVzaCI6ZmFsc2UsImlhdCI6MTczNTk4MzE2MCwianRpIjoiNjM0ODBiMzUtNDcyMC00ZjFmLWE0MWQtODQ5Yzc0NDkwMTQ5IiwidHlwZSI6ImFjY2VzcyIsInN1YiI6MSwibmJmIjoxNzM1OTgzMTYwLCJjc3JmIjoiMDIwMGFiNTgtN2I3MC00ODgxLTg5OTItYjg5YmIzNjllY2RiIiwiZXhwIjoxNzM1OTg0MDYwfQ.7BCUfZxyqBx5V4bdChEFq_CHCIM0lAAWQIsWvmr8Ci0")
    print(decoded)
except Exception as e:
    print(f"Invalid Token: {e}")
