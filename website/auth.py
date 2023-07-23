from flask import Blueprint, render_template, request, flash, redirect, url_for,send_from_directory, Response, jsonify
from .models import User
from werkzeug.security import generate_password_hash, check_password_hash
from . import db   ##means from __init__.py import db
from flask_login import login_user, login_required, logout_user, current_user
from werkzeug.utils import secure_filename
import os
from PIL import Image
from werkzeug.utils import secure_filename
import os



import face_recognition
import cv2
import numpy as np

import threading
from datetime import datetime


auth = Blueprint('auth', __name__)

UPLOAD_FOLDER = 'website/wanted_people_photos'  # Folder where the images will be saved
ALLOWED_EXTENSIONS = {'jpg', 'jpeg', 'png'}  # Allowed file extensions

# Function to check if a filename has an allowed extension
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@auth.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')

        user = User.query.filter_by(email=email).first()
        if user:
            if check_password_hash(user.password, password):
                flash('Logged in successfully!', category='success')
                login_user(user, remember=True)
                return redirect(url_for('views.home'))
            else:
                flash('Incorrect password, try again.', category='error')
        else:
            flash('Email does not exist.', category='error')

    return render_template("login.html", user=current_user)


@auth.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('auth.login'))


@auth.route('/sign-up', methods=['GET', 'POST'])
def sign_up():
    if request.method == 'POST':
        email = request.form.get('email')
        first_name = request.form.get('firstName')
        password1 = request.form.get('password1')
        password2 = request.form.get('password2')

        user = User.query.filter_by(email=email).first()
        if user:
            flash('Email already exists.', category='error')
        elif len(email) < 4:
            flash('Email must be greater than 3 characters.', category='error')
        elif len(first_name) < 2:
            flash('First name must be greater than 1 character.', category='error')
        elif password1 != password2:
            flash('Passwords don\'t match.', category='error')
        elif len(password1) < 7:
            flash('Password must be at least 7 characters.', category='error')
        else:
            new_user = User(email=email, first_name=first_name, password=generate_password_hash(
                password1, method='sha256'))
            db.session.add(new_user)
            db.session.commit()
            login_user(new_user, remember=True)
            flash('Account created!', category='success')
            return redirect(url_for('views.home'))

    return render_template("sign_up.html", user=current_user)



@auth.route('/upload')
@login_required
def upload():
    
    
    return render_template("upload.html", user=current_user)

@auth.route('/video')
def video():
    return Response(run_cctv_detection(),mimetype='multipart/x-mixed-replace; boundary=frame')

@auth.route('/person_name')
def person_name():
    global real_time_detect_name
    return real_time_detect_name

#pasindu
@auth.route('/ticket')
@login_required
def ticket():
    
    return render_template("ticket.html", user=current_user)

#Malinda
@auth.route('/static_dasbord')
@login_required
def static_dasbord():
    
    return render_template("static_dasbord.html", user=current_user)

@auth.route('/upload_image')
@login_required
def upload_image():
    return render_template("upload_image.html", user=current_user)

@auth.route('/upload_images', methods=['GET', 'POST'])
@login_required
def upload_images():
    if request.method == 'POST':
        # Check if an image file was submitted
        if 'image' in request.files:
            image = request.files['image']
            # Check if the filename is empty or not allowed
            if image.filename == '' or not allowed_file(image.filename):
                flash('Invalid image file', category='error')
            else:
                # Save the uploaded image to the designated folder
                filename = secure_filename(image.filename)
                image.save(os.path.join(UPLOAD_FOLDER, filename))
                flash('Image uploaded successfully!', category='success')
                return redirect(url_for('views.home'))

    return render_template("upload_image.html", user=current_user)


@auth.route('/detection_list')
def detection_list():
    return jsonify([{
        'person_name': entry.person_name,
        'time': entry.time
    } for entry in detection_list])


detection_list = []

class DetectionEntry:
    def __init__(self, person_name):
        self.person_name = person_name
        self.time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")


real_time_detect_name = 'no one detect'
# Path to the alert sound file


def run_cctv_detection():

    global real_time_detect_name

    video_capture = cv2.VideoCapture(0)

    wn_folder_parth ='C:\RP Final\Final\website\wanted_people_photos'
    pepl_list = os.listdir(wn_folder_parth)
    known_face_names = []
    known_face_encodings = []

    for pepl in pepl_list:

        print(wn_folder_parth+'/'+pepl)

        people_face = face_recognition.load_image_file(wn_folder_parth+'/'+pepl)
        people_face_encoding = face_recognition.face_encodings(people_face)[0]
        known_face_encodings.append(people_face_encoding)

        name,format = pepl.split(".")
        known_face_names.append(name)
        print('Enterd peoples name - ',name)


    face_locations = []
    face_encodings = []
    face_names = []
    process_this_frame = True

    while True:
        # Grab a single frame of video
        ret, frame = video_capture.read()

        # Only process every other frame of video to save time
        if process_this_frame:
            # Resize frame of video to 1/4 size for faster face recognition processing
            small_frame = cv2.resize(frame, (0, 0), fx=0.25, fy=0.25)
            
            # Convert the image from BGR color (which OpenCV uses) to RGB color (which face_recognition uses)
            rgb_small_frame = small_frame[:, :, ::-1]

            # Find all the faces and face encodings in the current frame of video
            face_locations = face_recognition.face_locations(rgb_small_frame)
            face_encodings = face_recognition.face_encodings(rgb_small_frame, face_locations)

            face_names = []
            for face_encoding in face_encodings:
                # See if the face is a match for the known face(s)
                matches = face_recognition.compare_faces(known_face_encodings, face_encoding)
                name = "Unknown"

                # # If a match was found in known_face_encodings, just use the first one.
                # if True in matches:
                #     first_match_index = matches.index(True)
                #     name = known_face_names[first_match_index]

                # Or instead, use the known face with the smallest distance to the new face
                face_distances = face_recognition.face_distance(known_face_encodings, face_encoding)
                best_match_index = np.argmin(face_distances)
                if matches[best_match_index]:
                    name = known_face_names[best_match_index]
           
                  
                 # Add the detection entry to the list
                detection_entry = DetectionEntry(name)
                detection_list.append(detection_entry)

                face_names.append(name)
                
        process_this_frame = not process_this_frame

        # Display the results
        for (top, right, bottom, left), name in zip(face_locations, face_names):
            # Scale back up face locations since the frame we detected in was scaled to 1/4 size
            top *= 4
            right *= 4
            bottom *= 4
            left *= 4

            # Draw a box around the face
            cv2.rectangle(frame, (left, top), (right, bottom), (0, 0, 255), 2)

            # Draw a label with a name below the face
            cv2.rectangle(frame, (left, bottom - 35), (right, bottom), (0, 0, 255), cv2.FILLED)
            font = cv2.FONT_HERSHEY_DUPLEX
            cv2.putText(frame, name, (left + 6, bottom - 6), font, 1.0, (255, 255, 255), 1)

            real_time_detect_name = name

        # Display the resulting image
            
            frame = cv2.resize(frame, (0, 0), fx=1, fy=1)
            frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            ret, jpeg = cv2.imencode('.jpg', frame_rgb)

            yield(b'--frame\r\n'
                    b'Content-Type: image/jpeg\r\n\r\n' + jpeg.tobytes() +  b'\r\n\r\n')
         
        
        # Hit 'q' on the keyboard to quit!
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

def gen():
    global real_time_detect_name

t1 = threading.Thread(target=run_cctv_detection)
t1.start()



# while True:
#
#
#     if real_time_detect_name != 'no one detect':
#
#         person_name = real_time_detect_name
#         real_time_detect_name = 'no one detect'
#
#         print(person_name)




def get_face_data():

    global real_time_detect_name

    send_data = str(real_time_detect_name)
    real_time_detect_name = 'no one detect'

    return send_data


