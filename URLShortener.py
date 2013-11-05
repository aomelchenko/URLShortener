# all the imports
from flask import Flask, request, session, g, redirect, url_for, abort, render_template, flash
import sqlite3
from contextlib import closing
from hashlib import md5





# configuration

DATABASE = '/tmp/urls.db'
DEBUG = True
SECRET_KEY = 'development key'
USERNAME = 'admin'
PASSWORD = 'default'



app = Flask(__name__)
app.config.from_object(__name__)

def connect_db():
    return sqlite3.connect(app.config['DATABASE'])

def init_db():
    with closing(connect_db()) as db:
        with app.open_resource('schema.sql', mode='r') as f:
            db.cursor().executescript(f.read())
        db.commit()

@app.before_request
def before_request():
    g.db = connect_db()

@app.teardown_request
def teardown_request(exception):
    db = getattr(g, 'db', None)
    if db is not None:
        db.close()


@app.route('/')
def show_entries():
    cur = g.db.execute('select original_url, shorten_url from entries order by id desc')
    entries = [dict(original_url=row[0], shorten_url=row[1]) for row in cur.fetchall()]
    return render_template('show_entries.html', entries=entries)

@app.route('/add', methods=['POST'])
def add_entry():
    if not session.get('logged_in'):
        abort(401)
    g.db.execute('insert into entries (original_url, shorten_url, faurls) values (?, ?, 0)',
                 [request.form['original_url'], 'http://127.0.0.1:5000/' + md5(request.form['original_url']).hexdigest()[0:5]])
    g.db.commit()
    flash('New entry was successfully posted')
    return redirect(url_for('show_entries'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    error = None
    if request.method == 'POST':
        if request.form['username'] != app.config['USERNAME']:
            error = 'Invalid username'
        elif request.form['password'] != app.config['PASSWORD']:
            error = 'Invalid password'
        else:
            session['logged_in'] = True
            flash('You were logged in')
            return redirect(url_for('show_entries'))
    return render_template('login.html', error=error)

@app.route('/logout')
def logout():
    session.pop('logged_in', None)
    flash('You were logged out')
    return redirect(url_for('show_entries'))


@app.route('/<short>')
def open_user_link(short):
    q = 'http://127.0.0.1:5000/' + short
    cur = g.db.execute("select original_url from entries where shorten_url = ?", (q, ))
    url = cur.fetchall()
    faurls = g.db.execute("select faurls from entries where shorten_url = ?", (q, ))
    f = faurls.fetchall()
    freq = g.db.execute("UPDATE entries SET faurls = ? where shorten_url = ?", (f[0][0]+1, q, ))
    freq.fetchall()

    return redirect(url[0][0])


if __name__ == '__main__':
    app.run()