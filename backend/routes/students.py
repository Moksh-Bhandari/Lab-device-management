from flask import Blueprint, request, jsonify, current_app
from extensions import get_db

students_bp = Blueprint('students', __name__)

@students_bp.route('/api/student/status', methods=['POST'])
def check_status():
    data = request.get_json()
    roll = data.get('student_rollnumber')

    if not roll:
        return jsonify({'error': 'Roll number required'}), 400

    db = get_db(current_app)
    try:
        with db.cursor() as cursor:
            cursor.execute("""
                SELECT ir.issue_id, ir.device_id, s.student_id
                FROM STUDENT s
                JOIN ISSUE_RECORD ir ON s.student_id = ir.student_id
                WHERE s.student_rollnumber = %s 
                AND ir.return_date IS NULL
            """, (roll,))
            active = cursor.fetchone()

        if active:
            return jsonify({
                'status': 'logged_in',
                'issue_id': active['issue_id']
            }), 200
        else:
            return jsonify({'status': 'logged_out'}), 200
    finally:
        db.close()

@students_bp.route('/api/student/login', methods=['POST'])
def student_login():
    data = request.get_json()
    required = ['student_rollnumber', 'student_name', 'department',
                'year', 'division', 'device_id', 'admin_id']

    for field in required:
        if not data.get(field):
            return jsonify({'error': f'{field} is required'}), 400

    db = get_db(current_app)
    try:
        with db.cursor() as cursor:
            # Check if device is available
            cursor.execute(
                "SELECT status FROM DEVICE WHERE device_id = %s",
                (data['device_id'],)
            )
            device = cursor.fetchone()
            if not device or device['status'] != 'Available':
                return jsonify({'error': 'Device not available'}), 400

            # Insert or get student
            cursor.execute(
                "SELECT student_id FROM STUDENT WHERE student_rollnumber = %s",
                (data['student_rollnumber'],)
            )
            student = cursor.fetchone()

            if not student:
                cursor.execute("""
                    INSERT INTO STUDENT
                    (student_rollnumber, student_name, department, year, division)
                    VALUES (%s, %s, %s, %s, %s)
                """, (data['student_rollnumber'], data['student_name'],
                      data['department'], data['year'], data['division']))
                student_id = cursor.lastrowid
            else:
                student_id = student['student_id']

            # Create issue record
            cursor.execute("""
                INSERT INTO ISSUE_RECORD (device_id, student_id, issued_by)
                VALUES (%s, %s, %s)
            """, (data['device_id'], student_id, data['admin_id']))

            # Mark device as Issued
            cursor.execute(
                "UPDATE DEVICE SET status = 'Issued' WHERE device_id = %s",
                (data['device_id'],)
            )
            db.commit()

        return jsonify({'message': 'Logged in successfully'}), 201
    except Exception as e:
        db.rollback()
        return jsonify({'error': str(e)}), 400
    finally:
        db.close()

@students_bp.route('/api/student/logout', methods=['POST'])
def student_logout():
    data = request.get_json()
    issue_id = data.get('issue_id')

    if not issue_id:
        return jsonify({'error': 'issue_id required'}), 400

    db = get_db(current_app)
    try:
        with db.cursor() as cursor:
            # Get device_id first
            cursor.execute(
                "SELECT device_id FROM ISSUE_RECORD WHERE issue_id = %s",
                (issue_id,)
            )
            record = cursor.fetchone()
            if not record:
                return jsonify({'error': 'Record not found'}), 404

            # Set return date
            cursor.execute("""
                UPDATE ISSUE_RECORD SET return_date = NOW()
                WHERE issue_id = %s
            """, (issue_id,))

            # Free the device
            cursor.execute("""
                UPDATE DEVICE SET status = 'Available'
                WHERE device_id = %s
            """, (record['device_id'],))

            db.commit()
        return jsonify({'message': 'Logged out successfully'}), 200
    except Exception as e:
        db.rollback()
        return jsonify({'error': str(e)}), 400
    finally:
        db.close()