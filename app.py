from flask import Flask, request, redirect, render_template, url_for, session
from flask_pymongo import PyMongo
from bson.objectid import ObjectId
import bcrypt
import random
import os

###########################################################
# SETUP
############################################################

app = Flask(__name__)

app.config["MONGO_URI"] = "mongodb://localhost:27017/taskDatabase"
mongo = PyMongo(app)

############################################################
# ROUTES
############################################################


@app.route('/')
def homepage():
    if 'username' in session:
        current_user = session['username']

        return render_template('homepage.html', current_user=current_user)

    return render_template('homepage.html')


@app.route('/tasks')
def tasks():

    users_tasks = mongo.db.tasks.find({ 'created_by': session['username'] })

    

    return render_template('tasks.html', users_tasks=users_tasks)


@app.route('/create_task', methods=['POST', "GET"])
def create_task():

    if 'username' in session:
        tasks = mongo.db.tasks
        current_user = session['username']
        
        if request.method == 'POST':
            title = request.form['title']
            description = request.form['description']
            category = request.form['category']
            deadline = request.form['deadline']

            tasks.insert_one({
                'created_by': current_user,
                'title': title,
                'description': description,
                'category': category,
                'deadline': deadline,
            })

            return redirect(url_for('tasks'))

        return render_template('create_task.html', current_user=current_user)

    return render_template('login.html')

@app.route('/account')
def account():

    return render_template('account.html')


############################################################
# Authentication
############################################################


@app.route('/login', methods=['POST', "GET"])
def login():
    users = mongo.db.users

    if request.method == 'POST':
        login_user = users.find_one({'name': request.form['username']})
        if login_user:
            if bcrypt.hashpw(request.form['pass'].encode('utf-8'), login_user['password']) == login_user['password']:
                session['username'] = request.form['username']
                return redirect(url_for('homepage'))
        else:
            return 'Invalid username/password'

    return render_template('login.html')


@app.route('/register', methods=["POST", "GET"])
def register():

    if request.method == 'POST':
        users = mongo.db.users
        existing_user = users.find_one({'name': request.form['username']})

        if existing_user is None:
            hashpass = bcrypt.hashpw(
                request.form['pass'].encode('utf-8'), bcrypt.gensalt())
            users.insert(
                {'name': request.form['username'], 'password': hashpass})
            session['username'] = request.form['username']
            return redirect(url_for('homepage'))

        return 'That username already exists!'

    return render_template('register.html')


@app.route('/sign_out')
def sign_out():

    session.pop('username')

    return redirect(url_for('homepage'))


############################################################
############################################################


if __name__ == '__main__':
    app.secret_key = 'mysecret'
    app.run(debug=True)
