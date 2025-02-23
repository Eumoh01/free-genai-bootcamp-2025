from flask import jsonify, request
from lib.db import get_db
import sqlite3

def register_routes(app):
    @app.route('/api/reset_history', methods=['POST'])
    def reset_history():
        try:
            with get_db() as db:
                cursor = db.cursor()
                # Delete all study history
                cursor.execute("DELETE FROM word_review_items")
                cursor.execute("DELETE FROM study_sessions")
                db.commit()

            return jsonify({
                "message": "Study history has been reset",
                "success": True
            })
        except sqlite3.Error as e:
            return jsonify({
                "error": "Database error",
                "message": str(e)
            }), 500

    @app.route('/api/full_reset', methods=['POST'])
    def full_reset():
        try:
            with get_db() as db:
                cursor = db.cursor()
                # Drop all data but keep tables
                cursor.execute("DELETE FROM word_review_items")
                cursor.execute("DELETE FROM study_sessions")
                cursor.execute("DELETE FROM word_groups")
                cursor.execute("DELETE FROM words")
                cursor.execute("DELETE FROM groups")
                cursor.execute("DELETE FROM study_activities")
                db.commit()

                # TODO: Re-run seed data import

            return jsonify({
                "message": "Database has been reset to initial state",
                "success": True
            })
        except sqlite3.Error as e:
            return jsonify({
                "error": "Database error",
                "message": str(e)
            }), 500 