from flask import jsonify, request, current_app
from lib.db import get_db, validate_page
import sqlite3

def register_routes(app):
    @app.route('/api/groups')
    def get_groups():
        try:
            page = request.args.get('page', 1, type=int)
            per_page = current_app.config['ITEMS_PER_PAGE']
            
            with get_db() as db:
                # Get total count first for validation
                cursor = db.cursor()
                cursor.execute("SELECT COUNT(*) as count FROM groups")
                total = cursor.fetchone()['count']
                
                # Validate page number
                error_response = validate_page(page, total)
                if error_response:
                    return error_response
                
                offset = (page - 1) * per_page
                cursor.execute("""
                    SELECT 
                        id,
                        name,
                        words_count
                    FROM groups
                    LIMIT ? OFFSET ?
                """, (per_page, offset))
                groups = cursor.fetchall()

            return jsonify({
                "items": [
                    {
                        "id": group['id'],
                        "name": group['name'],
                        "words_count": group['words_count']
                    } for group in groups
                ],
                "total_pages": (total + per_page - 1) // per_page,
                "current_page": page,
                "total_groups": total
            })
        except sqlite3.Error as e:
            return jsonify({
                "error": "Database error",
                "message": str(e)
            }), 500 