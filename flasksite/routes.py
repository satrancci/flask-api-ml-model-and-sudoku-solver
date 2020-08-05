import os
import secrets
from PIL import Image
from flask import render_template, url_for, flash, redirect, request, abort, jsonify
from flasksite import app, db, bcrypt, mail, graph, API_DOCUMENTATION_LINK
from flasksite.forms import (RegistrationForm, LoginForm, UpdateAccountForm,
                             PostForm, RequestResetForm, ResetPasswordForm, UploadImage,
                             GenerateToken, SolveSudoku)
from flasksite.models import User, Post, API_Key, EmotionPrediction
from flask_login import login_user, current_user, logout_user, login_required
from flask_mail import Message
from flasksite.ml_model.image import predict_emotion
from flasksite.utils import save_picture, generate_api_key
from flasksite.sudoku.sudoku_solver import Sudoku, preprocess_sudoku, postprocess_sudoku, validate_input

@app.route("/")
def home():
    return render_template('home.html')

@app.route("/blog")
def blog():
    page = request.args.get('page', 1, type=int)
    posts = Post.query.order_by(Post.date_posted.desc()).paginate(page=page, per_page=5)
    return render_template('blog.html', posts=posts)


@app.route("/api_documentation")
def api_documentation():
    return render_template('api_documentation.html', title = 'API Documentation', link=API_DOCUMENTATION_LINK) 

@app.route("/projects")
def projects():
    return render_template('projects.html', title='My Projects')


@app.route("/register", methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('home'))
    form = RegistrationForm()
    if form.validate_on_submit():
        hashed_password = bcrypt.generate_password_hash(form.password.data).decode('utf-8')
        user = User(username=form.username.data, email=form.email.data, password=hashed_password)
        db.session.add(user)
        db.session.commit()
        flash('Your account has been created! You are now able to log in', 'success')
        return redirect(url_for('login'))
    return render_template('register.html', title='Register', form=form)


@app.route("/login", methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('home'))
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user and bcrypt.check_password_hash(user.password, form.password.data):
            login_user(user, remember=form.remember.data)
            next_page = request.args.get('next')
            return redirect(next_page) if next_page else redirect(url_for('home'))
        else:
            flash('Login Unsuccessful. Please check email and password', 'danger')
    return render_template('login.html', title='Login', form=form)


@app.route("/logout")
def logout():
    logout_user()
    return redirect(url_for('home'))



@app.route("/account", methods=['GET', 'POST'])
@login_required
def account():
    form = UpdateAccountForm()
    if form.validate_on_submit():
        if form.picture.data:
            picture_file = save_picture(form.picture.data)
            current_user.image_file = picture_file
        current_user.username = form.username.data
        current_user.email = form.email.data
        db.session.commit()
        flash('Your account has been updated!', 'success')
        return redirect(url_for('account'))
    elif request.method == 'GET':
        form.username.data = current_user.username
        form.email.data = current_user.email
    image_file = url_for('static', filename='profile_pics/' + current_user.image_file)
    return render_template('account.html', title='Account',
                           image_file=image_file, form=form)


@app.route("/post/new", methods=['GET', 'POST'])
@login_required
def new_post():
    form = PostForm()
    if form.validate_on_submit():
        post = Post(title=form.title.data, content=form.content.data, author=current_user)
        db.session.add(post)
        db.session.commit()
        flash('Your post has been created!', 'success')
        return redirect(url_for('home'))
    return render_template('create_post.html', title='New Post',
                           form=form, legend='New Post')


@app.route("/post/<int:post_id>")
def post(post_id):
    post = Post.query.get_or_404(post_id)
    return render_template('post.html', title=post.title, post=post)


@app.route("/post/<int:post_id>/update", methods=['GET', 'POST'])
@login_required
def update_post(post_id):
    post = Post.query.get_or_404(post_id)
    if post.author != current_user:
        abort(403)
    form = PostForm()
    if form.validate_on_submit():
        post.title = form.title.data
        post.content = form.content.data
        db.session.commit()
        flash('Your post has been updated!', 'success')
        return redirect(url_for('post', post_id=post.id))
    elif request.method == 'GET':
        form.title.data = post.title
        form.content.data = post.content
    return render_template('create_post.html', title='Update Post',
                           form=form, legend='Update Post')


@app.route("/post/<int:post_id>/delete", methods=['POST'])
@login_required
def delete_post(post_id):
    post = Post.query.get_or_404(post_id)
    if post.author != current_user:
        abort(403)
    db.session.delete(post)
    db.session.commit()
    flash('Your post has been deleted!', 'success')
    return redirect(url_for('home'))


@app.route("/user/<string:username>")
def user_posts(username):
    page = request.args.get('page', 1, type=int)
    user = User.query.filter_by(username=username).first_or_404()
    posts = Post.query.filter_by(author=user)\
        .order_by(Post.date_posted.desc())\
        .paginate(page=page, per_page=5)
    return render_template('user_posts.html', posts=posts, user=user)


def send_reset_email(user):
    token = user.get_reset_token()
    msg = Message('Password Reset Request',
                  sender='noreply@demo.com',
                  recipients=[user.email])
    msg.body = f'''To reset your password, visit the following link:
{url_for('reset_token', token=token, _external=True)}

If you did not make this request then simply ignore this email and no changes will be made.
'''
    mail.send(msg)


@app.route("/reset_password", methods=['GET', 'POST'])
def reset_request():
    if current_user.is_authenticated:
        return redirect(url_for('home'))
    form = RequestResetForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        send_reset_email(user)
        flash('An email has been sent with instructions to reset your password.', 'info')
        return redirect(url_for('login'))
    return render_template('reset_request.html', title='Reset Password', form=form)


@app.route("/reset_password/<token>", methods=['GET', 'POST'])
def reset_token(token):
    if current_user.is_authenticated:
        return redirect(url_for('home'))
    user = User.verify_reset_token(token)
    if user is None:
        flash('That is an invalid or expired token', 'warning')
        return redirect(url_for('reset_request'))
    form = ResetPasswordForm()
    if form.validate_on_submit():
        hashed_password = bcrypt.generate_password_hash(form.password.data).decode('utf-8')
        user.password = hashed_password
        db.session.commit()
        flash('Your password has been updated! You are now able to log in', 'success')
        return redirect(url_for('login'))
    return render_template('reset_token.html', title='Reset Password', form=form)


###############################################


@app.route("/predict", methods=['GET', 'POST'])
def predict():
    form = UploadImage()
    if form.validate_on_submit():
        if form.picture.data:
            picture_fn = save_picture(form.picture.data, folder='ml_pics')       
            image_file = os.path.join('./flasksite/static/ml_pics',picture_fn)
            with graph.as_default():
                pred = predict_emotion(image_file)

            if current_user.is_authenticated:
                pic = EmotionPrediction(image_file=picture_fn, emotion_class = pred, uploader=current_user)
                db.session.add(pic)
                db.session.commit()
                return redirect(url_for('display_predictions'))
            else:
                flash(f"Your prediction is:  {pred.upper()}", 'success')
    return render_template('predict.html', title='Predict',
                           form=form)


@app.route("/predictions", methods=['GET'])
@login_required
def display_predictions():
    predictions = EmotionPrediction.query.filter_by(user_id=current_user.id).all()[::-1]
    display_path = 'static/ml_pics/'
    return render_template('predictions.html', title='User Emotion Predictions', predictions=predictions,
                        path=display_path, user=current_user.username, email=current_user.email)



@app.route("/api/tokens", methods=['GET', 'POST'])
@login_required
def api_keys():
    keys = API_Key.query.filter_by(user_id=current_user.id).all()[::-1]
    form = GenerateToken()
    if request.method == 'POST':
        if form.validate_on_submit():
            new_key = generate_api_key()
            api_key = API_Key(key=new_key, keyowner=current_user)
            db.session.add(api_key)
            db.session.commit()
            flash('Your API key has been generated!', 'success')
            return redirect(url_for('api_keys'))
    return render_template('api_keys.html', title = 'User API keys', form=form,
                            keys=keys, user=current_user.username, email=current_user.email)


@app.route("/api/posts/all", methods=['GET'])
def api_all_posts():
    author_id = None
    try:
        token = request.args['token']
        keys = API_Key.query.all()
        for key in keys:
            if key.key == token:
                author_id = int(key.user_id)
                break
        if not author_id:
            return "Token is invalid"
    except:
        return 'You need to provide a token with a query'
    posts = Post.query.filter_by(user_id=author_id).all()[::-1] # reverse to show the latest post first
    response = [ ( post.title,post.date_posted.strftime("%m/%d/%Y, %H:%M:%S")+" UTC" ) for post in posts]
    return jsonify(response) if response else "You have not published any posts"

@app.route("/api/posts/new", methods=['POST'])
def api_new_post():
    author_id = None
    try:
        token = request.args['token']
        keys = API_Key.query.all()
        for key in keys:
            if key.key == token:
                author_id = int(key.user_id)
                break
        if not author_id:
            return "Token is invalid"
    except:
        return 'You need to provide a token with a query'
    title = request.args.get('title')
    content = request.args.get('content')
    author = User.query.filter_by(id = author_id).first()
    post = Post(title=title, content=content, author=author)
    db.session.add(post)
    db.session.commit()
    posts = Post.query.filter_by(user_id=author_id, title=title, content=content).all() # a very unlikely edge case: there may be multiple posts with same attributes :)
    if not posts:
        return "Could not retrieve post from the database"
    posts.sort() # based on operator overlading __lt__ in modules.py. We get the latest post from the list of duplicates
    return f"The post has been successfully created: {request.url_root}post/{posts[-1].id}"


@app.route("/api/posts/last", methods=['GET'])
def api_get_last_post():
    author_id = None
    try:
        token = request.args['token']
        keys = API_Key.query.all()
        for key in keys:
            if key.key == token:
                author_id = int(key.user_id)
                break
        if not author_id:
            return "Token is invalid"
    except:
        return 'You need to provide a token with a query'
    posts = Post.query.filter_by(user_id = author_id).all()
    if not posts:
        return "You haven't posted any posts!"
    return f"Your last post is: {posts[-1]} and is located at {request.url_root}post/{posts[-1].id}"


@app.route("/api/posts/delete", methods=['DELETE'])
def api_gelete_last_post():
    author_id = None
    try:
        token = request.args['token']
        keys = API_Key.query.all()
        for key in keys:
            if key.key == token:
                author_id = int(key.user_id)
                break
        if not author_id:
            return "Token is invalid"
    except:
        return 'You need to provide a token with a query'
    posts = Post.query.filter_by(user_id = author_id).all()
    if not posts:
        return "You haven't posted any posts!"
    post_to_delete = posts[-1]
    db.session.delete(post_to_delete)
    db.session.commit()
    if post_to_delete in Post.query.filter_by(user_id = author_id).all():
        return "An error occurred while deleting a post"
    return f"Your last post {post_to_delete} has been successfully deleted."


@app.route("/api/emoclassifier", methods=['POST'])
def emoclassifierAPI():
    author_id = None
    try:
        token = request.args['token']
        keys = API_Key.query.all()
        for key in keys:
            if key.key == token:
                author_id = int(key.user_id)
                break
        if not author_id:
            return "Token is invalid"
    except:
        return 'You need to provide a token with a query'

    try:
        image = request.files["image"]
        picture_fn = save_picture(image, folder='ml_pics')
        image_predict_fn = os.path.join('./flasksite/static/ml_pics',picture_fn)
        with graph.as_default():
            pred = predict_emotion(image_predict_fn)
    except:
        return "You need to attach an image with a query"

    author = User.query.filter_by(id = author_id).first()
    pic = EmotionPrediction(image_file=picture_fn, emotion_class = pred, uploader=author)
    db.session.add(pic)
    db.session.commit()
    return pred


@app.route("/sudoku_solver", methods=['GET', 'POST'])
def sudoku_solver():
    form = SolveSudoku()
    if form.validate_on_submit():
        position = form.position.data
        if not validate_input(position):
            flash('Your input is not valid!', 'danger')
            return redirect(url_for('sudoku_solver'))
        matrix = preprocess_sudoku(position)
        s = Sudoku(matrix)
        solution = s.solve()
        if solution:
            flash('Your sudoku puzzle has been solved!', 'success')
            res = postprocess_sudoku(matrix) # convert back to string of length 81
            return redirect(url_for('sudoku_result', res=res))
        else:
            flash('Your sudoku puzzle has no solution', 'danger')
    return render_template('sudoku.html', title = 'Sudoku Solver', form=form)

@app.route("/sudoku_result", methods=['GET'])
def sudoku_result():
    res = request.args.get('res')
    matrix = preprocess_sudoku(res)
    matrix = [list(map(int, row)) for row in matrix] # convert to int for better display in the template
    return render_template('sudoku_result.html', title = 'Your sudoku was solved!',  matrix=matrix)


@app.route("/api/solve_sudoku", methods=['POST'])
def api_solve_sudoku():
    author_id = None
    try:
        token = request.args['token']
        keys = API_Key.query.all()
        for key in keys:
            if key.key == token:
                author_id = int(key.user_id)
                break
        if not author_id:
            return "Token is invalid"
    except:
        return 'You need to provide a token with a query'
    try:
        position = request.args['position']
    except:
        return "Query parameter must be POSITION"
    if not validate_input(position):
        return "Your input is not valid! Position must be strictly of size 81. Denote an empty cell as '0' or '.' , everything else as {1,2,...,9}"
    matrix = preprocess_sudoku(position)
    s = Sudoku(matrix)
    solution = s.solve()
    if solution:
        res = postprocess_sudoku(matrix)
        res_formatted = ''
        for i in range(0,len(res),9):
            res_formatted += res[i:i+9]+'\n'
        return f"Solution:\n {res_formatted}"
    else:
        return 'Your sudoku puzzle has no solution'
    