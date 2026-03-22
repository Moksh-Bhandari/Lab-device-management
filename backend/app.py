from flask import Flask
from flask_cors import CORS
from extensions import bcrypt
from config import Config

app = Flask(__name__)
app.config.from_object(Config)
CORS(app)
bcrypt.init_app(app)

from routes.auth import auth_bp
from routes.labs import labs_bp
from routes.devices import devices_bp
from routes.students import students_bp

app.register_blueprint(auth_bp)
app.register_blueprint(labs_bp)
app.register_blueprint(devices_bp)
app.register_blueprint(students_bp)

if __name__ == '__main__':
    app.run(debug=True)