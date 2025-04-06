from flask import Flask, render_template, request, jsonify
import os
from werkzeug.utils import secure_filename
import uuid
import json

app = Flask(__name__)

# Folders
UPLOAD_FOLDER = 'uploads'
POSTS_FOLDER = 'pending_posts'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(POSTS_FOLDER, exist_ok=True)

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# --- Home Page (for web form if needed) ---
@app.route('/')
def index():
    return render_template('form.html')  # Optional form.html

# --- Legacy web form submission route ---
@app.route('/submit', methods=['POST'])
def submit():
    text_data = request.form.get('text')
    uploaded_file = request.files.get('file')

    if uploaded_file:
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], uploaded_file.filename)
        uploaded_file.save(file_path)

    print("Text:", text_data)
    print("File saved to:", file_path if uploaded_file else "No file uploaded")

    return "Submitted successfully!"

# --- Route for reviewer GUI app ---
@app.route('/submit_post', methods=['POST'])
def submit_post():
    title = request.form.get('title')
    content = request.form.get('content')
    token = request.form.get('token')

    if token != "reviewer_secret":  # Change this later to something private
        return jsonify({"status": "unauthorized"}), 401

    file = request.files.get('file')
    filename = None
    if file:
        filename = secure_filename(file.filename)
        file.save(os.path.join(UPLOAD_FOLDER, filename))

    # Save post as JSON
    post_id = str(uuid.uuid4())
    post_data = {
        "id": post_id,
        "title": title,
        "content": content,
        "file": filename,
        "votes": {
            "owner1": None,
            "owner2": None,
            "admin": None
        }
    }

    with open(os.path.join(POSTS_FOLDER, f"{post_id}.json"), 'w') as f:
        json.dump(post_data, f)

    print(f"\n📥 New Post Saved: {post_id}")
    return jsonify({"status": "success", "post_id": post_id})

# --- Route for moderator app to fetch all pending posts ---
@app.route('/get_pending_posts', methods=['GET'])
def get_pending_posts():
    posts = []
    for filename in os.listdir(POSTS_FOLDER):
        if filename.endswith('.json'):
            with open(os.path.join(POSTS_FOLDER, filename), 'r') as f:
                post = json.load(f)
                posts.append(post)
    return jsonify(posts)

# --- Start app ---
if __name__ == '__main__':
    app.run(debug=True)
