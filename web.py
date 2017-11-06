from flask import Flask, render_template
from flask_sqlalchemy import SQLAlchemy
from models import Tracker, Rate, PeakRate
import config

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

if __name__ == "__main__":
    app.run(host='0.0.0.0')