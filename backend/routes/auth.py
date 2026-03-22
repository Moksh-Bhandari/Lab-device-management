from flask import Blueprint, request, jsonify, session, current_app
from extensions import get_db, bcrypt

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/api/admin/login', methods=['POST'])
def admin_login():
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')

    if not username or not password:
        return jsonify({'error': 'Username and password required'}), 400

    db = get_db(current_app)
    try:
        with db.cursor() as cursor:
            cursor.execute("SELECT * FROM ADMIN WHERE username = %s", (username,))
            admin = cursor.fetchone()

        if not admin or not bcrypt.check_password_hash(admin['password'], password):
            return jsonify({'error': 'Invalid credentials'}), 401

        session['admin_id'] = admin['admin_id']
        session['username'] = admin['username']
        return jsonify({
            'message': 'Login successful',
            'admin_id': admin['admin_id'],
            'username': admin['username']
        }), 200

    finally:
        db.close()

@auth_bp.route('/api/admin/logout', methods=['POST'])
def admin_logout():
    session.clear()
    return jsonify({'message': 'Logged out'}), 200