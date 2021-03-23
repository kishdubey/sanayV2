import os

from flask import Flask, render_template, request, redirect, url_for, flash
from flask_login import LoginManager, login_user, current_user, login_required, logout_user
from flask_socketio import SocketIO, send, emit, join_room, leave_room
from forms import *
from models import *

import pickle
import tensorflow as tf
from  keras.preprocessing.text import Tokenizer
from keras.preprocessing.sequence import pad_sequences

from time import localtime, strftime

# Initiate App
app = Flask(__name__)
app.secret_key = 'REPLACE LATER'#os.environ.get('DATABASE_URL')

# Setting up SQL database
app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://joeqoeubnocowo:7ae138822b0a6611ce524674312e724400bff93bf8566f789a9ccc21c5802240@ec2-54-161-239-198.compute-1.amazonaws.com:5432/d6711g835q321m' #os.environ.get('DATABASE_URL')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# Login Manager to handle user handling
login = LoginManager(app)
login.init_app(app)

@login.user_loader
def load_user(id):
    return User.query.get(int(id))

# Web Sockets for messaging
socketio = SocketIO(app)

# Default rooms
ROOMS = ["coding", "memes", "games", "animals"]

@app.route('/', methods=['GET', 'POST'])
def index():
    """Registration Page"""
    reg_form = RegistrationForm()

    if reg_form.validate_on_submit():
        username = reg_form.username.data
        password = sha256.hash(reg_form.password.data)

        user = User(username=username, password=password)
        db.session.add(user)
        db.session.commit()

        flash('Registered succesfully. Please login.', 'success')
        return redirect(url_for('login'))

    return render_template("index.html", form=reg_form)

@app.route('/login', methods=['GET', 'POST'])
def login():
    """Login Page"""
    login_form = LoginForm()

    if login_form.validate_on_submit():
        user_object = User.query.filter_by(username=login_form.username.data).first()
        login_user(user_object)
        return redirect(url_for('chat'))

    return render_template("login.html", form=login_form)

@app.route("/logout", methods=['GET'])
def logout():
    """Logout Page, Redirects to Login"""
    logout_user()
    flash('Logged Out succesfully', 'success')
    return redirect(url_for('login'))

@app.route("/chat", methods=['GET', 'POST'])
def chat():
    """Chat Page"""
    # if user is not authenticated
    if not current_user.is_authenticated:
        flash('Please login', 'danger')
        return redirect(url_for('login'))

    return render_template('chat.html', username=current_user.username, rooms=ROOMS)

@app.errorhandler(404)
def page_not_found(e):
    """If page not found"""
    return render_template('error.html'), 404

@socketio.on('message')
def message(data):
    """Sending Message to Client"""
    msg = data['msg']
    username = data['username']
    room = data['room']
    time_stamp = strftime('%b-%d %I:%M%p', localtime())
    prediction = predict(msg, 'tf_models/tokenizer.pickle', 'tf_models/bilstm.h5')

    send({'msg': msg, 'username': username, 'time_stamp': time_stamp, 'prediction': prediction}, room=room)

@socketio.on('join')
def join(data):
    """Joining Room"""
    username = data['username']
    room = data['room']
    join_room(room)

    send({"msg": username + " has joined the " + room + " room."}, room=room)

@socketio.on('leave')
def leave(data):
    """Leaving Room"""
    username = data['username']
    room = data['room']
    leave_room(room)

    send({"msg": username + " has left the room"}, room=room)

def _get_key(value):
    dictionary={'Joy':0,'Anger':1,'Love':2,'Sadness':3,'Fear':4,'Surprise':5}
    for key,val in dictionary.items():
          if (val==value):
            return key

def predict(text, tokenizer, model):
    with open(tokenizer, 'rb') as handle:
        tokenizer = pickle.load(handle)

    model = tf.keras.models.load_model(model)

    sent_list = []
    sent_list.append(text)
    sent_seq = tokenizer.texts_to_sequences(sent_list)
    sentence_padded = pad_sequences(sent_seq, maxlen = 80, padding='post')
    prediction = _get_key(model.predict_classes(sentence_padded))
    print(prediction)
    return prediction

if __name__ == '__main__':
    socketio.run(app, debug=True)
