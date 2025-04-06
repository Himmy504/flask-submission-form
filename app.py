from flask import Flask, render_template, request, jsonify
import os
import json
from werkzeug.utils import secure_filename
import uuid

app = Flask(__name__)

UPLOAD_FOLDER = 'uploads'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

DATA_FILE = 'posts.json'
if not os.path.exists(DATA_FILE):
    with open(DATA_FILE, 'w') as f:
        json.dump([], f)

# 🔹 Reviewer Web Form Route
@app.route('/')
def index():
    return render_template('form.html')

# 🔹 Handle Form Submission from Reviewer Web Page
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

# 🔹 Reviewer GUI App POST Submission
@app.route('/submit_post', methods=['POST'])
def submit_post():
    title = request.form.get('title')
    content = request.form.get('content')
    token = request.form.get('token')

    if token != "reviewer_secret":  # 🔐 Replace this with real secret later
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
        "votes": {}  # will store votes by moderator
    }

    with open(DATA_FILE, 'r') as f:
        posts = json.load(f)

    posts.append(post)

    with open(DATA_FILE, 'w') as f:
        json.dump(posts, f, indent=2)

    print(f"\n📥 New Submission\nTitle: {title}\nContent: {content}\nFile: {filename}")
    return jsonify({"status": "success"})

# 🔹 Send Posts List to Moderator GUI
@app.route('/get_pending_posts', methods=['GET'])
def get_pending_posts():
    with open(DATA_FILE, 'r') as f:
        posts = json.load(f)
    return jsonify(posts)

# 🔹 Receive Votes from Moderator GUI
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

            # ✅ Voting Logic
            votes = post['votes'].values()
            if list(votes).count("allow") >= 2:
                print(f"\n✅ APPROVED:\nTitle: {post['title']}\nContent: {post['content']}")
                # 🟢 Trigger WhatsApp send here if admin
            elif list(votes).count("deny") >= 2:
                print(f"\n❌ DENIED:\nTitle: {post['title']}\nContent: {post['content']}")
            break

    with open(DATA_FILE, 'w') as f:
        json.dump(posts, f, indent=2)

    return jsonify({"status": "vote recorded"})

if __name__ == '__main__':
    app.run(debug=True)
