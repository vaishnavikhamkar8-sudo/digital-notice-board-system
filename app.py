import sqlite3
import os
from functools import wraps
from flask import Flask, render_template, request, redirect, url_for, flash, session
from werkzeug.security import generate_password_hash, check_password_hash



app = Flask(__name__)
app.config['SECRET_KEY'] = 'change-this-to-a-random-secret-string'  # change in production

DB_PATH = os.path.join(os.path.dirname(__file__), 'notices.db')

def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # not logged in → go to login
        if 'username' not in session:
            flash("Please log in first.", "warning")
            return redirect(url_for('login'))

        # logged in but not admin → go home
        if session['username'].lower() != 'admin':
            flash("Access denied! Admins only.", "danger")
            return redirect(url_for('index'))

        return f(*args, **kwargs)
    return decorated_function
def login_required(f):
    @wraps(f)
    def wrapped(*args, **kwargs):
        if 'username' not in session:
            flash('Please log in to access that page.', 'warning')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return wrapped


@app.template_filter('datetimeformat')
def datetimeformat(value, format='%b %d, %Y'):
    from datetime import datetime
    if isinstance(value, str):
        value = datetime.fromisoformat(value)
    return value.strftime(format)




@app.route('/')
def index():
    if 'username' not in session:
        return redirect(url_for('login'))   # Not logged in → go to login
    else:
        return redirect(url_for('home'))    # Already logged in → go to home

@app.route('/home')
def home():
    if 'username' not in session:
        return redirect(url_for('login'))

    conn = get_db()
    cur = conn.execute("SELECT * FROM notices ORDER BY created_at DESC")
    notices = cur.fetchall()
    conn.close()

    return render_template("index.html", username=session['username'], notices=notices)







@app.route('/notice/<int:id>')
def notice(id):
    conn = get_db()
    cur = conn.execute("SELECT * FROM notices WHERE id = ?", (id,))
    n = cur.fetchone()
    conn.close()
    if not n:
        flash('Notice not found.', 'danger')
        return redirect(url_for('index'))
    return render_template('view_notice.html', notice=n)
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username'].strip()
        password = request.form['password'].strip()

        conn = get_db()
        conn.row_factory = sqlite3.Row  # ✅ so we can access columns by name
        cur = conn.cursor()
        cur.execute("SELECT * FROM users WHERE username=?", (username,))
        user = cur.fetchone()
        conn.close()

        if user and check_password_hash(user['password_hash'], password):
            session['username'] = username

            if username.lower() == "admin":   # ✅ Admin login
                return redirect(url_for('admin'))
            else:                             # ✅ Normal user login
                return redirect(url_for('index'))
        else:
            flash("Invalid username or password!", "danger")

    return render_template("login.html")

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))


@app.route('/admin')
@login_required
@admin_required
def admin():
    conn = get_db()
    cur = conn.execute("SELECT * FROM notices ORDER BY created_at DESC")
    notices = cur.fetchall()
    conn.close()
    return render_template('admin.html', notices=notices)

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        username = request.form['username'].strip()
        password = request.form['password'].strip()

        if username.lower() == "admin":
            flash("This username is reserved.", "danger")
            return redirect(url_for('signup'))

        conn = get_db()
        cur = conn.cursor()

        # ✅ store hashed password instead of plain text
        cur.execute(
    "INSERT INTO users (username, password_hash) VALUES (?, ?)",
    (username, generate_password_hash(password))
)
        conn.commit()
        conn.close()

        flash("Account created! Please login.", "success")
        return redirect(url_for('login'))

    return render_template("signup.html")



@app.route('/admin/add', methods=['GET', 'POST'])
@login_required
@admin_required   # ✅ Only admin can add
def add_notice():
    if request.method == 'POST':
        title = request.form['title'].strip()
        content = request.form['content'].strip()
        category = request.form.get('category', '').strip() or None
        notice_date = request.form.get('notice_date') or None  

        if not title or not content:
            flash('Title and content are required.', 'warning')
            return redirect(url_for('add_notice'))

        conn = get_db()
        conn.execute(
            "INSERT INTO notices (title, content, category, notice_date) VALUES (?, ?, ?, ?)",
            (title, content, category, notice_date)
        )
        conn.commit()
        conn.close()

        flash('Notice added.', 'success')
        return redirect(url_for('admin'))

    return render_template('add_edit_notice.html', notice=None)


@app.route('/admin/edit/<int:id>', methods=['GET', 'POST'])
@login_required
@admin_required   # ✅ Only admin can edit
def edit_notice(id):
    conn = get_db()
    cur = conn.execute("SELECT * FROM notices WHERE id = ?", (id,))
    notice = cur.fetchone()
    if not notice:
        conn.close()
        flash('Notice not found.', 'danger')
        return redirect(url_for('admin'))

    if request.method == 'POST':
        title = request.form['title'].strip()
        content = request.form['content'].strip()
        category = request.form.get('category', '').strip() or None
        conn.execute("UPDATE notices SET title=?, content=?, category=? WHERE id=?",
                     (title, content, category, id))
        conn.commit()
        conn.close()
        flash('Notice updated.', 'success')
        return redirect(url_for('admin'))

    conn.close()
    return render_template('add_edit_notice.html', notice=notice)


@app.route('/admin/delete/<int:id>', methods=['POST'])
@login_required
@admin_required   # ✅ Only admin can delete
def delete_notice(id):
    conn = get_db()
    conn.execute("DELETE FROM notices WHERE id = ?", (id,))
    conn.commit()
    conn.close()
    flash('Notice deleted.', 'info')
    return redirect(url_for('admin'))


if __name__ == '__main__':
    app.run(debug=True)
    