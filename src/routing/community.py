from flask import flash, redirect, render_template, request, session, url_for

from lib import storage
from lib.database import sql
from lib.models import Post, PostComment, PostLike, PostSaved, User, UserFollow
from main import app
from utils import require_login


@app.context_processor
def init_community():
    user_id = session.get("user_id")

    def is_liked(likes, user_id):
        return any(like.user_id == user_id for like in likes)

    def is_saved(saves, user_id):
        return any(save.user_id == user_id for save in saves)

    def is_followed(follows, user_id, follower_id):
        return any(follow.user_id == user_id and follow.follower_id == follower_id for follow in follows)

    def is_comment(comments, user_id):
        return any(comment.user_id == user_id for comment in comments)

    return dict(user_id=user_id, is_liked=is_liked, is_saved=is_saved, is_followed=is_followed, is_comment=is_comment)


@app.route("/community")
@app.route("/community/explore")
@require_login
def community():
    posts = sql.session.query(Post).order_by(Post.created_at.desc()).all()
    # users = sql.session.query(UserFollow).all()
    # users = sql.session.query(User).join(UserFollow, UserFollow.user_id == User.id).filter(UserFollow.follower_id == session["user_id"]).all()
    session["user_id"]
    users = (
        sql.session.query(User)
        .join(UserFollow, User.id == UserFollow.user_id)
        .filter(UserFollow.follower_id == session["user_id"])
        .all()
    )
    return render_template("community.html", posts=posts, users = users)


@app.route("/community/saved")
@require_login
def community_saved():
    user_id = session.get("user_id")
    posts = sql.session.query(PostSaved).filter_by(user_id=user_id).all()
    return render_template("community-saved.html", posts=posts)


@app.route("/community/post", methods=["GET", "POST"])
@require_login
def community_post():
    if request.method == "POST":
        user_id = session.get("user_id")
        content = request.form["content"]
        image = request.files["image"]

        image_url = None

        if image:
            if storage.check_format(image, storage.media_extensions):
                image_url = storage.upload_file(image)
            else:
                flash("Not allowed")
                return redirect(url_for("community_post"))

        post = Post(
            user_id=user_id,
            content=content,
            image_url=image_url,
        )

        sql.session.add(post)
        sql.session.commit()

        return redirect(url_for("community"))

    return render_template("community-post.html")


@app.route("/community/posts/<id>", methods=["GET", "POST"])
@require_login
def community_edit(id):
    post = sql.session.query(Post).filter_by(id=id).first()

    if request.method == "POST":
        post.content = request.form["content"]
        image = request.files["image"]

        if image:
            if storage.check_format(image, storage.media_extensions):
                image_url = storage.upload_file(image)
                post.image_url = image_url
            else:
                flash("Not allowed")
                return redirect(url_for("community_edit", id=id))

        sql.session.commit()

        return redirect(url_for("community"))

    return render_template("community-edit.html", post=post)


@app.route("/community/posts/<id>/delete", methods=["POST"])
@require_login
def community_delete(id):
    post = sql.session.query(Post).filter_by(id=id).first()
    sql.session.delete(post)
    sql.session.commit()
    return redirect(url_for("community"))


@app.route("/community/posts/<post_id>/like", methods=["GET", "POST"])
def toggle_like(post_id):
    user_id = session.get("user_id")
    like = sql.session.query(PostLike).filter_by(post_id=post_id, user_id=user_id).first()

    if not like:
        like = PostLike(post_id=post_id, user_id=user_id)
        sql.session.add(like)
    else:
        sql.session.delete(like)

    sql.session.commit()

    return redirect(request.referrer)


@app.route("/community/posts/<user_id>/follow", methods=["GET", "POST"])
def toggle_follow(user_id):
    follower_id = session.get("user_id")
    follow = sql.session.query(UserFollow).filter_by(user_id=user_id, follower_id=follower_id).first()

    if not follow:
        follow = UserFollow(user_id=user_id, follower_id=follower_id)
        sql.session.add(follow)
    else:
        sql.session.delete(follow)

    sql.session.commit()

    return redirect(request.referrer)


@app.route("/community/posts/<post_id>/save", methods=["GET", "POST"])
def toggle_save(post_id):
    user_id = session.get("user_id")  # Get the current logged-in user's ID

    # Check if the post is already saved by the user
    save = sql.session.query(PostSaved).filter_by(post_id=post_id, user_id=user_id).first()

    if not save:
        # If the post is not already saved, add it to the PostSaved table
        save = PostSaved(post_id=post_id, user_id=user_id)
        sql.session.add(save)
    else:
        # If the post is already saved, remove it from the PostSaved table
        sql.session.delete(save)

    # Commit the changes to the database
    sql.session.commit()

    # Redirect back to the community page (or wherever you want)
    return redirect(request.referrer)

@app.route("/community/posts/<post_id>/share", methods=["GET", "POST"])
def share_post(post_id):
    user_id = session.get("user_id")  # Get the logged-in user's ID

    if not user_id:
        return redirect(url_for("login"))  # Ensure the user is logged in

    # Get users that the logged-in user is following
    followings = (
        sql.session.query(User)
        .join(UserFollow, UserFollow.user_id == User.id)
        .filter(UserFollow.follower_id == user_id)  # Get users that the logged-in user follows
        .all()
    )

    return render_template("share_modal.html", post_id=post_id, followings=followings)


@app.route("/community/posts/<post_id>/comment", methods=["GET", "POST"])
def post_comment(post_id):
    user_id = session.get("user_id")

    message = request.form["comment_text"]
    user_id = session.get("user_id")

    print(message)
    new_comment = PostComment(
        message=message,
        post_id=post_id,
        user_id=user_id,
    )

    sql.session.add(new_comment)
    sql.session.commit()

    return redirect(url_for("community"))