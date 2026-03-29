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

# ── UPDATED: Remove Device by selected device_ids ────────────────────────────
@devices_bp.route('/api/devices/remove', methods=['POST'])
def remove_device():
    data       = request.get_json()
    lab_id     = data.get('lab_id')
    device_ids = data.get('device_ids', [])

    if not lab_id or not device_ids:
        return jsonify({'error': 'lab_id and device_ids required'}), 400

    db = get_db(current_app)
    try:
        with db.cursor() as cursor:
            # Verify all selected devices belong to this lab and check status
            format_ids = ','.join(['%s'] * len(device_ids))
            cursor.execute(f"""
                SELECT device_id, device_number, status 
                FROM DEVICE 
                WHERE device_id IN ({format_ids}) AND lab_id = %s
            """, (*device_ids, lab_id))
            devices = cursor.fetchall()

            # Check for Issued or Damaged
            issued  = [d for d in devices if d['status'] == 'Issued']
            damaged = [d for d in devices if d['status'] == 'Damaged']

            errors = []
            if issued:
                nums = ', '.join([f"PC {d['device_number']}" for d in issued])
                errors.append(f"{nums} still in use by student(s)")
            if damaged:
                nums = ', '.join([f"PC {d['device_number']}" for d in damaged])
                errors.append(f"{nums} still marked as damaged")

            if errors:
                return jsonify({'error': ' & '.join(errors)}), 400

            # Delete issue records and devices
            for d in devices:
                cursor.execute(
                    "DELETE FROM ISSUE_RECORD WHERE device_id = %s",
                    (d['device_id'],)
                )
                cursor.execute(
                    "DELETE FROM DEVICE WHERE device_id = %s",
                    (d['device_id'],)
                )

            # Renumber remaining PCs cleanly from 1
            cursor.execute("""
                SELECT device_id FROM DEVICE 
                WHERE lab_id = %s 
                ORDER BY device_number ASC
            """, (lab_id,))
            remaining = cursor.fetchall()

            for index, device in enumerate(remaining, start=1):
                cursor.execute("""
                    UPDATE DEVICE SET device_number = %s 
                    WHERE device_id = %s
                """, (index, device['device_id']))

            db.commit()

        return jsonify({'message': f'{len(devices)} PC(s) removed and renumbered successfully'}), 200
    except Exception as e:
        db.rollback()
        return jsonify({'error': str(e)}), 400
    finally:
        db.close()
# ── END: UPDATED Remove Device Route ─────────────────────────────────────────

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