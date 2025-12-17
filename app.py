from flask import Flask, render_template, request, redirect, url_for, flash
from flask_login import UserMixin, login_user, login_required, logout_user, current_user, LoginManager
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from datetime import datetime
import os, time

app = Flask(__name__, template_folder="templates")
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///blogs.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = 'thisisasecretkey'

# Upload folder for images
UPLOAD_FOLDER = "static/uploads"
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

db = SQLAlchemy(app)

# Flask-Login setup
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

# change to project folder
# cd "C:\Users\Sanjay Krishna R\OneDrive\Music\Desktop\project 2"

# if venv not yet active
# .\venv\Scripts\Activate.ps1

# run the app with Python
# python .\app.py
# or, if 'python' isn't available, use:
# py -3 .\app.py
@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


# Models
class GFGBLOG(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(50))
    author = db.Column(db.String(20))
    post_date = db.Column(db.DateTime)
    content = db.Column(db.Text)
    image = db.Column(db.String(100))  # store uploaded image filename
    likes = db.relationship('Like', backref='post', lazy=True)


class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(20), nullable=False, unique=True)
    password = db.Column(db.String(200), nullable=False)


class Like(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    post_id = db.Column(db.Integer, db.ForeignKey('gfgblog.id'))


def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


# Routes
@app.route("/")
def hello_world():
    article = GFGBLOG.query.order_by(GFGBLOG.post_date.desc()).all()
    name = "guest" if current_user.is_anonymous else current_user.username
    return render_template('index.html', article=article, name=name)


@app.route('/about')
def about():
    return render_template('about.html')


@app.route('/addpost', methods=['POST', 'GET'])
@login_required
def addpost():
    if request.method == 'POST':
        title = request.form['title']
        author = current_user.username
        content = request.form['content']

        # Handle image upload safely
        image_file = request.files.get('image')
        filename = None
        if image_file and image_file.filename:
            if allowed_file(image_file.filename):
                safe_name = secure_filename(image_file.filename)
                filename = f"{int(time.time())}_{safe_name}"
                image_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                image_file.save(image_path)
            else:
                flash('Invalid image file type.', 'danger')
                return redirect(request.url)

        post = GFGBLOG(title=title, author=author,
                       content=content, post_date=datetime.now(),
                       image=filename)

        db.session.add(post)
        db.session.commit()
        flash("Post added successfully!", "success")
        return redirect(url_for('hello_world'))
    return render_template('add.html')


@app.route('/update/<int:id>', methods=['POST', 'GET'])
@login_required
def update(id):
    post = GFGBLOG.query.get_or_404(id)
    if request.method == 'POST':
        post.title = request.form['title']
        post.content = request.form['content']

        # update image if uploaded (safe handling)
        image_file = request.files.get('image')
        if image_file and image_file.filename:
            if allowed_file(image_file.filename):
                safe_name = secure_filename(image_file.filename)
                filename = f"{int(time.time())}_{safe_name}"
                image_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                image_file.save(image_path)
                post.image = filename
            else:
                flash('Invalid image file type.', 'danger')
                return redirect(request.url)

        db.session.commit()
        flash("Post updated!", "info")
        return redirect(url_for('hello_world'))
    return render_template('update.html', edit=post)


@app.route('/delete/<int:id>')
@login_required
def delete(id):
    post = GFGBLOG.query.get_or_404(id)
    db.session.delete(post)
    db.session.commit()
    flash("Post deleted!", "danger")
    return redirect(url_for('hello_world'))


@app.route('/like/<int:post_id>', methods=['POST'])
@login_required
def like(post_id):
    post = GFGBLOG.query.get_or_404(post_id)
    existing_like = Like.query.filter_by(user_id=current_user.id, post_id=post.id).first()

    if existing_like:
        db.session.delete(existing_like)  # Unlike if already liked
        flash("You unliked the post.", "info")
    else:
        new_like = Like(user_id=current_user.id, post_id=post.id)
        db.session.add(new_like)
        flash("You liked the post!", "success")

    db.session.commit()
    return redirect(url_for('hello_world'))


@app.route('/login', methods=['POST', 'GET'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = User.query.filter_by(username=username).first()

        if not user or not check_password_hash(user.password, password):
            flash('Invalid username or password', 'danger')
            return redirect(url_for('login'))
        else:
            login_user(user)
            flash("Logged in successfully!", "success")
            return redirect(url_for('hello_world'))

    return render_template('login.html')


@app.route('/signin', methods=['POST', 'GET'])
def signin():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        hashed_pw = generate_password_hash(password, method='pbkdf2:sha256')
        user = User(username=username, password=hashed_pw)

        db.session.add(user)
        db.session.commit()
        flash('Account created! You can now log in.', 'success')
        return redirect(url_for('login'))

    return render_template("index.html")


@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash("Logged out successfully!", "info")
    return redirect(url_for('home'))


# Main
if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)



