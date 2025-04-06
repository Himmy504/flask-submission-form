from flask import Flask, render_template, request, jsonify
import os
import json
from werkzeug.utils import secure_filename
import uuid
import pywhatkit as kit
import datetime

app = Flask(__name__)

UPLOAD_FOLDER = 'uploads'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

DATA_FILE = 'posts.json'
if not os.path.exists(DATA_FILE):
    with open(DATA_FILE, 'w') as f:
        json.dump([], f)

# 🔹 Reviewer Web Form (HTML GUI)
@app.route('/')
def index():
    return render_template('form.html')

# 🔹 Web Form Submission
@app.route('/submit', methods=['POST'])
def submit():
    text_data = request.form.get('text')
    uploaded_file = request.files.get('file')

    if uploaded_file:
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], uploaded_file.filename)
        uploaded_file.save(file_path)
    else:
        file_path = None

    print("Text:", text_data)
    print("File saved to:", file_path if file_path else "No file uploaded")

    return "Submitted successfully!"

# 🔹 Reviewer GUI Submission
@app.route('/submit_post', methods=['POST'])
def submit_post():
    title = request.form.get('title')
    content = request.form.get('content')
    token = request.form.get('token')

    if token != "reviewer_secret":  # 🔐 Secure this
        return jsonify({"status": "unauthorized"}), 401

    file = request.files.get('file')
    filename = None
    if file:
        filename = secure_filename(file.filename)
        file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))

    post = {
        "id": str(uuid.uuid4()),
        "title": title,
        "content": content,
        "file": filename,
        "votes": {},
        "sent": False
    }

    with open(DATA_FILE, 'r') as f:
        posts = json.load(f)

    posts.append(post)

    with open(DATA_FILE, 'w') as f:
        json.dump(posts, f, indent=2)

    print(f"\n📥 New Submission\nTitle: {title}\nContent: {content}\nFile: {filename}")
    return jsonify({"status": "success"})

# 🔹 Fetch All Pending Posts
@app.route('/get_pending_posts', methods=['GET'])
def get_pending_posts():
    with open(DATA_FILE, 'r') as f:
        posts = json.load(f)
    return jsonify(posts)

# 🔹 Moderators Submit Their Vote
@app.route('/submit_vote', methods=['POST'])
def submit_vote():
    data = request.get_json()
    post_id = data.get('post_id')
    moderator = data.get('moderator')
    vote = data.get('vote')

    with open(DATA_FILE, 'r') as f:
        posts = json.load(f)

    for post in posts:
        if post['id'] == post_id:
            post['votes'][moderator] = vote

            # ✅ Vote Logic
            votes = post['votes'].values()
            if list(votes).count("allow") >= 2:
                print(f"\n✅ APPROVED:\nTitle: {post['title']}\nContent: {post['content']}")
            elif list(votes).count("deny") >= 2:
                print(f"\n❌ DENIED:\nTitle: {post['title']}\nContent: {post['content']}")
            break

    with open(DATA_FILE, 'w') as f:
        json.dump(posts, f, indent=2)

    return jsonify({"status": "vote recorded"})

# 🔹 Admin Only: Send Approved Post to WhatsApp Group
@app.route('/send_to_whatsapp', methods=['POST'])
def send_to_whatsapp():
    data = request.get_json()
    post_id = data.get('post_id')
    admin_token = data.get('token')

    if admin_token != "admin_secret":  # 🔐 Replace with real admin token
        return jsonify({"status": "unauthorized"}), 401

    with open(DATA_FILE, 'r') as f:
        posts = json.load(f)

    for post in posts:
        if post['id'] == post_id and not post.get('sent', False):
            message = f"*{post['title']}*\n\n{post['content']}"
            # 📱 Replace this with actual number (MUST be in your WhatsApp contacts)
            phone_number = "+911234567890"  # <--- CHANGE THIS

            now = datetime.datetime.now()
            kit.sendwhatmsg(phone_number, message, now.hour, now.minute + 1)

            post['sent'] = True

            with open(DATA_FILE, 'w') as f:
                json.dump(posts, f, indent=2)

            print(f"\n📤 SENT TO WHATSAPP:\n{message}")
            return jsonify({"status": "sent"})

    return jsonify({"status": "not found or already sent"}), 404

if __name__ == '__main__':
    app.run(debug=True)
