from flask import Flask, request, jsonify
import os
import json
from werkzeug.utils import secure_filename

app = Flask(__name__)

UPLOAD_FOLDER = 'uploads'
POSTS_FILE = 'posts.json'
REVIEWER_SECRET = "Allah"
ONLY_ADMIN_CAN_SEND = "Allah"
GROUP_NAME = "IslamicIQHub"

os.makedirs(UPLOAD_FOLDER, exist_ok=True)
if not os.path.exists(POSTS_FILE):
    with open(POSTS_FILE, 'w') as f:
        json.dump([], f)


def load_posts():
    with open(POSTS_FILE, 'r') as f:
        return json.load(f)

def save_posts(posts):
    with open(POSTS_FILE, 'w') as f:
        json.dump(posts, f, indent=4)


@app.route('/submit_post', methods=['POST'])
def submit_post():
    title = request.form.get('title')
    content = request.form.get('content')
    token = request.form.get('token')

    if token != REVIEWER_SECRET:
        return jsonify({"status": "unauthorized"}), 401

    file = request.files.get('file')
    filename = None
    if file:
        filename = secure_filename(file.filename)
        file.save(os.path.join(UPLOAD_FOLDER, filename))

    post = {
        "id": len(load_posts()),
        "title": title,
        "content": content,
        "file": filename,
        "votes": {
            "allow": 0,
            "deny": 0
        },
        "status": "pending"
    }

    posts = load_posts()
    posts.append(post)
    save_posts(posts)

    return jsonify({"status": "success"})


@app.route('/get_pending_posts', methods=['GET'])
def get_pending_posts():
    posts = load_posts()
    pending = [p for p in posts if p['status'] == 'pending']
    return jsonify(pending)


@app.route('/submit_vote', methods=['POST'])
def submit_vote():
    post_id = int(request.form.get('post_id'))
    vote = request.form.get('vote')
    voter = request.form.get('voter')

    posts = load_posts()
    if post_id >= len(posts):
        return jsonify({"status": "post not found"}), 404

    if vote not in ["allow", "deny"]:
        return jsonify({"status": "invalid vote"}), 400

    if 'voters' not in posts[post_id]:
        posts[post_id]['voters'] = {}

    if voter in posts[post_id]['voters']:
        return jsonify({"status": "already voted"}), 400

    posts[post_id]['votes'][vote] += 1
    posts[post_id]['voters'][voter] = vote

    allow_votes = posts[post_id]['votes']['allow']
    deny_votes = posts[post_id]['votes']['deny']

    # Decide when to post or reject
    if allow_votes >= 2:
        posts[post_id]['status'] = "approved"
        print(f"\n✅ POST APPROVED to {GROUP_NAME}:\nTitle: {posts[post_id]['title']}\nContent: {posts[post_id]['content']}")
    elif deny_votes >= 2:
        posts[post_id]['status'] = "rejected"
        print(f"\n❌ POST REJECTED:\nTitle: {posts[post_id]['title']}\nContent: {posts[post_id]['content']}")

    save_posts(posts)
    return jsonify({"status": "vote recorded"})


@app.route('/admin_send', methods=['POST'])
def admin_send():
    post_id = int(request.form.get('post_id'))
    token = request.form.get('token')

    if token != ONLY_ADMIN_CAN_SEND:
        return jsonify({"status": "unauthorized"}), 401

    posts = load_posts()
    if post_id >= len(posts) or posts[post_id]['status'] != 'approved':
        return jsonify({"status": "not approved or not found"}), 400

    # Simulate WhatsApp group send
    print(f"\n📤 SENT TO {GROUP_NAME}:\nTitle: {posts[post_id]['title']}\nContent: {posts[post_id]['content']}")
    posts[post_id]['status'] = "sent"
    save_posts(posts)

    return jsonify({"status": "sent"})


if __name__ == '__main__':
    app.run(debug=True)
