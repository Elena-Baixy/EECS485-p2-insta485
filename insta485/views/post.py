"""

Insta485 post view.

URLs include:
/

"""
import os
import uuid
import pathlib
import flask
import arrow
import insta485


@insta485.app.route('/posts/<postid_url_slug>/', methods=['GET'])
def get_posts(postid_url_slug):
    """Get_post."""
    if 'username' in flask.session:
        connection = insta485.model.get_db()
        cur = connection.execute(
            "SELECT filename, owner, postid, created "
            "FROM posts "
            "WHERE postid=?", (postid_url_slug, )
        )
        post = cur.fetchone()

        present = arrow.utcnow()
        created_time_obj = arrow.get(post.get("created"))
        created_time_obj = created_time_obj.humanize(present)
        post["created"] = created_time_obj

        for_user = connection.execute(
            "SELECT username, filename "
            "FROM users "
            "WHERE username = ?",
            (post["owner"], )
        )

        user = for_user.fetchone()
        print("Here is the user:", user)

        for_likes = connection.execute(
            "SELECT owner, postid, COUNT(*) as count "
            "FROM likes "
            "WHERE postid=?", (postid_url_slug, )
        )
        like = for_likes.fetchall()

        for_unlikes = connection.execute(
            "SELECT owner, postid "
            "FROM likes "
            "WHERE owner == ? AND postid ==? ",
            (flask.session["username"], postid_url_slug, )
        )
        unlike = for_unlikes.fetchone()

        for_comments = connection.execute(
            "SELECT owner, postid, text "
            "FROM comments "
            "WHERE postid=?", (postid_url_slug, )
        )
        comment = for_comments.fetchall()

    # Add database info to context
        context = {"posts": post, "users": user, "likes": like,
                   "comments": comment, "unlikes": unlike}

        return flask.render_template("post.html", **context,
                                     logname=flask.session["username"],
                                     postid=postid_url_slug)

    return flask.redirect(flask.url_for('login'))


@insta485.app.route('/explore/', methods=['GET'])
def explore():
    """explore."""
    if 'username' not in flask.session:
        return flask.redirect(flask.url_for('login'))
    logname = flask.session["username"]
    connection = insta485.model.get_db()

    not_following2 = connection.execute(
            "SELECT username, filename "
            "FROM users "
            "WHERE username NOT IN "
            "(SELECT username2 FROM following WHERE username1=?)",
            (logname, )
    )
    not_following1 = not_following2.fetchall()
    print(not_following1)
    context = {"not_following": not_following1}

    return flask.render_template("explore.html", **context, logname=logname)


@insta485.app.route('/posts/', methods=['POST'])
def post_posts():
    """post_post."""
    if 'username' not in flask.session:
        return flask.redirect(flask.url_for('login'))
    operation1 = flask.request.form["operation"]
    logname = flask.session["username"]

    connection = insta485.model.get_db()
    cur = connection.cursor()
    if operation1 == "create":
        print("create")
        fileobj = flask.request.files["file"]
        print(fileobj)
        if fileobj is None:
            flask.abort(400)
        print("Not here")
        filename1 = fileobj.filename
        stem = uuid.uuid4().hex
        suffix = pathlib.Path(filename1).suffix.lower()
        uuid_basename = f"{stem}{suffix}"
        newobj = insta485.app.config["UPLOAD_FOLDER"]
        fileobj.save(newobj/uuid_basename)
        cur.execute("INSERT INTO posts (filename, owner)"
                    "VALUES (?,?)",
                    (uuid_basename, logname))
        connection.commit()
    else:
        postid1 = flask.request.form["postid"]
        file1 = cur.execute("SELECT * FROM posts WHERE postid=?",
                            (postid1, )).fetchone()
        print("file1", file1)
        filename1 = file1["filename"]
        print("filename", filename1)
        owner1 = flask.session["username"]
        if owner1 != file1["owner"]:
            flask.abort(403)
        os.remove(insta485.app.config["UPLOAD_FOLDER"]/filename1)
        sql = 'DELETE FROM posts WHERE postid=?'
        cur.execute(sql, (postid1,))
        connection.commit()

    target = flask.request.args.get("target")
    if target is None:
        return flask.redirect(flask.url_for('users', name=logname))
    return flask.redirect(flask.request.args.get("target"))


@insta485.app.route('/likes/', methods=['POST'])
def post_likes():
    """post_post."""
    if 'username' not in flask.session:
        return flask.redirect(flask.url_for('login'))
    postid1 = flask.request.form["postid"]
    owner1 = flask.session["username"]
    print("----------------postid1", postid1)
    # get connection
    connection = insta485.model.get_db()
    cur = connection.cursor()
    # create a like
    if flask.request.form["operation"] == "like":
        # tries to create a like that has already existed
        result = cur.execute(
                             "SELECT  1 "
                             "FROM likes "
                             "WHERE postid == ? AND owner == ?",
                             (postid1, owner1,)
                            ).fetchall()
        if result:
            flask.abort(409)
        cur.execute("INSERT INTO likes "
                    "(owner, postid) VALUES (?,?)",
                    (owner1, postid1))
        connection.commit()
    else:
        # tries to delete a like that has not existed
        result = cur.execute(
                             "SELECT  1 "
                             "FROM likes "
                             "WHERE postid == ? AND owner == ?",
                             (postid1, owner1,)
                            ).fetchall()
        if not result:
            flask.abort(409)
        sql = 'DELETE FROM likes WHERE postid =?'
        cur.execute(sql, (postid1,))
        connection.commit()
    # target is not set
    if flask.request.args.get('target') is None:
        return flask.redirect(flask.url_for('show_index'))
    return flask.redirect(flask.request.args.get("target"))


@insta485.app.route('/comments/', methods=['POST'])
def post_comments():
    """post_comments."""
    if 'username' not in flask.session:
        return flask.redirect(flask.url_for('login'))
    owner1 = flask.session["username"]
    operation1 = flask.request.form["operation"]
    # commentid1 = flask.request.form["commentid"]
    # print("------------------commentid1:",commentid1)

    # print("------------------operation1:",operation1)
    # get connection
    connection = insta485.model.get_db()
    cur = connection.cursor()
    # create comment
    if operation1 == "create":
        text1 = flask.request.form["text"]
        postid1 = flask.request.form["postid"]

        # if text is empty
        if text1 == "":
            print("----text1:")
            flask.abort(400)
        cur.execute("INSERT INTO comments (owner, postid, text)"
                    "VALUES (?,?,?)",
                    (owner1, postid1, text1))
        connection.commit()
    # delete a comment
    else:
        # if the owner isn't the poster
        commentid1 = flask.request.form["commentid"]
        print("-----------commentid1:", commentid1)
        result = cur.execute("SELECT * FROM comments "
                             "WHERE commentid==?",
                             (commentid1, )).fetchone()
        if result["owner"] != owner1:
            flask.abort(403)
        sql = 'DELETE FROM comments WHERE commentid=?'
        cur.execute(sql, (commentid1,))
        connection.commit()
    # target is not set
    if flask.request.args.get('target') is None:
        return flask.redirect(flask.url_for('show_index'))
    return flask.redirect(flask.request.args.get("target"))


@insta485.app.route('/following/', methods=['POST'])
def post_following():
    """postfollowing."""
    if 'username' not in flask.session:
        return flask.redirect(flask.url_for('login'))
    username2 = flask.request.form["username"]
    operation1 = flask.request.form["operation"]
    owner1 = flask.session["username"]
    # get connection
    connection = insta485.model.get_db()
    cur = connection.cursor()
    # follow people
    if operation1 == "follow":
        # tries to follow the person that has already been followed
        result = cur.execute(
                             "SELECT  1 "
                             "FROM following "
                             "WHERE username1 == ? AND username2 == ?",
                             (owner1, username2,)
                            ).fetchall()

        if result:
            flask.abort(409)
        cur.execute("INSERT INTO following (username1, username2)"
                    "VALUES (?,?)",
                    (owner1, username2))
        connection.commit()
    else:
        # tries to unfollow the person that has not already been followed

        result = cur.execute(
                             "SELECT  1 "
                             "FROM following "
                             "WHERE username1 == ? AND username2 == ?",
                             (owner1, username2,)
                            ).fetchall()

        print("------------result:", result)
        if not result:
            flask.abort(409)
        sql = 'DELETE FROM following WHERE username1=? AND username2=?'
        cur.execute(sql, (owner1, username2,))
        connection.commit()
    # ?target is not setcd
    # ?target is not set
    if flask.request.args.get('target') is None:
        return flask.redirect(flask.url_for('show_index'))
    return flask.redirect(flask.request.args.get("target"))


@insta485.app.route('/accounts/delete/', methods=['GET'])
def delete():
    """delete."""
    logname = flask.session['username']
    return flask.render_template("delete.html", logname=logname)
