"""
REST API endpoints for desktop client integration
"""
from flask import Blueprint, jsonify, request, session
from app.models.part import Part
from app.models.inventory import Inventory
from app.extensions import db
import logging

api_bp = Blueprint('api', __name__)
logger = logging.getLogger(__name__)

@api_bp.route('/api/parts', methods=['GET'])
def get_parts():
    try:
        tenant_id = request.args.get('tenant_id', 1, type=int)
        parts = Part.query.filter_by(tenant_id=tenant_id, is_active=True).all()
        return jsonify({
            'success': True,
            'parts': [{
                'part_id': p.part_id,
                'part_name': p.part_name,
                'cost': float(p.cost),
                'sku': p.sku,
                'category': p.category,
                'supplier': p.supplier,
                'is_active': p.is_active
            } for p in parts]
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@api_bp.route('/api/parts/<int:part_id>', methods=['GET'])
def get_part(part_id):
    try:
        part = Part.find_by_id(part_id)
        if not part:
            return jsonify({'success': False, 'error': 'Part not found'}), 404
        return jsonify({
            'success': True,
            'part': {
                'part_id': part.part_id,
                'part_name': part.part_name,
                'cost': float(part.cost),
                'sku': part.sku,
                'category': part.category,
                'supplier': part.supplier,
                'is_active': part.is_active
            }
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@api_bp.route('/api/parts', methods=['POST'])
def create_part():
    try:
        data = request.get_json()
        tenant_id = data.get('tenant_id', 1)
        part = Part(
            tenant_id=tenant_id,
            part_name=data.get('part_name'),
            cost=float(data.get('cost', 0)),
            sku=data.get('sku'),
            category=data.get('category', 'General'),
            supplier=data.get('supplier'),
            is_active=True
        )
        db.session.add(part)
        db.session.commit()
        return jsonify({'success': True, 'part_id': part.part_id}), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500

@api_bp.route('/api/parts/<int:part_id>', methods=['PUT'])
def update_part(part_id):
    try:
        part = Part.find_by_id(part_id)
        if not part:
            return jsonify({'success': False, 'error': 'Part not found'}), 404
        data = request.get_json()
        part.part_name = data.get('part_name', part.part_name)
        part.cost = float(data.get('cost', part.cost))
        part.sku = data.get('sku', part.sku)
        part.category = data.get('category', part.category)
        part.supplier = data.get('supplier', part.supplier)
        db.session.commit()
        return jsonify({'success': True})
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500

@api_bp.route('/api/parts/<int:part_id>', methods=['DELETE'])
def delete_part(part_id):
    try:
        part = Part.find_by_id(part_id)
        if not part:
            return jsonify({'success': False, 'error': 'Part not found'}), 404
        part.is_active = False
        db.session.commit()
        return jsonify({'success': True})
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500

@api_bp.route('/api/inventory', methods=['GET'])
def get_inventory():
    try:
        tenant_id = request.args.get('tenant_id', 1, type=int)
        items = Inventory.query.filter_by(tenant_id=tenant_id).all()
        return jsonify({
            'success': True,
            'inventory': [{
                'inventory_id': i.inventory_id,
                'part_id': i.part_id,
                'quantity_on_hand': i.quantity_on_hand,
                'reorder_level': i.reorder_level,
                'reorder_quantity': i.reorder_quantity,
                'location': i.location
            } for i in items]
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500