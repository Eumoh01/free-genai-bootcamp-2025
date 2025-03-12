from flask import jsonify, request, current_app
from lib.db import get_db, validate_page
import sqlite3
from datetime import datetime

def register_routes(app):
    @app.route('/api/study_activities')
    def get_study_activities():
        try:
            db = get_db()
            cursor = db.cursor()
            
            cursor.execute("""
                SELECT id, name, url, preview_url 
                FROM study_activities
                ORDER BY id
            """)
            activities = cursor.fetchall()
            
            return jsonify({
                "activities": [dict(activity) for activity in activities]
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
            
            db = get_db()
            cursor = db.cursor()
            
            # Get total count
            cursor.execute("SELECT COUNT(*) as count FROM study_sessions")
            total = cursor.fetchone()['count']
            total_pages = max(1, (total + per_page - 1) // per_page)  # At least 1 page
            
            # Validate page number
            if page < 1 or page > total_pages:
                return jsonify({
                    "error": "Invalid page number",
                    "message": f"Page number must be between 1 and {total_pages}"
                }), 400
            
            offset = (page - 1) * per_page
            cursor.execute("""
                SELECT s.id, s.created_at, s.completed_at,
                       g.name as group_name, 
                       a.name as activity_name
                FROM study_sessions s
                JOIN groups g ON s.group_id = g.id
                JOIN study_activities a ON s.study_activity_id = a.id
                ORDER BY s.created_at DESC
                LIMIT ? OFFSET ?
            """, (per_page, offset))
            sessions = cursor.fetchall()
            
            return jsonify({
                "items": [dict(session) for session in sessions],
                "total_pages": total_pages,
                "current_page": page,
                "total_sessions": total
            })
        except sqlite3.Error as e:
            return jsonify({
                "error": "Database error",
                "message": str(e)
            }), 500
    
    @app.route('/api/study_sessions', methods=['POST'])
    def create_study_session():
        try:
            data = request.get_json()
            
            # Validate required fields
            if not all(k in data for k in ['group_id', 'activity_id']):
                return jsonify({
                    "error": "Missing required fields"
                }), 400
            
            with get_db() as db:
                cursor = db.cursor()
                
                # Verify group and activity exist
                cursor.execute("""
                    SELECT EXISTS(SELECT 1 FROM groups WHERE id = ?) as group_exists,
                           EXISTS(SELECT 1 FROM study_activities WHERE id = ?) as activity_exists
                """, (data['group_id'], data['activity_id']))
                result = cursor.fetchone()
                
                if not result['group_exists']:
                    return jsonify({"error": "Invalid group ID"}), 400
                if not result['activity_exists']:
                    return jsonify({"error": "Invalid activity ID"}), 400
                
                # Create session
                cursor.execute("""
                    INSERT INTO study_sessions (group_id, study_activity_id, created_at)
                    VALUES (?, ?, datetime('now'))
                """, (data['group_id'], data['activity_id']))
                
                session_id = cursor.lastrowid
                
                # Get the created session details
                cursor.execute("""
                    SELECT id, group_id, study_activity_id, created_at, completed_at
                    FROM study_sessions 
                    WHERE id = ?
                """, (session_id,))
                
                session = dict(cursor.fetchone())
                db.commit()
                
                return jsonify({
                    "success": True,
                    "session": session
                })
                
        except sqlite3.Error as e:
            return jsonify({
                "error": "Database error",
                "message": str(e)
            }), 500

    @app.route('/api/study_sessions/<int:id>/words/<int:word_id>/review', methods=['POST'])
    def create_word_review(id, word_id):
        try:
            # Check if request has JSON
            if not request.is_json:
                return jsonify({
                    "error": "Invalid JSON",
                    "message": "Request must be valid JSON"
                }), 400
            
            # Get and validate correct parameter
            if 'correct' not in request.json:
                correct = False  # Default value
            else:
                correct = request.json['correct']
                if not isinstance(correct, bool):
                    return jsonify({
                        "error": "Invalid correct value",
                        "message": "correct must be a boolean"
                    }), 400
            
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

    @app.route('/api/study_sessions/<int:session_id>/complete', methods=['POST'])
    def complete_study_session(session_id):
        try:
            db = get_db()
            cursor = db.cursor()
            
            # Check if session exists and isn't already completed
            cursor.execute("""
                SELECT id, completed_at 
                FROM study_sessions 
                WHERE id = ?
            """, (session_id,))
            
            session = cursor.fetchone()
            if not session:
                return jsonify({
                    "error": "Session not found"
                }), 404
                
            if session['completed_at']:
                return jsonify({
                    "error": "Session already completed"
                }), 400
            
            # Update completion time
            cursor.execute("""
                UPDATE study_sessions 
                SET completed_at = datetime('now')
                WHERE id = ?
            """, (session_id,))
            
            # Get updated session with review count
            cursor.execute("""
                SELECT s.*, COUNT(r.id) as review_items_count
                FROM study_sessions s
                LEFT JOIN word_review_items r ON r.study_session_id = s.id
                WHERE s.id = ?
                GROUP BY s.id
            """, (session_id,))
            
            session = dict(cursor.fetchone())
            db.commit()
            
            return jsonify({
                "success": True,
                "session": session
            })
            
        except sqlite3.Error as e:
            return jsonify({
                "error": "Database error",
                "message": str(e)
            }), 500

    @app.route('/api/study_sessions/<int:session_id>/words')
    def get_session_words(session_id):
        try:
            db = get_db()
            cursor = db.cursor()
            
            # Check if session exists
            cursor.execute("SELECT 1 FROM study_sessions WHERE id = ?", (session_id,))
            if not cursor.fetchone():
                return jsonify({
                    "error": "Session not found"
                }), 404
            
            # Get only reviewed words for this session
            cursor.execute("""
                SELECT 
                    w.id,
                    w.spanish,
                    w.english,
                    w.pronunciation,
                    1 as reviewed,  -- If we have the word, it was reviewed
                    r.correct
                FROM words w
                JOIN word_review_items r ON r.word_id = w.id 
                WHERE r.study_session_id = ?
                ORDER BY w.id
            """, (session_id,))
            
            words = cursor.fetchall()
            
            return jsonify({
                "words": [dict(word) for word in words]
            })
            
        except sqlite3.Error as e:
            return jsonify({
                "error": "Database error",
                "message": str(e)
            }), 500

    @app.route('/api/study_sessions/<int:session_id>/stats')
    def get_session_stats(session_id):
        try:
            db = get_db()
            cursor = db.cursor()
            
            # Check if session exists
            cursor.execute("SELECT 1 FROM study_sessions WHERE id = ?", (session_id,))
            if not cursor.fetchone():
                return jsonify({
                    "error": "Session not found"
                }), 404
            
            # Get review statistics
            cursor.execute("""
                SELECT 
                    COUNT(*) as total_words,
                    SUM(CASE WHEN correct = 1 THEN 1 ELSE 0 END) as correct_count,
                    ROUND(AVG(CASE WHEN correct = 1 THEN 100.0 ELSE 0 END), 2) as accuracy
                FROM word_review_items
                WHERE study_session_id = ?
            """, (session_id,))
            
            stats = dict(cursor.fetchone())
            
            # Handle case where there are no reviews
            if stats['total_words'] == 0:
                stats['accuracy'] = 0
                stats['correct_count'] = 0
            
            return jsonify(stats)
            
        except sqlite3.Error as e:
            return jsonify({
                "error": "Database error",
                "message": str(e)
            }), 500                                     

# Functionality to add later:
# - Get session history by date
# - Get session history by group
# - Get session history by activity
# - Get session history combined filters
# - Get session history by date range
# - Get session history by date range and group