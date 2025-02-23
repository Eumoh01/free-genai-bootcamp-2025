from flask import jsonify, request, current_app
from lib.db import get_db, validate_page
import sqlite3

def register_routes(app):
    @app.route('/api/study_activities')
    def get_study_activities():
        try:
            with get_db() as db:
                cursor = db.cursor()
                cursor.execute("""
                    SELECT id, name
                    FROM study_activities
                """)
                activities = cursor.fetchall()
                
            return jsonify({
                "activities": [
                    {
                        "id": activity['id'],
                        "name": activity['name']
                    } for activity in activities
                ]
            })
        except sqlite3.Error as e:
            return jsonify({
                "error": "Database error",
                "message": str(e)
            }), 500

    @app.route('/api/study_sessions')
    def get_study_sessions():
        try:
            page = request.args.get('page', 1, type=int)
            per_page = current_app.config['ITEMS_PER_PAGE']
            
            with get_db() as db:
                # Get total count first for validation
                cursor = db.cursor()
                cursor.execute("SELECT COUNT(*) as count FROM study_sessions")
                total = cursor.fetchone()['count']
                
                # Validate page number
                error_response = validate_page(page, total)
                if error_response:
                    return error_response
                
                offset = (page - 1) * per_page
                cursor.execute("""
                    SELECT 
                        s.id,
                        a.name as activity_name,
                        g.name as group_name,
                        s.created_at,
                        COUNT(r.id) as review_items_count
                    FROM study_sessions s
                    JOIN study_activities a ON a.id = s.study_activity_id
                    JOIN groups g ON g.id = s.group_id
                    LEFT JOIN word_review_items r ON r.study_session_id = s.id
                    GROUP BY s.id
                    ORDER BY s.created_at DESC
                    LIMIT ? OFFSET ?
                """, (per_page, offset))
                sessions = cursor.fetchall()

            return jsonify({
                "items": [
                    {
                        "id": session['id'],
                        "activity_name": session['activity_name'],
                        "group_name": session['group_name'],
                        "start_time": session['created_at'],
                        "end_time": session['created_at'],
                        "review_items_count": session['review_items_count']
                    } for session in sessions
                ],
                "total_pages": (total + per_page - 1) // per_page,
                "current_page": page,
                "total_sessions": total
            })
        except sqlite3.Error as e:
            return jsonify({
                "error": "Database error",
                "message": str(e)
            }), 500

    @app.route('/api/study_sessions/<int:id>/words/<int:word_id>/review', methods=['POST'])
    def create_word_review(id, word_id):
        try:
            correct = request.json.get('correct', False)
            
            with get_db() as db:
                cursor = db.cursor()
                cursor.execute("""
                    INSERT INTO word_review_items 
                    (word_id, study_session_id, correct, created_at) 
                    VALUES (?, ?, ?, datetime('now'))
                """, (word_id, id, correct))
                
                cursor.execute("SELECT datetime('now') as timestamp")
                timestamp = cursor.fetchone()['timestamp']
                db.commit()

            return jsonify({
                "message": "Word review recorded successfully",
                "success": True,
                "review": {
                    "session_id": id,
                    "word_id": word_id,
                    "correct": correct,
                    "created_at": timestamp
                }
            })
        except sqlite3.Error as e:
            return jsonify({
                "error": "Database error",
                "message": str(e)
            }), 500 