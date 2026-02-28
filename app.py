from flask import Flask, request, jsonify, session
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
from werkzeug.security import generate_password_hash, check_password_hash
from google import genai
from datetime import datetime, timedelta

# --- INITIALIZATION ---
client = genai.Client(api_key="AIzaSyCMij2fGZCpHpM_5dfr-5Vx0UwqtgwhptA")

app = Flask(__name__)
app.secret_key = "development_key_123"

app.config.update(
    SQLALCHEMY_DATABASE_URI='postgresql://neondb_owner:npg_eKw84vUXxYLP@ep-nameless-tooth-aihj4z15-pooler.c-4.us-east-1.aws.neon.tech/neondb?sslmode=require&channel_binding=require',
    SQLALCHEMY_TRACK_MODIFICATIONS=False,
    SESSION_COOKIE_SAMESITE="Lax",
    SESSION_COOKIE_SECURE=False, 
    SESSION_COOKIE_HTTPONLY=False 
)

db = SQLAlchemy(app)
CORS(app, supports_credentials=True, origins=["http://localhost:3000"])

# --- MODELS ---
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    # INCREASE THIS FROM 120 TO 255
    password = db.Column(db.String(255), nullable=False) 
    habits = db.relationship('Habit', backref='user', lazy=True)

class Habit(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    completed = db.Column(db.Boolean, default=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)

class CompletionLog(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    habit_id = db.Column(db.Integer, db.ForeignKey('habit.id'), nullable=False)
    # FIX: Pass the function itself (datetime.utcnow().date) so it evaluates on every insert
    date = db.Column(db.Date, default=lambda: datetime.utcnow().date())

with app.app_context():
    db.create_all()

# --- AUTH ROUTES ---
@app.route('/api/register', methods=['POST'])
def register():
    data = request.json
    if User.query.filter_by(username=data['username']).first():
        return jsonify({"error": "User already exists"}), 400
    
    hashed_pw = generate_password_hash(data['password'])
    new_user = User(username=data['username'], password=hashed_pw)
    db.session.add(new_user)
    db.session.commit()
    return jsonify({"message": "User created successfully"}), 201

@app.route('/api/login', methods=['POST'])
def login():
    data = request.json
    user = User.query.filter_by(username=data['username']).first()
    if user and check_password_hash(user.password, data['password']):
        session['user_id'] = user.id
        return jsonify({"message": "Logged in", "user": user.username})
    return jsonify({"error": "Invalid username or password"}), 401

@app.route('/api/logout', methods=['POST'])
def logout():
    session.pop('user_id', None)
    return jsonify({"message": "Logged out"}), 200

# --- HABIT ROUTES ---
@app.route('/api/habits', methods=['GET'])
def get_habits():
    user_id = session.get('user_id')
    if not user_id:
        return jsonify({"error": "Unauthorized"}), 401
    habits = Habit.query.filter_by(user_id=user_id).all()
    return jsonify([{"id": h.id, "name": h.name, "completed": h.completed} for h in habits])

@app.route('/api/habits', methods=['POST'])
def add_habit():
    user_id = session.get('user_id')
    if not user_id:
        return jsonify({"error": "Unauthorized"}), 401
    data = request.json
    new_habit = Habit(name=data['name'], user_id=user_id)
    db.session.add(new_habit)
    db.session.commit()
    return jsonify({"id": new_habit.id, "name": new_habit.name, "completed": False})

@app.route('/api/habits/<int:id>', methods=['PATCH'])
def toggle_habit(id):
    user_id = session.get('user_id')
    habit = Habit.query.filter_by(id=id, user_id=user_id).first()
    if not habit:
        return jsonify({"error": "Habit not found"}), 404
    
    habit.completed = not habit.completed
    today = datetime.utcnow().date()
    
    if habit.completed:
        # Avoid duplicate logs for the same day if the user toggles multiple times
        existing_log = CompletionLog.query.filter_by(habit_id=id, date=today).first()
        if not existing_log:
            new_log = CompletionLog(habit_id=id, date=today)
            db.session.add(new_log)
    else:
        CompletionLog.query.filter_by(habit_id=id, date=today).delete()
        
    db.session.commit()
    return jsonify({"id": habit.id, "completed": habit.completed})

@app.route('/api/habits/<int:id>', methods=['DELETE'])
def delete_habit(id):
    user_id = session.get('user_id')
    habit = Habit.query.filter_by(id=id, user_id=user_id).first()
    if not habit:
        return jsonify({"error": "Habit not found"}), 404
    
    # Delete associated logs first (Cascade delete manually)
    CompletionLog.query.filter_by(habit_id=id).delete()
    db.session.delete(habit)
    db.session.commit()
    return jsonify({"message": "Deleted"}), 200

@app.route('/api/habits/reset', methods=['POST'])
def reset_habits():
    user_id = session.get('user_id')
    if not user_id:
        return jsonify({"error": "Unauthorized"}), 401
    
    today = datetime.utcnow().date()

    # 1. Reset checkbox status
    Habit.query.filter_by(user_id=user_id).update({Habit.completed: False})

    # 2. Reset history counts for today specifically
    db.session.query(CompletionLog).filter(
        CompletionLog.habit_id.in_(
            db.session.query(Habit.id).filter_by(user_id=user_id)
        ),
        CompletionLog.date == today
    ).delete(synchronize_session=False)

    db.session.commit()
    return jsonify({"message": "All habits and today's history reset"}), 200

# --- AI COACH ROUTE ---
@app.route('/api/ai-coach', methods=['GET'])
def ai_coach():
    user_id = session.get('user_id')
    habits = Habit.query.filter_by(user_id=user_id).all()
    
    if not habits:
        return jsonify({"advice": "Add some habits first, then I'll give you a strategy!"})

    habit_list = [f"{h.name} ({'Done' if h.completed else 'Pending'})" for h in habits]
    prompt = f"User Habits today: {', '.join(habit_list)}. Give a clever, 2-sentence piece of advice to help them stay on track."
    
    try:
        response = client.models.generate_content(model='gemini-2.5-flash', contents=prompt)
        return jsonify({"advice": response.text})
    except Exception as e:
        print(f"DEBUG AI ERROR: {e}") 
        return jsonify({"error": "AI Coach is currently over-caffeinated."}), 500

# --- HISTORY ROUTE ---
@app.route('/api/history', methods=['GET'])
def get_history():
    user_id = session.get('user_id')
    if not user_id:
        return jsonify({"error": "Unauthorized"}), 401
        
    seven_days_ago = datetime.utcnow().date() - timedelta(days=6)
    
    logs = db.session.query(CompletionLog.date, db.func.count(CompletionLog.id))\
        .join(Habit)\
        .filter(Habit.user_id == user_id, CompletionLog.date >= seven_days_ago)\
        .group_by(CompletionLog.date).all()
    
    history_data = {str(log[0]): log[1] for log in logs}
    return jsonify(history_data)

if __name__ == '__main__':
    app.run(debug=True, port=5000)