from flask import jsonify, request, current_app
from lib.db import get_db
import sqlite3

def register_routes(app):
    @app.route('/api/words')
    def get_words():
        try:
            page = request.args.get('page', 1, type=int)
            per_page = current_app.config['ITEMS_PER_PAGE']
            
            db = get_db()
            cursor = db.cursor()
            
            # Get total count
            cursor.execute("SELECT COUNT(*) as count FROM words")
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
                SELECT id, spanish, pronunciation, english
                FROM words
                LIMIT ? OFFSET ?
            """, (per_page, offset))
            
            words = cursor.fetchall()
            
            return jsonify({
                "items": [dict(word) for word in words],
                "total_pages": total_pages,
                "current_page": page,
                "total_words": total
            })
            
        except sqlite3.Error as e:
            return jsonify({
                "error": "Database error",
                "message": str(e)
            }), 500

    @app.route('/api/words/<int:word_id>')
    def get_word(word_id):
        try:
            db = get_db()
            cursor = db.cursor()
            
            # Get word details
            cursor.execute("""
                SELECT 
                    w.id,
                    w.spanish,
                    w.english,
                    w.pronunciation,
                    GROUP_CONCAT(g.id) as group_ids,
                    GROUP_CONCAT(g.name) as group_names
                FROM words w
                LEFT JOIN word_groups wg ON w.id = wg.word_id
                LEFT JOIN groups g ON wg.group_id = g.id
                WHERE w.id = ?
                GROUP BY w.id
            """, (word_id,))
            
            word = cursor.fetchone()
            if not word:
                return jsonify({
                    "error": "Word not found"
                }), 404
            
            # Convert to dict and process group data
            result = dict(word)
            
            # Handle groups data
            if result['group_ids']:
                result['groups'] = [
                    {'id': int(gid), 'name': name}
                    for gid, name in zip(
                        result['group_ids'].split(','),
                        result['group_names'].split(',')
                    )
                ]
            else:
                result['groups'] = []
                
            # Remove concatenated fields
            del result['group_ids']
            del result['group_names']
            
            return jsonify(result)
            
        except sqlite3.Error as e:
            return jsonify({
                "error": "Database error",
                "message": str(e)
            }), 500
        
# Functionality to add later:
# - Search words by group
# - Search words by group and word
# - Search words by word
# - Search words by word and group
# - Search words by word and group and group
# - Search words by word and group and group and group  