from flasksite import app
import os
from PIL import Image
from keras.preprocessing.image import img_to_array
from keras.models import load_model
import cv2
import numpy as np


def predict_emotion(img_path):

    detection_model_path = os.path.join(app.root_path, 'ml_model/haarcascades','haarcascade_frontalface_default.xml')
    emotion_model_path =  os.path.join(app.root_path, 'ml_model/models','mini_XCEPTION_AffectNet_stratified_with_loss_.60-0.70.hdf5')

    face_detection = cv2.CascadeClassifier(detection_model_path)
    emotion_classifier = load_model(emotion_model_path, compile=False)
    EMOTIONS = ["angry","disgust","scared", "happy", "sad", "surprised","neutral"]

    frame = cv2.imread(img_path, 0) # 0 to read in grayscale
    faces = face_detection.detectMultiScale(frame,scaleFactor=1.1,minNeighbors=5,minSize=(30,30),flags=cv2.CASCADE_SCALE_IMAGE)

    label = 'Face could not be detected!'
    if len(faces) > 0:
        faces = sorted(faces, reverse=True,key=lambda x: (x[2] - x[0]) * (x[3] - x[1]))[0]
        (fX, fY, fW, fH) = faces
        roi = frame[fY:fY + fH, fX:fX + fW]
        roi = cv2.resize(roi, (48, 48))
        roi = roi.astype("float") / 255.0
        roi = img_to_array(roi)
        roi = np.expand_dims(roi, axis=0)
        preds = emotion_classifier.predict(roi)[0]
        label = EMOTIONS[preds.argmax()]
    
    
    return label
