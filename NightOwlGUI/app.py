import os
import email
import re
import extract_msg
from email import policy
from flask import Flask, render_template, request, redirect, url_for
from werkzeug.utils import secure_filename
import shutil

app = Flask(__name__)
UPLOAD_FOLDER = 'uploads'
ALLOWED_EXTENSIONS = {'msg', 'eml'}

# Utility function to check file extensions
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# Function to save attachments to a directory
def save_attachment(attachment, folder_path):
    filename = secure_filename(attachment.filename)
    attachment_path = os.path.join(folder_path, filename)
    with open(attachment_path, 'wb') as f:
        f.write(attachment.data)
    return filename

# Function to save .eml file attachments
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

# Email extraction function for .msg and .eml files
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
        'attachments': []
    }

    if filepath.endswith('.msg'):
        # Handle .msg files with extract_msg library
        msg = extract_msg.Message(filepath)
        email_data['from'] = msg.sender
        email_data['to'] = msg.to
        email_data['subject'] = msg.subject
        email_data['date'] = msg.date  # Extract Date
        email_data['body'] = msg.body.strip()

        # Create a folder to store attachments (based on email subject)
        subject_folder = secure_filename(email_data['subject'] if email_data['subject'] else 'no_subject')
        email_folder = os.path.join(UPLOAD_FOLDER, subject_folder)
        os.makedirs(email_folder, exist_ok=True)

        # Save attachments
        if msg.attachments:
            for attachment in msg.attachments:
                attachment_filename = save_attachment(attachment, email_folder)
                email_data['attachments'].append(attachment_filename)

    elif filepath.endswith('.eml'):
        # Handle .eml files with email library
        with open(filepath, 'rb') as f:
            msg = email.message_from_binary_file(f, policy=policy.default)

        email_data['from'] = msg.get('From')
        email_data['to'] = msg.get('To')
        email_data['subject'] = msg.get('Subject')
        email_data['date'] = msg.get('Date')  # Extract Date

        # Create a folder to store attachments (based on email subject)
        subject_folder = secure_filename(email_data['subject'] if email_data['subject'] else 'no_subject')
        email_folder = os.path.join(UPLOAD_FOLDER, subject_folder)
        os.makedirs(email_folder, exist_ok=True)

        # Get plain text body
        if msg.is_multipart():
            for part in msg.walk():
                # Extract plain text body
                if part.get_content_type() == 'text/plain':
                    email_data['body'] += part.get_payload(decode=True).decode('utf-8').strip() + "\n"
                
                # Save attachments
                if part.get('Content-Disposition') and 'attachment' in part.get('Content-Disposition'):
                    attachment_filename = save_eml_attachment(part, email_folder)
                    if attachment_filename:
                        email_data['attachments'].append(attachment_filename)
        else:
            email_data['body'] = msg.get_payload(decode=True).decode('utf-8').strip()

    # Extract IPs, emails, and URLs from the body
    email_data['ips'] = re.findall(r'\b(?:\d{1,3}\.){3}\d{1,3}\b', email_data['body'])
    email_data['emails'] = re.findall(r'[\w\.-]+@[\w\.-]+', email_data['body'])
    email_data['urls'] = re.findall(r'(https?://[^\s]+)', email_data['body'])

    return email_data

# Upload route
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

            # Extract data from the email file
            email_data = extract_email_data(filepath)

            return render_template('result.html', email_data=email_data)

    return render_template('index.html')

if __name__ == '__main__':
    if not os.path.exists(UPLOAD_FOLDER):
        os.makedirs(UPLOAD_FOLDER)
    app.run(debug=True)
