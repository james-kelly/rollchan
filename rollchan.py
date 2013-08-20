from flask import Flask, url_for, render_template, request, redirect
from sqlalchemy.sql.expression import null
from sqlalchemy import desc
import memcache

from database import db_session
import models

# Set to True to make the application run faster.
USE_MEMCACHE = False
PAGE_SIZE = 100

app = Flask(__name__)

if USE_MEMCACHE:
    memc = memcache.Client(['127.0.0.1:11211'], debug=1);


@app.teardown_appcontext
def shutdown_session(exception=None):
    db_session.remove()


@app.route('/<board>/', methods=['POST'])
@app.route('/<board>/res/<int:post_id>', methods=['POST'])
def upload_file(board, post_id=None):
    # Create the post
    post = models.Post(subject=request.form.get('subject'),
                       comment=request.form.get('comment'),
                       parent_id=post_id)
    db_session.add(post)
    db_session.flush()

    # Upload the file if present
    f = request.files['file']

    if f.filename:
        extension = get_extension(f)
        filename = "{0}.{1}".format(post.generate_filename(), extension)
        path = "{0}/static/{1}".format(app.root_path, filename)

        f.save(path)

        post.filename = filename
        post.mimetype = f.mimetype

    db_session.commit()

    # Redirect to page or post
    if post_id:
        return redirect(url_for('reply', board=board, post_id=post_id))
    else:
        return redirect(url_for('page', board=board))


@app.route('/<board>/')
@app.route('/<board>/<int:page_id>/')
def page(board, page_id=0):
    q = db_session.query(models.Post)
    q = q.filter(models.Post.parent_id == null())
    q = q.order_by(desc(models.Post.created))
    q = q.offset(PAGE_SIZE * page_id)
    q = q.limit(PAGE_SIZE)

    if USE_MEMCACHE:
        key = "page_{0}_{1}".format(board, page_id)
        page = memc.get(key)
        if not page:
            page = q.all()
            memc.set(key, page, time=30)
    else:
        page = q.all()

    return render_template('page.html', posts=page, board=board, num_children=4)


@app.route('/<board>/res/<int:post_id>')
def reply(board, post_id):
    q = db_session.query(models.Post)
    q = q.filter(models.Post.id == post_id)

    if USE_MEMCACHE:
        key = "post_{0}_{1}".format(board, post_id)
        post = memc.get(key)
        if not post:
            post = q.first()
            memc.set(key, post, time=30)
    else:
        post = q.first()

    db_session.add(post)

    return render_template('page.html', posts=[post], board=board, num_children=9999, is_reply=True)


def get_extension(f):
    return f.filename.split(".")[1]


if __name__ == '__main__':
    app.debug = True
    app.run()
