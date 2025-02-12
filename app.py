from flask import Flask, render_template, jsonify
from models.database import init_db
from models.photo import Photo

app = Flask(__name__)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/photos')
def get_photos():
    photos = Photo.get_approved_photos()
    return jsonify([photo.to_dict() for photo in photos])

if __name__ == '__main__':
    init_db()
    app.run(host='127.0.0.1', port=5000)
