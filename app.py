from flask import Flask, request, jsonify, send_file, render_template
import firebase_admin
from firebase_admin import credentials, db, storage
import os
import tempfile
import re
import time
import urllib.parse
import datetime


app = Flask(__name__)

# Initialize Firebase
cred = credentials.Certificate('terrahub-75dbf-firebase-adminsdk-v4cej-36f9ed1afe.json')
firebase_admin.initialize_app(cred, {
    'databaseURL': 'https://terrahub-75dbf-default-rtdb.firebaseio.com',
    'storageBucket': 'terrahub-75dbf.appspot.com'
})

bucket = storage.bucket()
def sanitize_email(email):
    return re.sub(r'[.#$[\]/]', ',', email)
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/dashboard')
def thing():
    return render_template('dashboard.html')

@app.route('/teacherdash')
def stuff():
    return render_template('teacherdash.html')
@app.route('/admindash')
def admin():
    return render_template('admindash.html')
@app.route('/class')
def classw():
    return render_template('class.html')



@app.route('/add_user', methods=['POST'])
def add_user():
    data = request.get_json()
    email = data['email']
    password = data['password']
    tag = data['tag']
    user_id = sanitize_email(email)
    ref = db.reference(f'users/{user_id}')
    ref.set({
        'email': email,
        'password': password,
        'tag': tag
    })
    return jsonify(success=True)
@app.route('/fetch-class-meeting-times', methods=['POST'])
def fetch_class_meeting_times():
    data = request.get_json()
    user_email = data.get('userEmail')
    if not user_email:
        return jsonify({'error': 'User email not provided'}), 400

    user_email = user_email.replace('.', ',')  # Firebase uses commas instead of periods in keys
    user_classes_ref = db.reference(f'users/{user_email}/classes')
    class_meetings = []

    try:
        snapshot = user_classes_ref.get()
        if snapshot:
            for class_key, class_value in snapshot.items():
                class_name = class_value.get('className')
                class_date = class_value.get('classDate')
                class_timezone = class_value.get('classTimezone')
                if class_name and class_date and class_timezone:
                    class_meetings.append({
                        'name': class_name,
                        'date': class_date,
                        'timezone': class_timezone
                    })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

    return jsonify({'classes': class_meetings})


@app.route('/add_class', methods=['POST'])
def add_class():
    data = request.get_json()
    user_email = data['userEmail']
    class_name = data['className']
    html_file_name = data['htmlFileName']
    class_tag = data['classTag']
    meeting_link = data['meetingLink']
    user_id = sanitize_email(user_email)
    user_ref = db.reference(f'users/{user_id}')
    user_snapshot = user_ref.get()
    if user_snapshot:
        class_data = {
            'className': class_name,
            'htmlFileName': html_file_name,
            'tag': class_tag
        }
        if class_tag == 'teacher' and meeting_link:
            class_data['meetingLink'] = meeting_link
        user_ref.child('classes').push(class_data)
        return jsonify(success=True)
    else:
        return jsonify(success=False, error='User not found')

@app.route('/create_assignment', methods=['POST'])
def create_assignment():
    data = request.get_json()
    user_email = sanitize_email(data['userEmail'])
    title = data['title']
    details = data['details']
    class_name = data['className']
    assignment_id = db.reference().child(f'users/{user_email}/assignments').push().key
    assignment_data = {
        'title': title,
        'details': details,
        'class': class_name,
        'uploaded': False
    }
    updates = {f'/users/{user_email}/assignments/{assignment_id}': assignment_data}
    db.reference().update(updates)
    return jsonify(success=True)

@app.route('/list_files', methods=['GET'])
def list_files():
    path = request.args.get('path', '')
    current_ref = bucket.list_blobs(prefix=path)
    folders = set()
    files = []
    for blob in current_ref:
        name = blob.name[len(path):]
        if '/' in name:
            folders.add(name.split('/', 1)[0])
        else:
            files.append(name)
    return jsonify(folders=list(folders), files=files)

@app.route('/add_file', methods=['POST'])
def add_file():
    file = request.files['file']
    folder_path = request.form['path']
    file_ref = bucket.blob(f'{folder_path}/{file.filename}')
    file_ref.upload_from_file(file)
    return jsonify(success=True)

@app.route('/add_folder', methods=['POST'])
def add_folder():
    data = request.get_json()
    folder_path = data['folderPath']
    folder_name = data['folderName']
    folder_blob = bucket.blob(f'{folder_path}{folder_name}/.folderMarker_{time.time()}')
    folder_blob.upload_from_string('folderMarker')
    return jsonify(success=True)

@app.route('/delete_file', methods=['POST'])
def delete_file():
    data = request.get_json()
    file_path = data['filePath']
    file_ref = bucket.blob(file_path)
    file_ref.delete()
    return jsonify(success=True)

@app.route('/delete_folder', methods=['POST'])
def delete_folder():
    data = request.get_json()
    folder_path = data['folderPath']
    folder_blobs = bucket.list_blobs(prefix=folder_path)
    for blob in folder_blobs:
        blob.delete()
    return jsonify(success=True)

@app.route('/download_file', methods=['GET'])
def download_file():
    file_path = request.args.get('filePath')
    file_ref = bucket.blob(file_path)
    _, temp_filename = tempfile.mkstemp()
    file_ref.download_to_filename(temp_filename)
    return send_file(temp_filename, as_attachment=True, attachment_filename=os.path.basename(file_path))

@app.route('/rename_file', methods=['POST'])
def rename_file():
    data = request.get_json()
    file_path = data['filePath']
    new_file_name = data['newFileName']
    file_ref = bucket.blob(file_path)
    new_file_path = f'{os.path.dirname(file_path)}/{new_file_name}'
    new_file_ref = bucket.blob(new_file_path)
    new_file_ref.rewrite(file_ref)
    file_ref.delete()
    return jsonify(success=True)

@app.route('/load_user_classes', methods=['GET'])
def load_user_classes():
    users_ref = db.reference('users')
    users_snapshot = users_ref.get()
    users = []
    for user_id, user_data in users_snapshot.items():
        classes = user_data.get('classes', [])
        users.append({'email': user_data['email'], 'classes': classes})
    return jsonify(users=users)


@app.route('/user_endpoint/user_data', methods=['POST'])
def get_user_data():
    data = request.json
    email = urllib.parse.unquote(data.get('email'))
    user_ref = db.reference(f'users/{email}')
    user_data = user_ref.get()
    return jsonify(user_data)

@app.route('/user_endpoint/update_profile', methods=['POST'])
def update_profile():
    data = request.json
    email = urllib.parse.unquote(data.get('email'))
    name = data.get('name')
    bio = data.get('bio')
    password = data.get('password')
    user_ref = db.reference(f'users/{email}')
    user_ref.update({'name': name, 'bio': bio, 'password': password})
    return jsonify({'status': 'success'})

@app.route('/user_endpoint/assignments', methods=['POST'])
def get_assignments():
    data = request.json
    email = urllib.parse.unquote(data.get('email'))
    assignments_ref = db.reference(f'users/{email}/assignments')
    assignments = assignments_ref.get()
    return jsonify(assignments)

@app.route('/user_endpoint/assignment_details', methods=['POST'])
def get_assignment_details():
    data = request.json
    email = urllib.parse.unquote(data.get('email'))
    assignment_id = data.get('assignmentId')
    assignment_ref = db.reference(f'users/{email}/assignments/{assignment_id}')
    assignment = assignment_ref.get()
    return jsonify(assignment)

@app.route('/user_endpoint/upload_assignment', methods=['POST'])
def upload_assignment():
    file = request.files['file']
    email = request.form.get('email')
    assignment_name = request.form.get('assignmentName')
    if file and email and assignment_name:
        bucket = storage.bucket()
        blob = bucket.blob(f'{email}/{assignment_name}/{file.filename}')
        blob.upload_from_file(file)
        return jsonify({'status': 'success'})
    return jsonify({'status': 'error', 'message': 'Missing file or assignment info'})

@app.route('/user_endpoint/submit_assignment', methods=['POST'])
def submit_assignment():
    data = request.json
    email = urllib.parse.unquote(data.get('email'))
    assignment_id = data.get('assignmentId')
    assignments_ref = db.reference(f'users/{email}/assignments/{assignment_id}')
    assignments_ref.update({'submitted': True})
    return jsonify({'status': 'success'})

@app.route('/login', methods=['POST'])
def login():
    data = request.json
    email = data.get('email')
    password = data.get('password')

    ref = db.reference('users')
    users = ref.order_by_child('email').equal_to(email).get()

    if users:
        user_id = list(users.keys())[0]
        user_info = users[user_id]
        if user_info['password'] == password:
            response = {
                'success': True,
                'tag': user_info.get('tag', 'unknown')
            }
        else:
            response = {'success': False, 'message': 'Incorrect password'}
    else:
        response = {'success': False, 'message': 'User not found'}

    return jsonify(response)
@app.route('/fetch-chat-messages', methods=['GET'])
def fetch_chat_messages():
    user_email = request.args.get('userEmail').replace('.', ',')
    chats_ref = db.reference('chats')
    messages = []

    try:
        chat_data = chats_ref.get()
        for teacher, students in chat_data.items():
            student_data = students.get(user_email, {})
            for msg in student_data.values():
                messages.append(msg)
        return jsonify(messages)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/send-message', methods=['POST'])
def send_message():
    data = request.json
    user_email = data.get('userEmail').replace('.', ',')
    message = data.get('message')
    chats_ref = db.reference('chats')

    try:
        chats_ref.child('some_teacher').child(user_email).push({
            'sender': 'student',
            'text': message,
            'timestamp': 'timestamp_placeholder'  # Replace with proper timestamp handling
        })
        return jsonify({'status': 'Message sent successfully'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/fetch-notes', methods=['GET'])
def fetch_notes():
    user_email = request.args.get('userEmail')
    notes = []
    try:
        bucket = storage.bucket()
        blobs = bucket.list_blobs(prefix=f'{user_email}/notes/')
        for blob in blobs:
            notes.append({
                'name': blob.name.split('/')[-1],
                'contentType': blob.content_type,
                'downloadUrl': blob.generate_signed_url(expiration=datetime.timedelta(hours=1))
            })
        return jsonify(notes)
    except Exception as e:
        return jsonify({'error': str(e)}), 500




if __name__ == '__main__':
    app.run(debug=True, port=63343)
