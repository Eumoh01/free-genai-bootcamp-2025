from flask import jsonify, request, current_app
from lib.db import get_db
import sqlite3

def register_routes(app):
    @app.route('/api/groups')
    def get_groups():
        try:
            # Get page parameter as string first
            page_param = request.args.get('page')
            
            # Check if page parameter is valid integer
            try:
                page = int(page_param) if page_param is not None else 1
            except ValueError:
                return jsonify({
                    "error": "Invalid page number",
                    "message": "Page number must be an integer"
                }), 400
            
            per_page = current_app.config['ITEMS_PER_PAGE']
            
            db = get_db()
            cursor = db.cursor()
            
            # Get total count
            cursor.execute("SELECT COUNT(*) as count FROM groups")
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
                SELECT id, name, words_count
                FROM groups 
                ORDER BY id  -- Ensure consistent ordering
                LIMIT ? OFFSET ?
            """, (per_page, offset))
            groups = cursor.fetchall()
            
            return jsonify({
                "items": [dict(group) for group in groups],
                "total_pages": total_pages,
                "current_page": page,
                "total_groups": total
            })
        except sqlite3.Error as e:
            return jsonify({
                "error": "Database error",
                "message": str(e)
            }), 500

    @app.route('/api/groups/<int:group_id>/words', methods=['POST'])
    def add_word_to_group(group_id):
        try:
            data = request.get_json()
            if 'word_id' not in data:
                return jsonify({
                    "error": "Missing word_id"
                }), 400
                
            word_id = data['word_id']
            
            db = get_db()
            cursor = db.cursor()
            
            # Check if group exists
            cursor.execute("SELECT 1 FROM groups WHERE id = ?", (group_id,))
            if not cursor.fetchone():
                return jsonify({
                    "error": "Group not found"
                }), 404
                
            # Check if word exists
            cursor.execute("SELECT 1 FROM words WHERE id = ?", (word_id,))
            if not cursor.fetchone():
                return jsonify({
                    "error": "Word not found"
                }), 404
                
            # Check if word already in group
            cursor.execute("""
                SELECT 1 FROM word_groups 
                WHERE word_id = ? AND group_id = ?
            """, (word_id, group_id))
            if cursor.fetchone():
                return jsonify({
                    "error": "Word already in group"
                }), 400
                
            # Add word to group
            cursor.execute("""
                INSERT INTO word_groups (word_id, group_id)
                VALUES (?, ?)
            """, (word_id, group_id))
            
            # Update group word count
            cursor.execute("""
                UPDATE groups 
                SET words_count = words_count + 1
                WHERE id = ?
            """, (group_id,))
            
            db.commit()
            
            return jsonify({
                "success": True,
                "message": "Word added to group"
            })
            
        except sqlite3.Error as e:
            return jsonify({
                "error": "Database error",
                "message": str(e)
            }), 500 

    @app.route('/api/groups/<int:group_id>/words')
    def get_group_words(group_id):
        try:
            db = get_db()
            cursor = db.cursor()
            
            # Check if group exists
            cursor.execute("SELECT 1 FROM groups WHERE id = ?", (group_id,))
            if not cursor.fetchone():
                return jsonify({
                    "error": "Group not found"
                }), 404
            
            # Get all words in the group
            cursor.execute("""
                SELECT 
                    w.id,
                    w.spanish,
                    w.english,
                    w.pronunciation
                FROM words w
                JOIN word_groups wg ON w.id = wg.word_id
                WHERE wg.group_id = ?
                ORDER BY w.id
            """, (group_id,))
            
            words = cursor.fetchall()
            
            return jsonify({
                "words": [dict(word) for word in words]
            })
            
        except sqlite3.Error as e:
            return jsonify({
                "error": "Database error",
                "message": str(e)
            }), 500

# Functionality to add later:
# - Remove word from group
# - Update group name
# - Delete group
# - Get all groups for a word
# - Get all words for a group