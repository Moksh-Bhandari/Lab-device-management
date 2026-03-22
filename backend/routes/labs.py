from flask import Blueprint, request, jsonify, current_app
from extensions import get_db

labs_bp = Blueprint('labs', __name__)

@labs_bp.route('/api/labs', methods=['GET'])
def get_labs():
    db = get_db(current_app)
    try:
        with db.cursor() as cursor:
            cursor.execute("SELECT * FROM LAB ORDER BY lab_number")
            labs = cursor.fetchall()
        return jsonify(labs), 200
    finally:
        db.close()

@labs_bp.route('/api/labs', methods=['POST'])
def add_lab():
    data = request.get_json()
    lab_number = data.get('lab_number')

    if not lab_number:
        return jsonify({'error': 'Lab number required'}), 400

    db = get_db(current_app)
    try:
        with db.cursor() as cursor:
            cursor.execute("INSERT INTO LAB (lab_number) VALUES (%s)", (lab_number,))
            db.commit()
            lab_id = cursor.lastrowid
        return jsonify({'message': 'Lab added', 'lab_id': lab_id}), 201
    except Exception as e:
        return jsonify({'error': str(e)}), 400
    finally:
        db.close()