from flask import Flask, request, redirect, render_template, url_for, session
from flask_pymongo import PyMongo
from bson.objectid import ObjectId
from datetime import datetime
import time
import bcrypt
import random
import os

###########################################################
# SETUP
############################################################

app = Flask(__name__)

app.config["MONGO_URI"] = "mongodb://localhost:27017/taskDatabase"
mongo = PyMongo(app)

###########################################################
# GLOBAL VARIABLES
############################################################

current_time = datetime.now()

print(current_time)

############################################################
# MAIN ROUTES
############################################################


@app.route('/')
def homepage():
    if 'username' in session:
        current_user = session['username']

        return render_template('homepage.html', current_user=current_user)

    return render_template('homepage.html')


@app.route('/tasks')
def tasks():

    if 'username' in session:
        current_user = session['username']
        users_tasks = mongo.db.tasks.find({ 'created_by': session['username'] })
        context = {
            'users_tasks': users_tasks,
            'current_user': current_user,
            'current_time': current_time.timestamp()
        }

        return render_template('tasks.html', **context)

    return render_template('login.html')


@app.route('/account')
def account():
    current_user = session['username']

    return render_template('account.html', current_user=current_user)


@app.route('/create_task', methods=['POST', "GET"])
def create_task():

    if 'username' in session:
        tasks = mongo.db.tasks
        current_user = session['username']
        
        if request.method == 'POST':
            title = request.form['title']
            description = request.form['description']
            category = request.form['category']
            deadline = datetime.strptime(request.form['deadline'], '%Y-%m-%d')


            tasks.insert_one({
                'created_by': current_user,
                'title': title,
                'description': description,
                'category': category,
                'progression': {
                    'completed': False,
                    'completion_percentage': 50
                },
                'dates': {
                    'deadline': deadline.strftime('%B %d, %Y'),
                    'deadline_unix': deadline.timestamp(),
                    'date_created': current_time.strftime('%B %d, %Y'),
                    'date_created_unix': int(current_time.timestamp())
                }

            })

            return redirect(url_for('tasks'))

        return render_template('create_task.html', current_user=current_user)

    return render_template('login.html')



############################################################
# TASK MODIFICATION ROUTES
############################################################



@app.route('/delete_task/<task_id>')
def delete_task(task_id):

    mongo.db.tasks.delete_one({ '_id': ObjectId(task_id)})

    return redirect(url_for('tasks'))




@app.route('/task_details/<task_id>')
def task_details(task_id):

    task = mongo.db.tasks.find_one({ '_id': ObjectId(task_id)})

    return render_template('task_details.html', task=task)



@app.route('/mark_completion/<task_id>', methods=['POST', "GET"])
def mark_completion(task_id):

    task = mongo.db.tasks.find_one({'_id': ObjectId(task_id)})
    task_completion_status = task['progression']['completed']

    if task_completion_status is True:
        mongo.db.tasks.update_one(
            {'_id': ObjectId(task_id)},
            {
                '$set': {
                    'progression': {
                        'completed': False,
                        'completion_percentage': 25
                    }
                }
            }
        )
        return redirect(url_for('tasks'))
    elif task_completion_status is False:
        mongo.db.tasks.update_one(
            {'_id': ObjectId(task_id)},
            {
                '$set': {
                    'progression': {
                        'completed': True,
                        'completion_percentage': 100
                    }
                }
            }
        )
        return redirect(url_for('tasks'))

    return render_template('tasks.html')





































































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
            hashpass = bcrypt.hashpw(request.form['pass'].encode('utf-8'), bcrypt.gensalt())
            users.insert({'name': request.form['username'], 'password': hashpass})
            session['username'] = request.form['username']
            return redirect(url_for('homepage'))

        return 'That username already exists!'

    return render_template('register.html')


@app.route('/logout')
def logout():

    session.pop('username')

    return redirect(url_for('homepage'))


############################################################
############################################################


if __name__ == '__main__':
    app.secret_key = 'mysecret'
    app.run(debug=True)
