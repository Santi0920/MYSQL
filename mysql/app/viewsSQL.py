#app/views.py

from flask import render_template, flash, redirect, url_for, session, request, logging
from flask_mysqldb import MySQL
from wtforms import Form, StringField, TextAreaField, PasswordField, validators
from passlib.hash import sha256_crypt
from functools import wraps

from app import app
from app import data

from apispec import APISpec
from apispec.ext.marshmallow import MarshmallowPlugin
from apispec_webframeworks.flask import FlaskPlugin
from flask import Flask,jsonify,send_from_directory
from marshmallow import Schema, fields
from datetime import date

spec = APISpec(
    title='Flask-api-swagger-doc',
    version='1.0.0.',
    openapi_version='3.0.2',
    plugins=[FlaskPlugin(),MarshmallowPlugin()]
)

app.secret_key='secrect123'

# Config MySQL
app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = ''
app.config['MYSQL_DB'] = 'myflaskapp'
app.config['MYSQL_CURSORCLASS'] = 'DictCursor'

#INIT MYSQL
mysql = MySQL(app)

class RegisterForm(Form):
    name = StringField('Name', [validators.Length(min=1, max=50)])
    username = StringField ('Username', [validators.Length(min=4, max=25)])
    email = StringField('Email', [validators.Length(min=6, max=50)])
    password = PasswordField('Password', [
        validators.DataRequired(),
        validators.EqualTo('confirm', message='Password do not match')
        ])
    confirm = PasswordField ('Confirm Password')

@app.route('/register', methods=['GET', 'POST'])
def register():
    form = RegisterForm(request.form)
    if request.method == 'POST' and form.validate():        
	name = form.name.data
        email = form.email.data
        username = form.username.data
        password = sha256_crypt.encrypt(str(form.password.data))

        # Create Cursor
        cur = mysql.connection.cursor()

        #Execute Query
        cur.execute("INSERT INTO users (name, email, username, password) VALUES (%s, %s, %s, %s)", (name, email, username, password))

        # Commit to DB
        mysql.connection.commit()

        # Close connection
        cur.close()

        flash('You are now registered and can log in', 'success')

        return redirect(url_for('index'))

    return render_template('register.html', form=form)

@app.route('/')
def index():
        return render_template("index.html")

@app.route('/about')
def about():
        return render_template("about.html")

@app.route('/articles')
def articulos():
    resultado = data.articles()
    return render_template("articles.html", resultado = resultado)

@app.route('/article/<article>')
def prueba(article):
    return render_template("article.html", article = article)

@app.route('/api/swagger.json')
def create_swagger_spec():
            return jsonify(spec.to_dict())

class ArticleResponseSchema(Schema):
    id = fields.Int()
    title = fields.Str()
    body = fields.Str()
    author = fields.Str()
    create_date = fields.Str()

class ArticleListResponseSchema(Schema):
    article_list = fields.List(fields.Nested(ArticleResponseSchema))

@app.route('/prueba')
def article():
    """Get List of Articles
        ---
        get:
            description: Get List of Articles
            responses:
                200:
                    description: Return an article list
                    content:
                        application/json:
                            schema: ArticleListResponseSchema
    """
    resultado = data.articles()

    return ArticleListResponseSchema().dump({'article_list':resultado})

with app.test_request_context():
        spec.path(view=article)

@app.route('/docs')
@app.route('/docs/<path:path>')
def swagger_docs(path=None):
    if not path or path == 'docs.html':
        return render_template('docs.html',base_url='/docs')
    else:
        return send_from_directory('static',path)