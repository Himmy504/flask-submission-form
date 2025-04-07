from flask import Flask, request, jsonify, render_template, send_from_directory
import os
import json
from datetime import datetime

app = Flask(__name__)
UPLOAD_FOLDER = 'uploads'
POSTS_FILE = 'posts.json'

reviewer_secret = "Allah"
only_admin_can_send = "Allah"
group_name = "IslamicIQHub"

# Ensure uploads and data file exist
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
if not os.path.exists(POSTS_FILE):
    with open(POSTS_FILE, 'w') as f:
        json.dump([], f)

@app.route('/')
def index():
    return render_template('form.html')

@app.route('/moderator')
def moderator_panel():
    return render_template('moderator.html')

@app.route('/uploads/<filename>')
def uploaded_file(filename):
    return send_from_directory(UPLOAD_FOLDER, filename)

@app.route('/submit', methods=['POST'])
def submit_post():
    text = request.form.get('text')
    file = request.files.get('file')
    submitter = request.form.get('submitter', 'Anonymous')

    if not text and not file:
        return jsonify({'success': False, 'message': 'Text or file is required.'}), 400

    file_url = None
    if file:
        filename = datetime.now().strftime('%Y%m%d%H%M%S_') + file.filename
        filepath = os.path.join(UPLOAD_FOLDER, filename)
        file.save(filepath)
        file_url = f'/uploads/{filename}'

    with open(POSTS_FILE, 'r') as f:
        posts = json.load(f)

    post_id = len(posts) + 1
    new_post = {
        'id': post_id,
        'text': text,
        'file_url': file_url,
        'submitter': submitter,
        'votes': [],
        'status': 'pending'
    }

    posts.append(new_post)
    with open(POSTS_FILE, 'w') as f:
        json.dump(posts, f, indent=2)

    return jsonify({'success': True, 'message': 'Post submitted for review.'})

@app.route('/pending_posts', methods=['GET'])
def get_pending_posts():
    with open(POSTS_FILE, 'r') as f:
        posts = json.load(f)
    pending = [p for p in posts if p['status'] == 'pending']
    return jsonify(pending)

@app.route('/submit_vote', methods=['POST'])
def submit_vote():
    data = request.json
    post_id = data.get('post_id')
    vote = data.get('vote')
    reviewer = data.get('reviewer')

    if not reviewer:
        return jsonify({'success': False, 'message': 'Reviewer ID required'}), 400

    with open(POSTS_FILE, 'r') as f:
        posts = json.load(f)

    for post in posts:
        if post['id'] == post_id:
            # Remove previous vote from same reviewer
            post['votes'] = [v for v in post['votes'] if v.get('reviewer') != reviewer]
            post['votes'].append({'reviewer': reviewer, 'vote': vote})
            break
    else:
        return jsonify({'success': False, 'message': 'Post not found'}), 404

    with open(POSTS_FILE, 'w') as f:
        json.dump(posts, f, indent=2)

    return jsonify({'success': True, 'message': 'Vote recorded'})

@app.route('/finalize_post', methods=['POST'])
def finalize_post():
    data = request.json
    post_id = data.get('post_id')
    decision = data.get('decision')
    admin_key = data.get('admin_key')

    if admin_key != only_admin_can_send:
        return jsonify({'success': False, 'message': 'Unauthorized'}), 403

    with open(POSTS_FILE, 'r') as f:
        posts = json.load(f)

    for post in posts:
        if post['id'] == post_id:
            post['status'] = 'approved' if decision == 'allow' else 'denied'
            break
    else:
        return jsonify({'success': False, 'message': 'Post not found'}), 404

    with open(POSTS_FILE, 'w') as f:
        json.dump(posts, f, indent=2)

    if decision == 'allow':
        print(f"\n📢 Approved post for {group_name}:\n{text_with_file(post)}\n")

    return jsonify({'success': True, 'message': 'Post finalized'})

def text_with_file(post):
    result = f"📝 *{post['submitter']}* submitted:\n{post['text']}"
    if post['file_url']:
        result += f"\n📎 File: {post['file_url']}"
    return result

if __name__ == '__main__':
    app.run(debug=True)
