from flask import Flask, request, jsonify, send_from_directory
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
from datetime import datetime
import os

app = Flask(__name__, static_folder='../frontend', static_url_path='')
CORS(app)

# Database config
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///bank.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# Models
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100))
    balance = db.Column(db.Float, default=10000)

class Transaction(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    amount = db.Column(db.Float)
    type = db.Column(db.String(20))  # credit or debit
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)

# Create tables and default user
def create_tables():
    db.create_all()
    if not User.query.first():
        user = User(name="Gokul", balance=100000)
        db.session.add(user)
        db.session.commit()

# Serve index.html on /
@app.route('/')
def serve_index():
    return send_from_directory(app.static_folder, 'index.html')

# API Routes
@app.route('/balance/<int:user_id>', methods=['GET'])
def get_balance(user_id):
    user = User.query.get(user_id)
    if not user:
        return jsonify({"error": "User not found"}), 404
    return jsonify({"name": user.name, "balance": user.balance})

@app.route('/transfer', methods=['POST'])
def transfer():
    data = request.json
    user_id = data.get('user_id')
    amount = float(data.get('amount', 0))

    user = User.query.get(user_id)
    if not user:
        return jsonify({"error": "User not found"}), 404
    if amount <= 0:
        return jsonify({"error": "Invalid amount"}), 400
    if user.balance < amount:
        return jsonify({"error": "Insufficient balance"}), 400

    user.balance -= amount
    txn = Transaction(user_id=user.id, amount=amount, type='debit')
    db.session.add(txn)
    db.session.commit()
    return jsonify({"message": "Transfer successful", "balance": user.balance})

@app.route('/credit', methods=['POST'])
def credit():
    data = request.json
    user_id = data.get('user_id')
    amount = float(data.get('amount', 0))

    # Only Gokul (user_id=1) can credit money
    if user_id != 1:
        return jsonify({"error": "Only Gokul can add money"}), 403

    user = User.query.get(user_id)
    if not user:
        return jsonify({"error": "User not found"}), 404
    if amount <= 0:
        return jsonify({"error": "Invalid amount"}), 400

    user.balance += amount
    txn = Transaction(user_id=user.id, amount=amount, type='credit')
    db.session.add(txn)
    db.session.commit()
    return jsonify({"message": f"Gokul added ₹{amount} to the account", "balance": user.balance})

@app.route('/transactions/<int:user_id>', methods=['GET'])
def get_transactions(user_id):
    txns = Transaction.query.filter_by(user_id=user_id).order_by(Transaction.timestamp.desc()).all()
    result = []
    for txn in txns:
        result.append({
            "amount": txn.amount,
            "type": txn.type,
            "timestamp": txn.timestamp.strftime("%Y-%m-%d %H:%M:%S")
        })

    return jsonify(result)

# Main
if __name__ == '__main__':
    with app.app_context():
        create_tables()
    app.run(debug=True)
