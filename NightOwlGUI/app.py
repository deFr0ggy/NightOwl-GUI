import os
import email
import re
import extract_msg
from email import policy
from flask import Flask, render_template, request, redirect, url_for, jsonify
from werkzeug.utils import secure_filename
import requests
import hashlib
import zipfile
from io import BytesIO

app = Flask(__name__)
UPLOAD_FOLDER = 'uploads'
ALLOWED_EXTENSIONS = {'msg', 'eml'}

ABUSEIPDB_API_KEY = os.getenv('ABUSEIPDB_API_KEY')

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def save_attachment(attachment, folder_path):
    filename = secure_filename(attachment.filename)
    attachment_path = os.path.join(folder_path, filename)
    with open(attachment_path, 'wb') as f:
        f.write(attachment.data)
    return filename

def save_eml_attachment(part, folder_path):
    attachment_filename = part.get_filename()
    if attachment_filename:
        attachment_filename = secure_filename(attachment_filename)
        attachment_data = part.get_payload(decode=True)
        attachment_path = os.path.join(folder_path, attachment_filename)
        with open(attachment_path, 'wb') as f:
            f.write(attachment_data)
        return attachment_filename
    return None

def calculate_hashes(filepath):
    hashes = {
        'md5': hashlib.md5(),
        'sha256': hashlib.sha256(),
        'sha512': hashlib.sha512(),
    }

    with open(filepath, 'rb') as f:
        while chunk := f.read(8192):
            for hash_algo in hashes.values():
                hash_algo.update(chunk)

    return {algo: hash_obj.hexdigest() for algo, hash_obj in hashes.items()}

def save_and_zip_attachments(attachments, folder_path):
    zip_filename = os.path.join(folder_path, 'attachments.zip')

    with zipfile.ZipFile(zip_filename, 'w') as zip_file:
        for attachment in attachments:
            attachment_filename = secure_filename(attachment)
            attachment_path = os.path.join(folder_path, attachment_filename)
            zip_file.write(attachment_path, compress_type=zipfile.ZIP_DEFLATED)

    return zip_filename

def extract_email_data(filepath):
    email_data = {
        'from': '',
        'to': '',
        'subject': '',
        'date': '',
        'body': '',
        'ips': [],
        'emails': [],
        'urls': [],
        'attachments': [],
        'attachment_hashes': []
    }

    if filepath.endswith('.msg'):
        msg = extract_msg.Message(filepath)
        email_data['from'] = msg.sender
        email_data['to'] = msg.to
        email_data['subject'] = msg.subject
        email_data['date'] = msg.date  
        email_data['body'] = msg.body.strip()

        subject_folder = secure_filename(email_data['subject'] if email_data['subject'] else 'no_subject')
        email_folder = os.path.join(UPLOAD_FOLDER, subject_folder)
        os.makedirs(email_folder, exist_ok=True)

        if msg.attachments:
            for attachment in msg.attachments:
                attachment_filename = save_attachment(attachment, email_folder)
                email_data['attachments'].append(attachment_filename)

        zip_filename = save_and_zip_attachments(msg.attachments, email_folder)
        email_data['attachments'].append(zip_filename)

        for attachment in msg.attachments:
            attachment_filename = save_attachment(attachment, email_folder)
            attachment_path = os.path.join(email_folder, attachment_filename)
            hashes = calculate_hashes(attachment_path)
            email_data['attachment_hashes'].append(hashes)

    elif filepath.endswith('.eml'):
        with open(filepath, 'rb') as f:
            msg = email.message_from_binary_file(f, policy=policy.default)

        email_data['from'] = msg.get('From')
        email_data['to'] = msg.get('To')
        email_data['subject'] = msg.get('Subject')
        email_data['date'] = msg.get('Date')  

        subject_folder = secure_filename(email_data['subject'] if email_data['subject'] else 'no_subject')
        email_folder = os.path.join(UPLOAD_FOLDER, subject_folder)
        os.makedirs(email_folder, exist_ok=True)

        if msg.is_multipart():
            for part in msg.walk():

                if part.get_content_type() == 'text/plain':
                    email_data['body'] += part.get_payload(decode=True).decode('utf-8').strip() + "\n"

                if part.get('Content-Disposition') and 'attachment' in part.get('Content-Disposition'):
                    attachment_filename = save_eml_attachment(part, email_folder)
                    if attachment_filename:
                        email_data['attachments'].append(attachment_filename)
                        attachment_path = os.path.join(email_folder, attachment_filename)
                        hashes = calculate_hashes(attachment_path)
                        email_data['attachment_hashes'].append(hashes)
        else:
            email_data['body'] = msg.get_payload(decode=True).decode('utf-8').strip()

        zip_filename = save_and_zip_attachments(email_data['attachments'], email_folder)
        email_data['attachments'].append(zip_filename)

    email_data['ips'] = re.findall(r'\b(?:\d{1,3}\.){3}\d{1,3}\b', email_data['body'])
    email_data['emails'] = re.findall(r'[\w\.-]+@[\w\.-]+', email_data['body'])
    email_data['urls'] = re.findall(r'(https?://[^\s]+)', email_data['body'])

    return email_data

def query_abuse_ipdb(ip):
    url = f"https://api.abuseipdb.com/api/v2/check"
    querystring = {
        "ipAddress": ip,
        "maxAgeInDays": "90" 
    }
    headers = {
        "Accept": "application/json",
        "Key": ABUSEIPDB_API_KEY
    }
    response = requests.request(method="GET", url=url, headers=headers, params=querystring)
    return response.json()

@app.route('/check_ip', methods=['POST'])
def check_ip():
    ip = request.form.get('ip')
    result = query_abuse_ipdb(ip)
    return jsonify(result)

@app.route('/', methods=['GET', 'POST'])
def upload_file():
    if request.method == 'POST':
        if 'file' not in request.files:
            return redirect(request.url)

        file = request.files['file']

        if file.filename == '':
            return redirect(request.url)

        if file and allowed_file(file.filename):
            filepath = os.path.join(UPLOAD_FOLDER, secure_filename(file.filename))
            os.makedirs(UPLOAD_FOLDER, exist_ok=True)
            file.save(filepath)

            email_data = extract_email_data(filepath)

            return render_template('result.html', email_data=email_data)

    return render_template('index.html')


if __name__ == '__main__':
    if not os.path.exists(UPLOAD_FOLDER):
        os.makedirs(UPLOAD_FOLDER)
    app.run(debug=True)

