from flask import Flask, render_template, request, flash, Markup, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_htpasswd import HtPasswdAuth
from itertools import groupby
from operator import attrgetter, itemgetter
import uuid
import os
import string

basedir = os.path.abspath(os.path.dirname(__file__))

# EB looks for an 'application' callable by default.
application = Flask(__name__)
application.secret_key = 'k8ozj4h9xCBcsP$e'

application.config['FLASK_HTPASSWD_PATH'] = '.htpasswd'
application.config['FLASK_AUTH_ALL'] = True
htpasswd = HtPasswdAuth(application)

application.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + \
    os.path.join(basedir, 'data.db')
application.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(application)

class FreightLine(db.Model):
    id = db.Column(db.String, primary_key=True,
                   default=uuid.uuid4, unique=True)
    country = db.Column(db.String(64))
    region = db.Column(db.String)
    state = db.Column(db.String(64))
    short_state = db.Column(db.String(8))
    postcode = db.Column(db.Integer)
    suburb = db.Column(db.String)
    cost_per_palet = db.Column(db.Float)
    cost_per_1_1000 = db.Column(db.Float)
    cost_per_2_1000 = db.Column(db.Float)
    cost_per_1_1500 = db.Column(db.Float)
    cost_per_1_2000 = db.Column(db.Float)
    note = db.Column(db.String)
    lat = db.Column(db.Float)
    lon = db.Column(db.Float)

@application.route('/')
def index():
    return render_template('index.html')

# groups = {'descriptor':[result, result, result, ...], 'descriptor':[result, result, result, ...], 'descriptor':[result, result, result, ...], ...}
@application.route('/list')
def browse():
    group_by = request.args.get('group_by')
    mydict = {}

    if group_by == 'alphabetical':
        results = FreightLine.query.order_by('suburb').all()

        # mydict = {}
        for k, g in groupby(results, key=lambda x: x.suburb[0]):
            if k in mydict:
                mydict[k] += g
            else:
                mydict[k]=list(g)
    elif group_by == 'state':
        results = FreightLine.query.order_by('short_state').all()

        # mydict = {}
        for k, g in groupby(results, key=attrgetter('short_state')):
            if k in mydict:
                mydict[k] += g
            else:
                mydict[k]=list(g)
    elif group_by == 'postcode':
        results = FreightLine.query.order_by('postcode').all()

        # mydict = {}
        for k, g in groupby(results, key=lambda x: str(x.postcode)[0]):
            if k in mydict:
                mydict[k] += g
            else:
                mydict[k]=list(g)

    return render_template('list.html', results=mydict)

@application.route('/result', methods = ['get'])
def results():
    id = request.args.get('id')
    postcode = request.args.get('postcode')
    suburb = request.args.get('suburb')

    results = None

    if id:
        results = FreightLine.query.filter_by(id=id).all()
    elif suburb:
        results = FreightLine.query.filter(FreightLine.suburb.like('%' + suburb + '%')).all()
    elif postcode:
        results = FreightLine.query.filter_by(postcode=postcode).all()

    if not results:
        flash(Markup('<div class="alert alert-danger" role="alert">No matching results</div>'))
        return render_template('index.html')

    return render_template('result.html', results=results)

@application.route('/map')
def map():
    locations = FreightLine.query.all()

    return render_template('map.html', locations=locations)

@application.route('/autocomplete', methods=['GET'])
def autocomplete():
    type = request.args.get('type')

    if type == 'postcode':
        query = db.session.query(FreightLine.postcode).all()

        results = [str(result[0]) for result in query]
    elif type == 'suburb':
        query = db.session.query(FreightLine.suburb).all()

        results = [str(result[0]) for result in query]

    return jsonify(results)

# run the app.
if __name__ == "__main__":
    db.create_all()

    application.debug = True
    application.run(host='0.0.0.0', port=8080)
