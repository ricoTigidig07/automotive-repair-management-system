from flask import request, jsonify, current_app
from app import db
from app.models.user import User

def register_api_routes(app):
    
    @app.route('/api/auth/register', methods=['POST'])
    def register():
        try:
            data = request.get_json()
            
            username = data.get('username')
            email = data.get('email')
            password = data.get('password')
            
            if not username or not email or not password:
                return jsonify({'success': False, 'message': 'All fields required'}), 400
            
            if User.find_by_username(username):
                return jsonify({'success': False, 'message': 'Username exists'}), 400
            
            if email and User.find_by_email(email):
                return jsonify({'success': False, 'message': 'Email exists'}), 400
            
            user = User(username=username, email=email, is_active=True)
            user.set_password(password)
            
            db.session.add(user)
            db.session.commit()
            
            return jsonify({'success': True, 'message': 'User created', 'user_id': user.user_id}), 201
            
        except Exception as e:
            db.session.rollback()
            return jsonify({'success': False, 'message': str(e)}), 500
    
    @app.route('/api/auth/login', methods=['POST'])
    def login():
        try:
            data = request.get_json()
            
            username = data.get('username')
            password = data.get('password')
            
            if not username or not password:
                return jsonify({'success': False, 'message': 'Username and password required'}), 400
            
            user = User.find_by_username(username)
            
            if not user or not user.is_active or not user.check_password(password):
                return jsonify({'success': False, 'message': 'Invalid credentials'}), 401
            
            user.update_last_login()
            
            return jsonify({'success': True, 'message': 'Login successful', 'user_id': user.user_id, 'username': user.username}), 200
            
        except Exception as e:
            return jsonify({'success': False, 'message': str(e)}), 500