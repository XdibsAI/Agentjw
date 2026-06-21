from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from models import db, Todo

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///todos.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db.init_app(app)

# Create tables
with app.app_context():
    db.create_all()

# GET /todos - Retrieve all todos
@app.route('/todos', methods=['GET'])
def get_todos():
    try:
        todos = Todo.query.all()
        return jsonify([todo.to_dict() for todo in todos])
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# GET /todos/<id> - Retrieve a specific todo
@app.route('/todos/<int:todo_id>', methods=['GET'])
def get_todo(todo_id):
    try:
        todo = Todo.query.get(todo_id)
        if todo is None:
            return jsonify({'error': 'Todo not found'}), 404
        return jsonify(todo.to_dict())
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# POST /todos - Create a new todo
@app.route('/todos', methods=['POST'])
def create_todo():
    try:
        data = request.get_json()
        
        if not data or 'title' not in data:
            return jsonify({'error': 'Title is required'}), 400
            
        todo = Todo(
            title=data['title'],
            description=data.get('description', ''),
            completed=data.get('completed', False)
        )
        
        db.session.add(todo)
        db.session.commit()
        
        return jsonify(todo.to_dict()), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

# PUT /todos/<id> - Update a todo
@app.route('/todos/<int:todo_id>', methods=['PUT'])
def update_todo(todo_id):
    try:
        todo = Todo.query.get(todo_id)
        if todo is None:
            return jsonify({'error': 'Todo not found'}), 404
            
        data = request.get_json()
        if not data:
            return jsonify({'error': 'No data provided'}), 400
            
        todo.title = data.get('title', todo.title)
        todo.description = data.get('description', todo.description)
        todo.completed = data.get('completed', todo.completed)
        
        db.session.commit()
        
        return jsonify(todo.to_dict())
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

# DELETE /todos/<id> - Delete a todo
@app.route('/todos/<int:todo_id>', methods=['DELETE'])
def delete_todo(todo_id):
    try:
        todo = Todo.query.get(todo_id)
        if todo is None:
            return jsonify({'error': 'Todo not found'}), 404
            
        db.session.delete(todo)
        db.session.commit()
        
        return jsonify({'message': 'Todo deleted successfully'}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

# Health check endpoint
@app.route('/health', methods=['GET'])
def health_check():
    return jsonify({'status': 'healthy'}), 200

if __name__ == '__main__':
    app.run(debug=True)