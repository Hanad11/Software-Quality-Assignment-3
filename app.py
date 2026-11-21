# Importing required libs
"""Flask web app for hand sign digit recognition."""
import os

from flask import Flask, render_template, request
from flask_wtf.csrf import CSRFProtect
from model import preprocess_img, predict_result

# Instantiating flask app
app = Flask(__name__)
# The secret key signs the session cookie that holds the CSRF token.
# It is read from the environment, or randomly generated if it is not set.
app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY") or os.urandom(32)
# Reject any POST request (like the upload form) without a valid CSRF token
csrf = CSRFProtect()
csrf.init_app(app)


def debug_enabled():
    """Return True only when FLASK_DEBUG=1 is set, so debug mode is never on by default."""
    return os.environ.get("FLASK_DEBUG") == "1"


# Home route
@app.route("/")
def main():
    """Render the upload page."""
    return render_template("index.html")


# Prediction route
@app.route('/prediction', methods=['POST'])
def predict_image_file():
    """Predict the digit in the uploaded image and render the result page."""
    try:
        img = preprocess_img(request.files['file'].stream)
        pred = predict_result(img)
        return render_template("result.html", predictions=str(pred))
    except (KeyError, OSError, ValueError):
        error = "File cannot be processed."
        return render_template("result.html", err=error)

# Driver code
if __name__ == "__main__":
    app.run(port=9000, debug=debug_enabled())
