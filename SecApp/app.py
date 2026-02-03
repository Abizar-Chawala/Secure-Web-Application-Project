from flask import Flask, render_template, request, redirect, session
import sqlite3
import os

app = Flask(__name__)
app.secret_key = 'insecure-key-12345'  # INTENTIONALLY WEAK

def init_db():
    """Initialize the database"""
    conn = sqlite3.connect('users.db')
    conn.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL,
            password TEXT NOT NULL
        )
    ''')
    # Add a test user
    try:
        conn.execute("INSERT INTO users (username, password) VALUES ('admin', 'password123')")
        conn.commit()
    except:
        pass  # User already exists
    conn.close()

@app.route('/')
def home():
    return render_template('home.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        # VULNERABILITY: SQL Injection
        conn = sqlite3.connect('users.db')
        query = f"SELECT * FROM users WHERE username='{username}' AND password='{password}'"
        user = conn.execute(query).fetchone()
        conn.close()
        
        if user:
            session['user_id'] = user[0]
            session['username'] = user[1]
            return redirect('/dashboard')
        
        return render_template('login.html', error="Invalid credentials")
    
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        # VULNERABILITY: No input validation
        conn = sqlite3.connect('users.db')
        try:
            query = f"INSERT INTO users (username, password) VALUES ('{username}', '{password}')"
            conn.execute(query)
            conn.commit()
            conn.close()
            return redirect('/login')
        except:
            conn.close()
            return render_template('register.html', error="Username already exists")
    
    return render_template('register.html')

@app.route('/dashboard')
def dashboard():
    if 'username' not in session:
        return redirect('/login')
    
    # VULNERABILITY: Reflected XSS
    name = request.args.get('name', session['username'])
    return f"<h1>Welcome {name}!</h1><p><a href='/upload'>Upload File</a> | <a href='/logout'>Logout</a></p>"

@app.route('/upload', methods=['GET', 'POST'])
def upload():
    if 'username' not in session:
        return redirect('/login')
    
    if request.method == 'POST':
        if 'file' not in request.files:
            return "No file uploaded"
        
        file = request.files['file']
        if file.filename == '':
            return "No file selected"
        
        # VULNERABILITY: No file type validation
        filepath = os.path.join('uploads', file.filename)
        file.save(filepath)
        
        return f"File {file.filename} uploaded successfully! <a href='/dashboard'>Back to dashboard</a>"
    
    return render_template('upload.html')

@app.route('/logout')
def logout():
    session.clear()
    return redirect('/')

if __name__ == '__main__':
    init_db()
    os.makedirs('uploads', exist_ok=True)
    app.run(debug=True, host='127.0.0.1', port=5000)
