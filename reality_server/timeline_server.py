from flask import render_template
from flask_cors import CORS
import connexion
import os

# Create the application instance
app = connexion.App(__name__, specification_dir="./")

# Read the swagger.yml file to configure the endpoints
my_dir = os.path.dirname(os.path.realpath(__file__))
config_path = os.path.join(my_dir, "api", "timeline_api.yml")

CORS(app.app)
app.add_api(config_path)
# app.add_api('timeline_api.yml')
# to open the swagger UI install: connexion[swagger-ui]

# Create a URL route in our application for "/"
@app.route("/")
def home():
    """
    This function just responds to the browser ULR
    localhost:5000/
    :return:        the rendered template 'home.html'
    """
    return render_template("home.html")


# If we're running in stand alone mode, run the application
def main():
    app.run(host="0.0.0.0", port=5005, debug=True)


if __name__ == "__main__":
    main()
# The full project:
# https://github.com/realpython/materials/blob/master/flask-connexion-rest/version_3/swagger.yml
