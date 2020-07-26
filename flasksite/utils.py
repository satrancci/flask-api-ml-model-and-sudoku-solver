from flasksite import app
import os
import secrets
from PIL import Image

def save_picture(form_picture, folder='profile_pics'):
    random_hex = secrets.token_hex(8)
    _, f_ext = os.path.splitext(form_picture.filename)
    picture_fn = random_hex + f_ext
    picture_path = os.path.join(app.root_path, 'static/', folder, picture_fn)

    img = Image.open(form_picture)

    # Resize while keeping the original proportion
    width = 250
    width_percent = (width/float(img.size[0]))
    height_size = int((float(img.size[1])*float(width_percent)))
    img = img.resize((width,height_size), Image.ANTIALIAS)

    img.save(picture_path)

    return picture_fn


def generate_api_key():
    s = secrets.token_hex(32)
    return s