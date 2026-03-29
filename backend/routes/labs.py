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

# ── NEW: Remove Lab Route ─────────────────────────────────────────────────────
@labs_bp.route('/api/labs/<int:lab_id>', methods=['DELETE'])
def remove_lab(lab_id):
    db = get_db(current_app)
    try:
        with db.cursor() as cursor:
            # Check for issued PCs
            cursor.execute("""
                SELECT COUNT(*) as count FROM DEVICE
                WHERE lab_id = %s AND status = 'Issued'
            """, (lab_id,))
            issued = cursor.fetchone()['count']

            # Check for damaged PCs
            cursor.execute("""
                SELECT COUNT(*) as count FROM DEVICE
                WHERE lab_id = %s AND status = 'Damaged'
            """, (lab_id,))
            damaged = cursor.fetchone()['count']

            errors = []
            if issued > 0:
                errors.append(f"{issued} student(s) are still logged in")
            if damaged > 0:
                errors.append(f"{damaged} PC(s) are still marked as damaged")

            if errors:
                return jsonify({'error': ' & '.join(errors)}), 400

            # Safe to delete — delete issue records, devices, then lab
            cursor.execute("""
                DELETE ir FROM ISSUE_RECORD ir
                JOIN DEVICE d ON ir.device_id = d.device_id
                WHERE d.lab_id = %s
            """, (lab_id,))
            cursor.execute("DELETE FROM DEVICE WHERE lab_id = %s", (lab_id,))
            cursor.execute("DELETE FROM LAB WHERE lab_id = %s", (lab_id,))
            db.commit()

        return jsonify({'message': 'Lab removed successfully'}), 200
    except Exception as e:
        db.rollback()
        return jsonify({'error': str(e)}), 400
    finally:
        db.close()
# ── END: Remove Lab Route ─────────────────────────────────────────────────────