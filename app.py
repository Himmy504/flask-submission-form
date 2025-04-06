from flask import Flask, render_template, request, jsonify
from werkzeug.utils import secure_filename
import os
import json
import datetime
import pywhatkit as kit

app = Flask(__name__)

UPLOAD_FOLDER = 'uploads'
DATA_FILE = 'posts.json'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# 🔹 Load or initialize post storage
if not os.path.exists(DATA_FILE):
    with open(DATA_FILE, 'w') as f:
        json.dump([], f)

# 🔹 Public form (optional)
@app.route('/')
def index():
    return render_template('form.html')

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

# 🔹 Reviewer Submission (from GUI)
@app.route('/submit_post', methods=['POST'])
def submit_post():
    title = request.form.get('title')
    content = request.form.get('content')
    token = request.form.get('token')

    if token != "reviewer_secret":  # 🔐 Secret shared with reviewers
        return jsonify({"status": "unauthorized"}), 401

    file = request.files.get('file')
    filename = None
    if file:
        filename = secure_filename(file.filename)
        file.save(os.path.join(UPLOAD_FOLDER, filename))

    with open(DATA_FILE, 'r') as f:
        posts = json.load(f)

    post_id = str(len(posts) + 1)
    posts.append({
        "id": post_id,
        "title": title,
        "content": content,
        "file": filename,
        "votes": {"allow": 0, "deny": 0},
        "sent": False
    })

    with open(DATA_FILE, 'w') as f:
        json.dump(posts, f, indent=2)

    print(f"\n📥 New Submission\nTitle: {title}\nContent: {content}\nFile: {filename}")
    return jsonify({"status": "success", "id": post_id})


# 🔹 Vote Submission
@app.route('/submit_vote', methods=['POST'])
def submit_vote():
    data = request.get_json()
    post_id = data.get('post_id')
    vote = data.get('vote')  # "allow" or "deny"

    if vote not in ["allow", "deny"]:
        return jsonify({"status": "invalid vote"}), 400

    with open(DATA_FILE, 'r') as f:
        posts = json.load(f)

    for post in posts:
        if post['id'] == post_id:
            post['votes'][vote] += 1
            break
    else:
        return jsonify({"status": "post not found"}), 404

    with open(DATA_FILE, 'w') as f:
        json.dump(posts, f, indent=2)

    print(f"🗳️ Vote received: {vote} for post ID {post_id}")
    return jsonify({"status": "vote recorded"})


# 🔹 Admin Only: Send Approved Post to WhatsApp Group
@app.route('/send_to_whatsapp', methods=['POST'])
def send_to_whatsapp():
    data = request.get_json()
    post_id = data.get('post_id')
    admin_token = data.get('token')

    if admin_token != "only_admin_can_send":  # 🔐 Only admin (you)
        return jsonify({"status": "unauthorized"}), 401

    with open(DATA_FILE, 'r') as f:
        posts = json.load(f)

    for post in posts:
        if post['id'] == post_id and not post.get('sent', False):
            message = f"*{post['title']}*\n\n{post['content']}"
            group_name = "My Islamic Group 💫"  # 🔁 Change to your real group name

            now = datetime.datetime.now()
            kit.sendwhatmsg_to_group(group_name, message, now.hour, now.minute + 1)

            post['sent'] = True

            with open(DATA_FILE, 'w') as f:
                json.dump(posts, f, indent=2)

            print(f"\n📤 SENT TO WHATSAPP GROUP:\n{message}")
            return jsonify({"status": "sent"})

    return jsonify({"status": "not found or already sent"}), 404


if __name__ == '__main__':
    app.run(debug=True)
