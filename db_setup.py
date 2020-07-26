import os
from flasksite import db, bcrypt
from flasksite.models import User
db.create_all()

ADMIN_EMAIL = os.environ.get('ADMIN_EMAIL')
ADMIN_PASSWORD = os.environ.get('ADMIN_PASS')

if not User.query.filter_by(username='admin').first():
    hashed_password = bcrypt.generate_password_hash(ADMIN_PASSWORD).decode('utf-8')
    user = User(username='admin', email=ADMIN_EMAIL, password=hashed_password)
    db.session.add(user)
    db.session.commit()


