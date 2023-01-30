"""
Insta485 index (main) view.

URLs include:
/
"""
import os
import uuid
import hashlib
import pathlib
import flask
from flask import send_from_directory
import arrow
import insta485


# for index.html
@insta485.app.route('/')
def show_index():
    """Display / route."""
    if 'username' in flask.session:

        # Connect to database
        connection = insta485.model.get_db()
        # log_followings_and_self list is all users logname following
        log_followings_and_self = connection.execute(
            "SELECT username2 "
            "FROM following "
            "WHERE username1 = ?",
            (flask.session['username'], )
        )
        log_followings_and_self = log_followings_and_self.fetchall()
        # append user himself to the list
        logname_self = {'username2': flask.session['username']}
        log_followings_and_self.append(logname_self)

        # Query database

        post = connection.execute(
            "SELECT filename, owner, postid, created "
            "FROM posts "
            "ORDER BY postid DESC "
        )
        post = post.fetchall()

        present = arrow.utcnow()
        for one_post in post:
            created_time_obj = arrow.get(one_post.get("created"))
            created_time_obj = created_time_obj.humanize(present)
            one_post["created"] = created_time_obj

        user = connection.execute(
            "SELECT username, filename "
            "FROM users "
            # "WHERE username != ?",
            # (logname, )
        )

        user = user.fetchall()

        like = connection.execute(
            "SELECT owner, postid, COUNT(*) as count "
            "FROM likes "
            "GROUP BY postid "
        )
        like = like.fetchall()

        like_post = connection.execute(
            "SELECT postid "
            "FROM likes "
            "WHERE owner == ?",
            (flask.session['username'], )
        )
        like_post = like_post.fetchall()

        all_postid = connection.execute(
            "SELECT postid "
            "FROM posts "
        )

        all_postid = all_postid.fetchall()

        unlike = []
        for row in all_postid:
            if row not in like_post:
                unlike.append(row['postid'])

        comment = connection.execute(
            "SELECT owner, postid, text "
            "FROM comments "
        )
        comment = comment.fetchall()

        # Add database info to context
        context = {"posts": post, "users": user, "likes": like,
                   "comments": comment, "unlikes": unlike,
                   "like_posts": like_post,
                   "log_followings_and_self": log_followings_and_self}
        return flask.render_template("index.html",
                                     **context,
                                     logname=flask.session['username'])

    return flask.redirect(flask.url_for('login'))


@insta485.app.route('/uploads/<filename>')
def show_img(filename):
    """show_img."""
    if 'username' not in flask.session:
        flask.abort(403)
    print("test upload file")
    connection = insta485.model.get_db()
    for_post_file = connection.cursor()
    for_post_file.execute(
        "SELECT filename "
        "FROM posts "
        "WHERE filename = ?",
        (filename, )
    )
    post_file = for_post_file.fetchall()

    for_user_file = connection.cursor()
    for_user_file.execute(
        "SELECT filename "
        "FROM users "
        "WHERE filename = ?",
        (filename, )
    )
    user_file = for_user_file.fetchall()

    if (len(post_file) == 0 and len(user_file) == 0):
        flask.abort(404)

    return send_from_directory(insta485.app.config['UPLOAD_FOLDER'], filename)


@insta485.app.route('/accounts/login/', methods=['GET'])
def login():
    """show_img."""
    if 'username' in flask.session:
        return flask.redirect(flask.url_for('show_index'))

    print("DEBUG flask.session:", flask.session)
    return flask.render_template("login.html")


@insta485.app.route('/accounts/create/', methods=['GET'])
def create():
    """show_img."""
    if 'username' in flask.session:
        return flask.redirect(flask.url_for('edit'))

    return flask.render_template("create.html")


@insta485.app.route('/accounts/edit/', methods=['GET'])
def edit():
    """Get edit."""
    if 'username' not in flask.session:
        return flask.redirect(flask.url_for('login'))
    connection = insta485.model.get_db()

    # Query database
    logname = flask.session['username']
    print("debug:", logname)
    cur = connection.execute(
        "SELECT filename, fullname, email "
        "FROM users "
        "WHERE username = ?",
        (logname, )
    )
    users = cur.fetchall()
    context = {"users": users}
    return flask.render_template("edit.html", **context, logname=logname)


@insta485.app.route('/accounts/password/', methods=['GET'])
def update_password():
    """show_img."""
    if 'username' not in flask.session:
        return flask.redirect(flask.url_for('login'))

    logname = flask.session['username']
    return flask.render_template("password.html", logname=logname)


@insta485.app.route('/accounts/logout/', methods=['POST'])
def logout():
    """show_img."""
    if 'username' not in flask.session:
        return flask.redirect(flask.url_for('login'))
    print("DEBUG Logout: user has logged out")
    flask.session.clear()
    return flask.redirect(flask.url_for('login'))


@insta485.app.route('/accounts/', methods=['POST'])
def accounts():
    """show_img."""
    if flask.request.form['operation'] == 'login':
        return accounts_login()
    if flask.request.form['operation'] == 'create':
        return accounts_create()
    if flask.request.form['operation'] == 'update_password':
        return accounts_update_password()
    if flask.request.form['operation'] == 'delete':
        return accounts_delete()
    # if flask.request.form['operation'] == 'edit_account':
    return accounts_edit_account()


# if any of the field is empty
def accounts_login():
    """Docstring."""
    connection = insta485.model.get_db()
    algorithm = 'sha512'
    hash_obj = hashlib.new(algorithm)
    if ((flask.request.form['username'] == " ")
       or (flask.request.form['password'] == " ")):
        flask.abort(400)

    query_parameter = flask.request.args.get("target")
    print("DEBUG query_parameter:", query_parameter)
    username = flask.request.form['username']
    enteredpassword = flask.request.form['password']
    cur = connection.execute(
        "SELECT password FROM users "
        "WHERE username = ? ",
        (username,)
    )
    password = cur.fetchall()
    if len(password) == 0:
        flask.abort(403)
    password = password[0].get("password")
    print("DEBUG Enteredpassword", enteredpassword)
    password_list = password.split('$')
    salt = password_list[1]

    # algorithm = 'sha512'
    # hash_obj = hashlib.new(algorithm)
    password_salted = salt + enteredpassword
    hash_obj.update(password_salted.encode('utf-8'))
    password_hash = hash_obj.hexdigest()
    salted_enter_password = "$".join([algorithm, salt, password_hash])
    print("DEBUG saltedEnterPassword:", salted_enter_password)
    print("DEBUG password_db:", password)

    # password authentication
    if password != salted_enter_password:
        flask.abort(403)
    flask.session['username'] = flask.request.form['username']
    flask.session['password'] = flask.request.form['password']
    print("DEBUG flask.session:", flask.session)
    return flask.redirect(flask.url_for('show_index'))


def accounts_create():  # create
    """Docstring."""
    connection = insta485.model.get_db()
    algorithm = 'sha512'
    hash_obj = hashlib.new(algorithm)
    # Error check: empty
    if (
        (flask.request.form['username'] == " ") or
        (flask.request.form['password'] == " ") or
        (flask.request.form['fullname'] == " ") or
        (flask.request.form['email'] == " ") or
        (flask.request.files.get('file') is None)
    ):
        flask.abort(400)

    # get information
    password = flask.request.form['password']
    fileobj = flask.request.files["file"]

    # Error check: already exist:
    check_user = connection.execute(
        "SELECT 1 FROM users "
        "WHERE username = ? ",
        (flask.request.form['username'],)
    )
    check_user = check_user.fetchall()
    if len(check_user) == 1:
        flask.abort(409)

    # add uuid for file storage
    stem = uuid.uuid4().hex
    suffix = pathlib.Path(fileobj.filename).suffix.lower()
    uuid_basename = f"{stem}{suffix}"
    fileobj.save(insta485.app.config["UPLOAD_FOLDER"]
                 / uuid_basename)

    # password storgae
    # algorithm = 'sha512'

    salt = uuid.uuid4().hex
    password_salted = salt + password
    hash_obj.update(password_salted.encode('utf-8'))
    password_hash = hash_obj.hexdigest()
    password_db_string = "$".join([algorithm, salt, password_hash])
    # print(password_db_string)

    # store into db
    cur = connection.cursor()
    cur.execute(
        "INSERT INTO users "
        "(username, fullname, email, filename, password) "
        "VALUES (?,?,?,?,?)",
        (flask.request.form['username'],
         flask.request.form['fullname'],
         flask.request.form['email'],
         uuid_basename, password_db_string)
    )
    connection.commit()
    target1 = flask.request.args.get("target")
    if 'username' not in flask.session:
        flask.session['username'] = flask.request.form['username']
        flask.session['password'] = flask.request.form['password']
        return flask.redirect(flask.url_for('show_index'))
    if target1 is None:
        return flask.redirect(flask.url_for('show_index'))
    return flask.redirect(target1)
    # how to store password and  username into database


def accounts_update_password():  # password
    """Docstring."""
    connection = insta485.model.get_db()
    algorithm = 'sha512'
    hash_obj = hashlib.new(algorithm)
    # Error check: login
    if 'username' not in flask.session:
        flask.abort(403)

    # Error check: empty
    if (
        (flask.request.form['password'] == " ")
        or (flask.request.form['new_password1'] == " ")
        or (flask.request.form['new_password2'] == " ")
    ):
        flask.abort(400)

    # initialize
    connection = insta485.model.get_db()
    old_password = flask.request.form['password']
    new_password1 = flask.request.form['new_password1']
    new_password2 = flask.request.form['new_password2']

    if new_password1 != new_password2:
        flask.abort(401)

    # check old password
    cur = connection.execute(
        "SELECT password "
        "FROM users "
        "WHERE username = ?",
        (flask.session['username'], )
    )
    password = cur.fetchall()
    password = password[0].get("password")
    password_list = password.split('$')
    salt = password_list[1]
    password_salted = salt + old_password
    hash_obj = hashlib.new(algorithm)
    hash_obj.update(password_salted.encode('utf-8'))
    salted_old_password = "$".join([algorithm,
                                   salt, hash_obj.hexdigest()])

    if password != salted_old_password:
        flask.abort(403)

    # change new password
    salt = uuid.uuid4().hex
    new_password_salted = salt + new_password1
    hash_obj = hashlib.new(algorithm)
    hash_obj.update(new_password_salted.encode('utf-8'))
    new_password_hash = hash_obj.hexdigest()
    new_password_db_string = "$".join([algorithm, salt, new_password_hash])
    print(new_password_db_string)

    # store into db
    cur = connection.cursor()
    cur.execute(
        "UPDATE users "
        "SET password = ? "
        "WHERE username = ? ",
        (new_password_db_string,
         flask.session['username'], )
    )
    connection.commit()

    if 'username' not in flask.session:
        return flask.redirect(flask.url_for('login'))
    if flask.request.args.get("target") is None:
        return flask.redirect(flask.url_for('show_index'))

    return flask.redirect(flask.request.args.get("target"))


def accounts_edit_account():  # edit
    """Docstring."""
    connection = insta485.model.get_db()
    # Error check: login
    if 'username' not in flask.session:
        flask.abort(403)

    # Error check: empty
    if (
        (flask.request.form['fullname'] == " ")
        or (flask.request.form['email'] == " ")
    ):
        flask.abort(400)

    # get information
    logname = flask.session['username']
    fullname = flask.request.form['fullname']
    email = flask.request.form['email']
    if flask.request.files.get('file') is None:
        # print("is none?")
        cur = connection.cursor()
        for_refresh = connection.execute(
            "SELECT filename "
            "FROM users "
            "WHERE username = ? ",
            (logname, )
        )
        refresh = for_refresh.fetchall()
        cur.execute(
            "UPDATE users "
            "SET fullname = ?, email = ?,filename = ? "
            "WHERE username = ? ",
            (fullname, email, refresh[0]['filename'], logname)
        )
        connection.commit()
    else:
        # if add new file then delete
        fileobj = flask.request.files["file"]
        # add uuid for file storage
        filename = fileobj.filename
        stem = uuid.uuid4().hex
        suffix = pathlib.Path(filename).suffix.lower()
        uuid_basename = f"{stem}{suffix}"

        # Save files to disk
        path = insta485.app.config["UPLOAD_FOLDER"]/uuid_basename
        print(path)
        fileobj.save(path)

        # store into db
        cur = connection.cursor()
        for_delete = connection.execute(
            "SELECT filename "
            "FROM users "
            "WHERE username = ? ",
            (logname, )
        )
        newobj = insta485.app.config["UPLOAD_FOLDER"]
        os.remove(newobj/for_delete.fetchall()[0]['filename'])
        cur.execute(
            "UPDATE users "
            "SET fullname = ?, email = ?, filename = ? "
            "WHERE username = ? ",
            (fullname, email, uuid_basename, logname)
        )
        connection.commit()

    if 'username' not in flask.session:
        return flask.redirect(flask.url_for('login'))

    if flask.request.args.get("target") is None:
        return flask.redirect(flask.url_for('show_index'))

    return flask.redirect(flask.request.args.get("target"))
    # how to store password and  username into database


def accounts_delete():
    """Docstring."""
    # Error check: login
    if 'username' not in flask.session:
        flask.abort(403)
    logname = flask.session['username']
    connection = insta485.model.get_db()
    # Delete the post from the database
    connection.execute(
        "DELETE FROM posts WHERE owner = ?",
        (logname, )
    )
    # Delete the following info
    connection.execute(
        "DELETE FROM following WHERE username1 = ?",
        (logname, )
    )
    # Delete the comments info
    connection.execute(
        "DELETE FROM comments WHERE owner = ?",
        (logname, )
    )
    # Delete the like info
    connection.execute(
        "DELETE FROM likes WHERE owner = ?",
        (logname, )
    )

    # delete user icon
    for_delete = connection.execute(
            "SELECT filename "
            "FROM users "
            "WHERE username = ? ",
            (logname, )
    )
    deletion = for_delete.fetchall()
    newobj = insta485.app.config["UPLOAD_FOLDER"]
    delete_path = newobj/deletion[0]['filename']
    os.remove(delete_path)

    # Delete the users info
    connection.execute(
        "DELETE FROM users WHERE username = ?",
        (logname, )
    )

    target1 = flask.request.args.get("target")
    if 'username' not in flask.session:
        flask.session.clear()
        return flask.redirect(flask.url_for('login'))

    if target1 is None:
        flask.session.clear()
        return flask.redirect(flask.url_for('show_index'))
    flask.session.clear()
    return flask.redirect(target1)
