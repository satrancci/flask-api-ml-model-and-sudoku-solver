from datetime import datetime
from itsdangerous import TimedJSONWebSignatureSerializer as Serializer
from flasksite import db, login_manager, app
from flask_login import UserMixin
from datetime import datetime

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


class User(db.Model, UserMixin):
    #__tablename__ = "User"

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(20), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    image_file = db.Column(db.String(20), nullable=False, default='default.jpg')
    password = db.Column(db.String(60), nullable=False)
    posts = db.relationship('Post', backref='author', lazy=True)
    api_keys = db.relationship('API_Key', backref='keyowner', lazy=True)
    emotion_predictions = db.relationship('EmotionPrediction', backref='uploader', lazy=True)

    def get_reset_token(self, expires_sec=1800):
        s = Serializer(app.config['SECRET_KEY'], expires_sec)
        return s.dumps({'user_id': self.id}).decode('utf-8')


    @staticmethod
    def verify_reset_token(token):
        s = Serializer(app.config['SECRET_KEY'])
        try:
            user_id = s.loads(token)['user_id']
        except:
            return None
        return User.query.get(user_id)


    def __repr__(self):
        return f"User('{self.username}', '{self.email}', '{self.image_file}')"


class Post(db.Model):
    #__tablename__ = "Post"

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    date_posted = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    content = db.Column(db.Text, nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)

    def __lt__(self, other):
        return self.date_posted < other.date_posted

    def __repr__(self):
        t = self.date_posted
        return f"Post('{self.title}', '{t.strftime('%Y-%m-%d %H:%M:%S')} UTC', {self.content})"

class API_Key(db.Model):
    #__tablename__ = "API_Key"

    id = db.Column(db.Integer, primary_key=True)
    key = db.Column(db.String(100), nullable=False)
    date_created = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    
    def __repr__(self):
        return f"API_KEY('{self.key}','{self.user_id}','{self.date_created}')"

class EmotionPrediction(db.Model):
    #__tablename__ = "EmotionPrediction"

    id = db.Column(db.Integer, primary_key=True)
    image_file = db.Column(db.String(20), nullable=False)
    emotion_class = db.Column(db.String(100), nullable=False)
    date_uploaded = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False, default='Anonymous User')

    def __repr__(self):
        return f"EmotionPrediction('{self.image_file}','{self.user_id}','{self.date_uploaded}')"



