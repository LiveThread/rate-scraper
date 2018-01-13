import sys
import os.path

# appends the current "full path name of the executing script in a multiplatform-safe way"
# https://stackoverflow.com/questions/21005822/what-does-os-path-abspathos-path-joinos-path-dirname-file-os-path-pardir
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from flask import Flask, render_template, send_from_directory
from flask_sqlalchemy import SQLAlchemy
from scraper.models import Rate, PeakRate
from scraper import config

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = config.db_connection
db = SQLAlchemy(app)


@app.route("/")
def index():
    query = db.session().query(Rate).order_by(Rate.rate.desc())
    return render_template('instantaneous_rates.html', posts=query)


@app.route("/top/")
def top():
    query = db.session().query(PeakRate).order_by(PeakRate.rate.desc())
    return render_template('peak_rates.html', posts=query)


# shouldn't serve this from flask in production
@app.route("/topjson/")
def raw():
    root_dir = os.path.dirname(os.getcwd())
    return send_from_directory(os.path.join(root_dir, 'python', 'data'), 'data.json')


if __name__ == "__main__":
    app.run(host='0.0.0.0')
