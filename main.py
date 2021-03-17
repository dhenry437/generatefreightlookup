from flask import Flask, render_template, request, flash, Markup, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_htpasswd import HtPasswdAuth
from itertools import groupby
from operator import attrgetter, itemgetter
import uuid
import os
import string

os.chdir(os.path.dirname(os.path.abspath(__file__)))
# sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

basedir = os.path.abspath(os.path.dirname(__file__))

app = Flask(__name__)
app.secret_key = 'k8ozj4h9xCBcsP$e'

app.config['FLASK_HTPASSWD_PATH'] = '.htpasswd'
app.config['FLASK_AUTH_ALL'] = True
htpasswd = HtPasswdAuth(app)

app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + \
    os.path.join(basedir, 'data.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)


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

# add a rule for the index page.


@app.route('/')
def index():
    return render_template('index.html')

# groups = {'descriptor':[result, result, result, ...], 'descriptor':[result, result, result, ...], 'descriptor':[result, result, result, ...], ...}


@app.route('/list')
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

@app.route('/result', methods = ['get'])
def postcode_lookup():
    id = request.args.get('id')
    if id:
       results = FreightLine.query.filter_by(id=id).all()
    else:
        postcode = request.args.get('postcode')
        results = FreightLine.query.filter_by(postcode=postcode).all()

    if not results:
        flash(Markup('<div class="alert alert-danger" role="alert">No matching postcode</div>'))
        return render_template('index.html')

    return render_template('result.html', results=results)

@app.route('/autocomplete', methods=['GET'])
def autocomplete():
    type = request.args.get('type')

    query = db.session.query(FreightLine.postcode).all()

    results = [result[0] for result in query]

    return jsonify(results)

# run the app.
if __name__ == "__main__":
    db.create_all()

    app.debug = True
    app.host ='0.0.0.0'
    app.port = 8080
    app.run()
