from flask import Blueprint, request, jsonify, current_app
from extensions import get_db

devices_bp = Blueprint('devices', __name__)

@devices_bp.route('/api/devices/report-damaged', methods=['POST'])
def report_damaged():
    data = request.get_json()
    device_id = data.get('device_id')

    if not device_id:
        return jsonify({'error': 'device_id required'}), 400

    db = get_db(current_app)
    try:
        with db.cursor() as cursor:
            cursor.execute("""
                UPDATE DEVICE SET status = 'Damaged'
                WHERE device_id = %s
            """, (device_id,))
            db.commit()
        return jsonify({'message': 'Device marked as damaged'}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 400
    finally:
        db.close()

@devices_bp.route('/api/devices/mark-available', methods=['POST'])
def mark_available():
    data = request.get_json()
    device_id = data.get('device_id')
    admin_id  = data.get('admin_id')

    if not device_id or not admin_id:
        return jsonify({'error': 'device_id and admin_id required'}), 400

    db = get_db(current_app)
    try:
        with db.cursor() as cursor:
            cursor.execute(
                "SELECT admin_id FROM ADMIN WHERE admin_id = %s", (admin_id,)
            )
            if not cursor.fetchone():
                return jsonify({'error': 'Unauthorized'}), 401

            cursor.execute("""
                UPDATE DEVICE SET status = 'Available'
                WHERE device_id = %s AND status = 'Damaged'
            """, (device_id,))
            db.commit()
        return jsonify({'message': 'Device marked as available'}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 400
    finally:
        db.close()

@devices_bp.route('/api/devices/<int:lab_id>', methods=['GET'])
def get_devices(lab_id):
    db = get_db(current_app)
    try:
        with db.cursor() as cursor:
            cursor.execute("""
                SELECT d.device_id, d.device_number, d.status,
                       s.student_name, s.student_rollnumber,
                       s.year, s.department, s.division,
                       l.lab_number,
                       DATE_FORMAT(ir.issue_date,  '%%Y-%%m-%%d %%H:%%i:%%s') as issue_date,
                       DATE_FORMAT(ir.return_date, '%%Y-%%m-%%d %%H:%%i:%%s') as return_date
                FROM DEVICE d
                LEFT JOIN (
                    SELECT ir1.*
                    FROM ISSUE_RECORD ir1
                    INNER JOIN (
                        SELECT device_id, MAX(issue_date) as max_date
                        FROM ISSUE_RECORD
                        GROUP BY device_id
                    ) ir2 ON ir1.device_id = ir2.device_id
                          AND ir1.issue_date = ir2.max_date
                ) ir ON d.device_id = ir.device_id
                LEFT JOIN STUDENT s ON ir.student_id = s.student_id
                LEFT JOIN LAB l ON d.lab_id = l.lab_id
                WHERE d.lab_id = %s
                ORDER BY d.device_number
            """, (lab_id,))
            devices = cursor.fetchall()
        return jsonify(devices), 200
    finally:
        db.close()

@devices_bp.route('/api/devices', methods=['POST'])
def add_device():
    data   = request.get_json()
    lab_id = data.get('lab_id')
    count  = data.get('count', 1)

    if not lab_id:
        return jsonify({'error': 'lab_id required'}), 400

    db = get_db(current_app)
    try:
        with db.cursor() as cursor:
            cursor.execute("""
                SELECT COALESCE(MAX(device_number), 0) as max_num
                FROM DEVICE WHERE lab_id = %s
            """, (lab_id,))
            result   = cursor.fetchone()
            next_num = result['max_num'] + 1

            for i in range(count):
                cursor.execute("""
                    INSERT INTO DEVICE (lab_id, device_number, status)
                    VALUES (%s, %s, 'Available')
                """, (lab_id, next_num + i))
            db.commit()
        return jsonify({'message': f'{count} device(s) added'}), 201
    except Exception as e:
        return jsonify({'error': str(e)}), 400
    finally:
        db.close()