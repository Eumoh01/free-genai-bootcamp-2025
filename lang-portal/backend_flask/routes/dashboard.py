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
                "activiy_name": session['activity_name'],
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
            with get_db() as db:
                cursor = db.cursor()
                # Get total sessions
                cursor.execute("SELECT COUNT(*) as count FROM study_sessions")
                total_sessions = cursor.fetchone()['count']

                # Calculate current streak
                cursor.execute("""
                    WITH daily_study AS (
                        -- Get distinct study dates
                        SELECT DISTINCT date(created_at) as study_date
                        FROM study_sessions
                    ),
                    today_check AS (
                        -- Check if studied today
                        SELECT EXISTS (
                            SELECT 1 FROM daily_study 
                            WHERE study_date = date('now')
                        ) as studied_today
                    ),
                    streak_count AS (
                        -- Count consecutive days backwards from today/yesterday
                        SELECT COUNT(*) as days
                        FROM daily_study
                        WHERE study_date >= (
                            SELECT CASE 
                                WHEN studied_today = 1 THEN date('now')
                                ELSE date('now', '-1 day')
                            END
                            FROM today_check
                        )
                        AND NOT EXISTS (
                            -- Check for any gaps in dates
                            SELECT 1
                            FROM generate_series(
                                julianday(study_date),
                                julianday(
                                    CASE 
                                        WHEN (SELECT studied_today FROM today_check) = 1 
                                        THEN date('now')
                                        ELSE date('now', '-1 day')
                                    END
                                ),
                                1
                            ) as missing_date
                            WHERE missing_date NOT IN (
                                SELECT julianday(study_date) FROM daily_study
                            )
                        )
                    )
                    SELECT CASE 
                        WHEN (SELECT studied_today FROM today_check) = 0 THEN 0
                        ELSE (SELECT days FROM streak_count)
                    END as current_streak
                """)
                
                current_streak = cursor.fetchone()['current_streak']

            return jsonify({
                "total_sessions": total_sessions,
                "current_streak": current_streak
            })
        except sqlite3.Error as e:
            return jsonify({
                "error": "Database error",
                "message": str(e)
            }), 500