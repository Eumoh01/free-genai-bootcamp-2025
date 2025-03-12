from flask import jsonify, request
from lib.db import get_db
import sqlite3

def register_routes(app):
    @app.route('/api/dashboard/last_study_session')
    def last_study_session():
        try:
            with get_db() as db:
                cursor = db.cursor()
                cursor.execute("""
                    SELECT 
                        s.id,
                        s.study_activity_id as activity_id,
                        a.name as activity_name,
                        s.group_id,
                        g.name as group_name,
                        s.created_at
                    FROM study_sessions s
                    JOIN study_activities a ON a.id = s.study_activity_id
                    JOIN groups g ON g.id = s.group_id
                    ORDER BY s.created_at DESC
                    LIMIT 1
                """)
                session = cursor.fetchone()

            if not session:
                return jsonify(None)

            return jsonify({
                "id": session['id'],
                "activity_id": session['activity_id'],
                "activity_name": session['activity_name'],
                "group_id": session['group_id'],
                "group_name": session['group_name'],
                "created_at": session['created_at']
            })
        except sqlite3.Error as e:
            return jsonify({
                "error": "Database error",
                "message": str(e)
            }), 500

    @app.route('/api/dashboard/study_progress')
    def study_progress():
        try:
            with get_db() as db:
                cursor = db.cursor()
                # Get total words
                cursor.execute("SELECT COUNT(*) as count FROM words")
                total_words = cursor.fetchone()['count']

                # Get studied words count
                cursor.execute("""
                    SELECT COUNT(DISTINCT word_id) as count 
                    FROM word_review_items
                """)
                studied_words = cursor.fetchone()['count']

            return jsonify({
                "total_words": total_words,
                "total_words_studied": studied_words
            })
        except sqlite3.Error as e:
            return jsonify({
                "error": "Database error",
                "message": str(e)
            }), 500

    @app.route('/api/dashboard/quick_stats')
    def quick_stats():
        try:
            db = get_db()
            cursor = db.cursor()
            
            # Get total sessions
            cursor.execute("SELECT COUNT(*) as count FROM study_sessions")
            total_sessions = cursor.fetchone()['count']
            
            # Calculate current streak
            cursor.execute("""
                WITH RECURSIVE dates(date) AS (
                    SELECT date('now')
                    UNION ALL
                    SELECT date(date, '-1 day')
                    FROM dates
                    WHERE date >= date('now', '-30 days')  -- Limit recursion
                ),
                study_dates AS (
                    SELECT DISTINCT date(created_at) as study_date
                    FROM study_sessions
                    WHERE date(created_at) >= date('now', '-30 days')
                )
                SELECT COUNT(*) as streak
                FROM (
                    SELECT dates.date
                    FROM dates
                    LEFT JOIN study_dates ON dates.date = study_dates.study_date
                    WHERE study_dates.study_date IS NOT NULL
                    ORDER BY dates.date DESC
                    LIMIT -1 OFFSET (
                        SELECT CASE 
                            WHEN EXISTS (
                                SELECT 1 FROM study_dates 
                                WHERE study_date = date('now')
                            ) THEN 0
                            ELSE 1
                        END
                    )
                ) streak_days
                WHERE NOT EXISTS (
                    SELECT 1
                    FROM dates d
                    WHERE d.date > streak_days.date
                      AND d.date <= date('now')
                      AND NOT EXISTS (
                        SELECT 1 FROM study_dates
                        WHERE study_date = d.date
                      )
                )
            """)
            current_streak = cursor.fetchone()['streak']
            
            return jsonify({
                "total_sessions": total_sessions,
                "current_streak": current_streak
            })
        except sqlite3.Error as e:
            return jsonify({
                "error": "Database error",
                "message": str(e)
            }), 500