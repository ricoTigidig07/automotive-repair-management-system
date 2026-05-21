import requests
from flask import request, jsonify, current_app

API_URL = "http://localhost:5001"

def register_api_routes(app):
    
    @app.route('/api/auth/register', methods=['POST'])
    def register():
        response = requests.post(f"{API_URL}/api/auth/register", json=request.get_json())
        return jsonify(response.json()), response.status_code
    
    @app.route('/api/auth/login', methods=['POST'])
    def login():
        response = requests.post(f"{API_URL}/api/auth/login", json=request.get_json())
        return jsonify(response.json()), response.status_code
    
    @app.route('/api/parts', methods=['GET'])
    def get_parts():
        response = requests.get(f"{API_URL}/api/parts", params=request.args)
        return jsonify(response.json()), response.status_code
    
    @app.route('/api/parts', methods=['POST'])
    def create_part():
        response = requests.post(f"{API_URL}/api/parts", json=request.get_json())
        return jsonify(response.json()), response.status_code
    
    @app.route('/api/parts/<int:part_id>', methods=['PUT'])
    def update_part(part_id):
        response = requests.put(f"{API_URL}/api/parts/{part_id}", json=request.get_json())
        return jsonify(response.json()), response.status_code
    
    @app.route('/api/parts/<int:part_id>', methods=['DELETE'])
    def delete_part(part_id):
        response = requests.delete(f"{API_URL}/api/parts/{part_id}")
        return jsonify(response.json()), response.status_code