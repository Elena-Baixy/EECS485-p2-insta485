"""
Insta485 index (main) view.

URLs include:
/
"""
import flask
import insta485


@insta485.app.route('/users/<name>/', methods=['GET'])
def users(name):
    """users."""
    if 'username' not in flask.session:
        return flask.redirect(flask.url_for('login'))

    connection = insta485.model.get_db()
    user_exist = connection.execute(
            "SELECT username "
            "FROM users "
            "WHERE username == ? ",
            (name, )
    )
    user_exist = user_exist.fetchall()
    if not user_exist:
        flask.abort(404)

    logname_following = 0
    if flask.session['username'] != name:
        is_following = connection.execute(
            "SELECT username1, username2 "
            "FROM following "
            "WHERE username1 == ? AND username2 == ?",
            (flask.session['username'], name, )
        )
        logname_following = is_following.fetchall()
        if not logname_following:
            logname_following = 0
        else:
            logname_following = 1

    posts_num = connection.execute(
                                  "SELECT  postid, COUNT(*) as count "
                                  "FROM posts "
                                  "WHERE owner == ?",
                                  (name, )
                                  )
    posts_num = posts_num.fetchall()

    for_following = connection.execute(
                                      "SELECT  username1, COUNT(*) as count "
                                      "FROM following "
                                      "WHERE username1 == ?",
                                      (name, )
                                      )

    following = for_following.fetchall()

    for_follower = connection.execute(
                                     "SELECT  username2, COUNT(*) as count "
                                     "FROM following "
                                     "WHERE username2 == ?",
                                     (name, )
                                     )
    follower = for_follower.fetchall()

    for_name = connection.execute(
                                 "SELECT fullname "
                                 "FROM users "
                                 "WHERE username == ?",
                                 (name, )
                                 )
    names = for_name.fetchall()

    for_post = connection.execute(
                                 "SELECT filename, postid "
                                 "FROM posts "
                                 "WHERE owner == ?",
                                 (name, )
                                 )
    posts = for_post.fetchall()

    context = {"is_following": logname_following, "posts_num": posts_num,
               "following": following, "follower": follower, "fullname": names,
               "posts": posts}

    return flask.render_template("user.html", **context,
                                 logname=flask.session['username'],
                                 username=name)
    # return flask.redirect(flask.url_for('show_index'))


@insta485.app.route('/users/<name>/followers/', methods=['GET'])
def user_followers(name):
    """user_followers."""
    if 'username' not in flask.session:
        return flask.redirect(flask.url_for('login'))
    logname = flask.session['username']
    connection = insta485.model.get_db()
    user_exist = connection.execute(
                                   "SELECT username "
                                   "FROM users "
                                   "WHERE username == ? ",
                                   (name, )
                                   )
    user_exist = user_exist.fetchall()
    if not user_exist:
        flask.abort(404)

    for_follower = connection.execute(
                                     "SELECT following."
                                     "username1, users.filename "
                                     "FROM following "
                                     "INNER JOIN users "
                                     "ON following.username1 = users.username "
                                     "WHERE following.username2 == ?",
                                     (name, )
                                     )
    followers = for_follower.fetchall()

    logname_following = connection.execute(
                                          "SELECT  username2 "
                                          "FROM following "
                                          "WHERE username1 == ?",
                                          (logname, )
                                          )
    log_following = logname_following.fetchall()

    print(followers)
    for follower in followers:
        log_is_following = 0
        for following in log_following:
            if follower.get("username1") == following.get("username2"):
                log_is_following = 1
                follower["log_is_following"] = 1
        if not log_is_following:
            follower["log_is_following"] = 0
        else:
            follower["log_is_following"] = 1

    print(followers)

    context = {"user_followers": followers}
    # return flask.redirect(flask.url_for('show_index'))
    return flask.render_template("followers.html", **context,
                                 logname=logname, username=name,
                                 isFollowing=0)


@insta485.app.route('/users/<name>/following/', methods=['GET'])
def user_following(name):
    """user_following."""
    if 'username' not in flask.session:
        return flask.redirect(flask.url_for('login'))
    logname = flask.session['username']
    connection = insta485.model.get_db()
    user_exist = connection.execute(
                                   "SELECT username "
                                   "FROM users "
                                   "WHERE username == ? ",
                                   (name, )
                                   )
    user_exist = user_exist.fetchall()
    if not user_exist:
        flask.abort(404)

    for_following = connection.execute(
                                      "SELECT following.username2, "
                                      "users.filename "
                                      "FROM following "
                                      "INNER JOIN users "
                                      "ON "
                                      "following.username2 = users.username "
                                      "WHERE following.username1 == ?",
                                      (name, )
                                      )
    followings = for_following.fetchall()
    # print(followings)

    logname_following = connection.execute(
                                          "SELECT  username2 "
                                          "FROM following "
                                          "WHERE username1 == ?",
                                          (logname, )
                                          )
    log_followings = logname_following.fetchall()

    # print(followings)
    for following in followings:
        log_is_following = 0
        for log_following in log_followings:
            if following.get("username2") == log_following.get("username2"):
                log_is_following = 1
                following["log_is_following"] = 1
        if not log_is_following:
            following["log_is_following"] = 0
        else:
            following["log_is_following"] = 1

    print(followings)

    context = {"user_following": followings}
    # return flask.redirect(flask.url_for('follower'))
    return flask.render_template("following.html",
                                 **context, logname=logname, username=name)
