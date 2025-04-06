from flask import Flask, render_template, request
import os

app = Flask(__name__)
UPLOAD_FOLDER = 'uploads'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

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

if __name__ == '__main__':
    app.run(debug=True)
    from flask import request, jsonify
import os
from werkzeug.utils import secure_filename

UPLOAD_FOLDER = 'uploads'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

@app.route('/submit_post', methods=['POST'])
def submit_post():
    title = request.form.get('title')
    content = request.form.get('content')
    token = request.form.get('token')

    if token != "reviewer_secret":  # 🔒 change this to something secret later
        return jsonify({"status": "unauthorized"}), 401

    file = request.files.get('file')
    filename = None
    if file:
        filename = secure_filename(file.filename)
        file.save(os.path.join(UPLOAD_FOLDER, filename))

    # For now just print to console (you’ll handle saving later)
    print(f"\n📥 New Submission\nTitle: {title}\nContent: {content}\nFile: {filename}")
    return jsonify({"status": "success"})

