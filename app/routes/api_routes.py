import requests
from flask import request, jsonify, current_app, flash, redirect, url_for

API_URL = "http://localhost:5001"

def register_api_routes(app):
    
    @app.route('/api/auth/register', methods=['POST'])
    def register():
        try:
            response = requests.post(f"{API_URL}/api/auth/register", json=request.get_json(), timeout=5)
            return jsonify(response.json()), response.status_code
        except requests.exceptions.ConnectionError:
            return jsonify({'success': False, 'message': 'API service unavailable'}), 503
    
    @app.route('/api/auth/login', methods=['POST'])
    def login():
        try:
            response = requests.post(f"{API_URL}/api/auth/login", json=request.get_json(), timeout=5)
            return jsonify(response.json()), response.status_code
        except requests.exceptions.ConnectionError:
            return jsonify({'success': False, 'message': 'API service unavailable'}), 503
    
    @app.route('/api/parts', methods=['GET'])
    def get_parts():
        try:
            response = requests.get(f"{API_URL}/api/parts", params=request.args, timeout=5)
            return jsonify(response.json()), response.status_code
        except requests.exceptions.ConnectionError:
            return jsonify({'success': False, 'message': 'API service unavailable'}), 503
    
    @app.route('/api/parts', methods=['POST'])
    def create_part():
        try:
            response = requests.post(f"{API_URL}/api/parts", json=request.get_json(), timeout=5)
            return jsonify(response.json()), response.status_code
        except requests.exceptions.ConnectionError:
            return jsonify({'success': False, 'message': 'API service unavailable'}), 503
    
    @app.route('/api/parts/<int:part_id>', methods=['PUT'])
    def update_part(part_id):
        try:
            response = requests.put(f"{API_URL}/api/parts/{part_id}", json=request.get_json(), timeout=5)
            return jsonify(response.json()), response.status_code
        except requests.exceptions.ConnectionError:
            return jsonify({'success': False, 'message': 'API service unavailable'}), 503
    
    @app.route('/api/parts/<int:part_id>', methods=['DELETE'])
    def delete_part(part_id):
        try:
            response = requests.delete(f"{API_URL}/api/parts/{part_id}", timeout=5)
            return jsonify(response.json()), response.status_code
        except requests.exceptions.ConnectionError:
            return jsonify({'success': False, 'message': 'API service unavailable'}), 503