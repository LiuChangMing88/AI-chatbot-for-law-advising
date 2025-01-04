# server.py
from flask import Flask, request, jsonify
from flask_cors import CORS
from flask_jwt_extended import JWTManager, create_access_token, jwt_required, get_jwt_identity
from pythonLLM.LLM import get_response
from dotenv import load_dotenv
import os
import traceback
import logging
from datetime import timedelta

app = Flask(__name__)
CORS(app)

load_dotenv()

jwt_key = os.getenv('JWT_SECRET_KEY')


app.config['DEBUG'] = True 
app.logger.setLevel(logging.INFO)

# Configure database
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://chatbot_user:password@localhost/chatbot_db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['JWT_SECRET_KEY'] = jwt_key
app.config['JWT_TOKEN_LOCATION'] = ['headers']
app.config['JWT_HEADER_NAME'] = 'Authorization'
app.config['JWT_HEADER_TYPE'] = 'Bearer'

# Set JWT expiration time
app.config['JWT_ACCESS_TOKEN_EXPIRES'] = timedelta(hours=2)  # Set token expiration to 1 hour

from models import db, bcrypt, User, ChatSession, ChatHistory

db.init_app(app)
jwt = JWTManager(app)

@jwt.unauthorized_loader
def unauthorized_callback(err_msg):
    print(f"Unauthorized error: {err_msg}")  # Log unauthorized errors
    return jsonify({"error": "Unauthorized access"}), 401

@jwt.invalid_token_loader
def invalid_token_callback(err_msg):
    print(f"Invalid token error: {err_msg}")  # Log invalid token errors
    return jsonify({"error": "Invalid token"}), 422

@app.route('/register', methods=['POST'])
def register():
    data = request.json
    email = data.get('email')
    username = data.get('username')
    password = data.get('password')

    hashed_password = bcrypt.generate_password_hash(password).decode('utf-8')
    new_user = User(email=email, password=hashed_password, username=username)
    db.session.add(new_user)
    db.session.commit()

    return jsonify({'message': 'User registered successfully'}), 201

@app.route('/login', methods=['POST'])
def login():
    data = request.json
    email = data.get('email')
    password = data.get('password')
    user = User.query.filter_by(email=email).first()
    if user and bcrypt.check_password_hash(user.password, password):
        access_token = create_access_token(identity=str(user.id))
        return jsonify({'access_token': access_token}), 200
    else:
        return jsonify({'message': 'Invalid credentials'}), 401

@app.route('/api/sessions', methods=['POST'])
@jwt_required()
def create_session():
    user_id = get_jwt_identity()
    data = request.json
    session_name = data.get('name')

    new_session = ChatSession(user_id=user_id, name=session_name)
    db.session.add(new_session)
    db.session.commit()

    return jsonify({'session_id': new_session.id, 'name': new_session.name}), 201

@app.route('/api/sessions', methods=['GET'])
@jwt_required()
def get_sessions():
    try:
        user_id = get_jwt_identity()
        sessions = ChatSession.query.filter_by(user_id=user_id).all()
        return jsonify([
            {'id': session.id, 'name': session.name, 'created_at': session.created_at.isoformat()}
            for session in sessions
        ]), 200
    except Exception as e:
        print(f"Error: {e}")
        return jsonify({'error': str(e)}), 422

@app.route('/api/chat', methods=['POST'])
@jwt_required()
def chat():
    try:
        user_id = get_jwt_identity()
        data = request.json
        session_id = data.get('session_id')
        messages = data.get('messages', [])
        
        msg = messages[-1]

        new_message = ChatHistory(session_id=session_id, role=msg['role'], content=msg['content'])
        db.session.add(new_message)
        db.session.commit()

        response = get_response(messages)
        ai_message = {'role': 'AI', 'content': response}

        # Save AI response to chat history
        new_message = ChatHistory(session_id=session_id, role='AI', content=response)
        db.session.add(new_message)
        db.session.commit()

        return jsonify({'response': response})
    except Exception as e:
        print(f"Error: {e}")
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500

@app.route('/api/history/<int:session_id>', methods=['GET'])
@jwt_required()
def history(session_id):
    user_id = get_jwt_identity()
    history = ChatHistory.query.filter_by(session_id=session_id).all()
    return jsonify([{'role': msg.role, 'content': msg.content, 'timestamp': msg.timestamp} for msg in history])

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(host='0.0.0.0', port=5000)