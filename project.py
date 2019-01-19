#!/usr/bin/env python 2.7.12

from flask import (Flask, render_template,
                   request, redirect, url_for,
                   flash, jsonify)
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from database_setup import Base, Bookstore, StoreItem, User
from flask import session as login_session
import random
import string
from oauth2client.client import flow_from_clientsecrets
from oauth2client.client import FlowExchangeError
import httplib2
import json
from flask import make_response
import requests

app = Flask(__name__)

CLIENT_ID = json.loads(
    open('client_secrets.json', 'r').read())['web']['client_id']
APPLICATION_NAME = "bookstoreApp"

# Connect to Database and create database session
engine = create_engine('sqlite:///bookstorelistwithusers.db?' +
                       'check_same_thread=False')
DBSession = sessionmaker(bind=engine)
session = DBSession()


# Create anti-forgery state token
@app.route('/login')
def showLogin():
    state = ''.join(random.choice(string.ascii_uppercase + string.digits)
                    for x in xrange(32))
    login_session['state'] = state
    return render_template('login.html', STATE=state)


@app.route('/gconnect', methods=['POST'])
def gconnect():
    # Validate state token
    if request.args.get('state') != login_session['state']:
        response = make_response(json.dumps('Invalid state parameter.'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response
    # Obtain authorization code
    code = request.data

    try:
        # Upgrade the authorization code into a credentials object
        oauth_flow = flow_from_clientsecrets('client_secrets.json', scope='')
        oauth_flow.redirect_uri = 'postmessage'
        credentials = oauth_flow.step2_exchange(code)
    except FlowExchangeError:
        response = make_response(
            json.dumps('Failed to upgrade the authorization code.'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Check that the access token is valid.
    access_token = credentials.access_token
    url = ('https://www.googleapis.com/oauth2/v1/tokeninfo?access_token=%s'
           % access_token)
    h = httplib2.Http()
    result = json.loads(h.request(url, 'GET')[1])
    # If there was an error in the access token info, abort.
    if result.get('error') is not None:
        response = make_response(json.dumps(result.get('error')), 500)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Verify that the access token is used for the intended user.
    gplus_id = credentials.id_token['sub']
    if result['user_id'] != gplus_id:
        response = make_response(
            json.dumps("Token's user ID doesn't match given user ID."), 401)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Verify that the access token is valid for this app.
    if result['issued_to'] != CLIENT_ID:
        response = make_response(
            json.dumps("Token's client ID does not match app's."), 401)
        print "Token's client ID does not match app's."
        response.headers['Content-Type'] = 'application/json'
        return response

    stored_access_token = login_session.get('access_token')
    stored_gplus_id = login_session.get('gplus_id')
    if stored_access_token is not None and gplus_id == stored_gplus_id:
        response = make_response(json.dumps('Current user ' +
                                            'is already connected.'), 200)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Store the access token in the session for later use.
    login_session['access_token'] = credentials.access_token
    login_session['gplus_id'] = gplus_id

    # Get user info
    userinfo_url = "https://www.googleapis.com/oauth2/v1/userinfo"
    params = {'access_token': credentials.access_token, 'alt': 'json'}
    answer = requests.get(userinfo_url, params=params)

    data = answer.json()

    login_session['username'] = data['name']
    login_session['picture'] = data['picture']
    login_session['email'] = data['email']

    # if user is exists, if it doesn't make a new one
    user_id = getUserID(login_session['email'])
    if not user_id:
        user_id = createUser(login_session)
    login_session['user_id'] = user_id

    output = ''
    output += '<h1>Welcome, '
    output += login_session['username']
    output += '!</h1>'
    output += '<img src="'
    output += login_session['picture']
    output += ' " style = "width: 300px; height: 300px;'\
              'border-radius: 150px;'\
              '-webkit-border-radius: 150px;-moz-border-radius: 150px;"> '
    flash("you are now logged in as %s" % login_session['username'])
    print "done!"
    return output


# DISCONNECT - Revoke a current user's token and reset their login_session
@app.route('/gdisconnect')
def gdisconnect():
    access_token = login_session.get('access_token')
    if access_token is None:
        print 'Access Token is None'
        response = make_response(json.dumps('Current user not connected.'),
                                 401)
        response.headers['Content-Type'] = 'application/json'
        return response
    print 'In gdisconnect access token is %s', access_token
    print 'User name is: '
    print login_session['username']
    url = 'https://accounts.google.com/o/oauth2/revoke?token=%s'\
          % login_session['access_token']
    h = httplib2.Http()
    result = h.request(url, 'GET')[0]
    print 'result is '
    print result
    if result['status'] == '200':
        del login_session['access_token']
        del login_session['gplus_id']
        del login_session['username']
        del login_session['email']
        del login_session['picture']
        response = make_response(json.dumps('Successfully disconnected.'), 200)
        response.headers['Content-Type'] = 'application/json'
        return response
    else:
        response = make_response(json.dumps('Failed to revoke token ' +
                                            'for given user.', 400))
        response.headers['Content-Type'] = 'application/json'
        return response


# JSON APIs to view Bookstore
@app.route('/bookstore/<int:bookstore_id>/JSON')
def bookstoreListJSON(bookstore_id):
    bookstore = session.query(Bookstore).filter_by(id=bookstore_id).one()
    items = session.query(StoreItem).filter_by(
        bookstore_id=bookstore_id).all()
    return jsonify(StoreItems=[i.serialize for i in items])


@app.route('/bookstore/<int:bookstore_id>/<int:item_id>/JSON')
def storeItemJSON(bookstore_id, item_id):
    Store_Item = session.query(StoreItem).filter_by(id=item_id).one()
    return jsonify(Store_Item=Store_Item.serialize)


@app.route('/bookstore/JSON')
def bookstoresJSON():
    bookstores = session.query(Bookstore).all()
    return jsonify(bookstores=[r.serialize for r in bookstores])


# Show a Bookstore itemsList
@app.route('/bookstore/<int:bookstore_id>/')
@app.route('/bookstore/<int:bookstore_id>/list')
def bookstoreList(bookstore_id):
    bookstore = session.query(Bookstore).filter_by(id=bookstore_id).one()
    items = session.query(StoreItem).filter_by(bookstore_id=bookstore_id).all()
    if 'username' not in login_session:
        return render_template('PublicitemsList.html',
                               bookstore=bookstore,
                               items=items, bookstore_id=bookstore_id)
    else:
        return render_template('itemsList.html', bookstore=bookstore,
                               items=items, bookstore_id=bookstore_id)


# Create a new item
@app.route('/bookstore/<int:bookstore_id>/new/', methods=['GET', 'POST'])
def newItem(bookstore_id):
    if 'username' not in login_session:
        return redirect('/login')
    if request.method == 'POST':
        newItem = StoreItem(name=request.form['name'],
                            description=request.form['description'],
                            price=request.form['price'],
                            category=request.form['category'],
                            bookstore_id=bookstore_id,
                            user_id=login_session['user_id'])
        session.add(newItem)
        session.commit()
        flash("new menu item created!")
        return redirect(url_for('bookstoreList', bookstore_id=bookstore_id))
    else:
        return render_template('newitem.html', bookstore_id=bookstore_id)


# Edit a item
@app.route('/bookstore/<int:bookstore_id>/<int:item_id>/edit',
           methods=['GET', 'POST'])
def editItem(bookstore_id, item_id):
    if 'username' not in login_session:
        return redirect('/login')
    editedItem = session.query(StoreItem).filter_by(id=item_id).one()
    bookstore = session.query(Bookstore).filter_by(id=bookstore_id).one()
    itemToDelete = session.query(StoreItem).filter_by(id=item_id).one()
    if editedItem.user_id != login_session['user_id']:
        return " <script>function myFunction() "\
               "{alert ('Your are not authorized to delete this item. "\
               "Please create your own resturant in order to delete.');}"\
               "</script><bodyonload= myFunction()''>"

    if request.method == 'POST':
        if request.form['name']:
            editedItem.name = request.form['name']
        if request.form['description']:
            editedItem.description = request.form['description']
        if request.form['price']:
            editedItem.price = request.form['price']
        if request.form['category']:
            editedItem.course = request.form['category']
        session.add(editedItem)
        session.commit()
        return redirect(url_for('bookstoreList', bookstore_id=bookstore_id))
    else:
        return render_template('edititem.html', bookstore_id=bookstore_id,
                               item_id=item_id, item=editedItem)


# Delete a menu item
@app.route('/bookstore/<int:bookstore_id>/<int:item_id>/delete',
           methods=['GET', 'POST'])
def deleteItem(bookstore_id, item_id):
    if 'username' not in login_session:
        return redirect('/login')
    itemToDelete = session.query(StoreItem).filter_by(id=item_id).one()
    if itemToDelete.user_id != login_session['user_id']:
        return " <script>function myFunction() "\
               "{alert ('Your are not authorized to delete this item. "\
               "Please create your own resturant in order to delete.');}"\
               "</script><bodyonload= myFunction()''>"
    if request.method == 'POST':
        session.delete(itemToDelete)
        session.commit()
        return redirect(url_for('bookstoreList', bookstore_id=bookstore_id))
    else:
        return render_template('deleteitem.html', item=itemToDelete)


# Show all bookstores
@app.route('/')
@app.route('/bookstore/')
def showBookstores():
    bookstores = session.query(Bookstore).order_by(Bookstore.name)
    return render_template('bookstores.html', bookstores=bookstores)


# Show all items in a Bookstore
@app.route('/bookstore/<int:bookstore_id>/')
def showList(bookstore_id):
    bookstore = session.query(Bookstore).filter_by(id=bookstore_id).one()
    creator = getUserInfo(bookstore.user_id)
    items = session.query(StoreItem).filter_by(bookstore_id=bookstore_id).all()
    condition = ('username'not in login_session or
                 creator.id != login_session['user_id'])
    if condition:
        return render_template('PublicitemsList.html', items=items,
                               bookstore=bookstore, creator=creator)
    else:
        return render_template('itemsList.html', items=items,
                               bookstore=bookstore, creator=creator)


# User Helper Functions
def createUser(login_session):
    newUser = User(name=login_session['username'], email=login_session[
                   'email'], picture=login_session['picture'])
    session.add(newUser)
    session.commit()
    user = session.query(User).filter_by(email=login_session['email']).one()
    return user.id


def getUserInfo(user_id):
    user = session.query(User).filter_by(id=user_id).one()
    return user


def getUserID(email):
    try:
        user = session.query(User).filter_by(email=email).one()
        return user.id
    except:
        return None


if __name__ == '__main__':
    app.secret_key = 'super_secret_key'
    app.debug = True
    app.run(host='0.0.0.0', port=5000)
