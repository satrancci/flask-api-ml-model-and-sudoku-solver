# Deploying ML model with Flask

The emotion classification model `/flasksite/ml_model/models/mini_XCEPTION_AffectNet_stratified_with_loss_.60-0.70.hdf5` was developed in the spring 2020 as the requirement for the final project for CS5750 Machine Learning class at Saint Louis University. The model was trained on FER-2013 [[5]] and AffectNet [[3]] datasets. 

The goal of this project was to deploy the model on the web using Flask framework, and also make it available via an API. The API documentation can be accessed [here][6].

Later, a sudoku solver was added to this project, which is also available in the web application and via an API.


### References:

1. Arriaga, O et al. (2017). <em>Face detection and emotion classification</em>. [Link][1]
2. Kumar, A. (2018). <em>Demonstration of Facial Emotion Recognition on Real Time Video Using CNN : Python & Keras</em>. [Link][2]
3. Mahoor, M. (2017). <em>AffectNet</em>. [Link][3]
4. Schaefer, C. (2018). <em>Flask Tutorial</em>. [Link][4]
5. Wolfram Data Repository (2017). <em>FER-2013</em>. [Link][5]

[1]: https://github.com/oarriaga/face_classification
[2]: https://appliedmachinelearning.blog/2018/11/28/demonstration-of-facial-emotion-recognition-on-real-time-video-using-cnn-python-keras/
[3]: http://mohammadmahoor.com/affectnet/
[4]: https://www.youtube.com/playlist?list=PL-osiE80TeTs4UjLw5MM6OjgkjFeUxCYH
[5]: https://datarepository.wolframcloud.com/resources/FER-2013
[6]: https://documenter.getpostman.com/view/11985382/T1LFmVRw?version=latest
