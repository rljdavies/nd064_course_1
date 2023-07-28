import sqlite3
import logging
import sys
import time
from flask import Flask, jsonify, json, render_template, request, url_for, redirect, flash
from werkzeug.exceptions import abort

#global count of database connections
connection_count = 0;

# Function to get a database connection.
# This function connects to database with the name `database.db`
def get_db_connection():
    global connection_count
    connection = sqlite3.connect('database.db')
    connection.row_factory = sqlite3.Row
    connection_count += 1
    return connection

# Function to get a post using its ID
def get_post(post_id):
    connection = get_db_connection()
    post = connection.execute('SELECT * FROM posts WHERE id = ?',
                        (post_id,)).fetchone()
    connection.close()
    return post

# Function to get a total post count
def get_post_count():
   connection = get_db_connection()
   posts = connection.execute('SELECT count(*) FROM posts').fetchone()
   connection.close()
   return posts[0]
   
# Function to get a db connection count
def get_db_connection_count():
   return connection_count

# Define the Flask application
app = Flask(__name__)
app.config['SECRET_KEY'] = 'your secret key'

# Define the main route of the web application 
@app.route('/')
def index():
    connection = get_db_connection()
    posts = connection.execute('SELECT * FROM posts').fetchall()
    connection.close()
    return render_template('index.html', posts=posts)

# Define how each individual article is rendered 
# If the post ID is not found a 404 page is shown
@app.route('/<int:post_id>')
def post(post_id):
    post = get_post(post_id)
    if post is None:
      logger.error("Could not retrieve non existent article: " + str(post_id) + ".")
      return render_template('404.html'), 404
    else:
      logger.info("\"" + str(post["title"]) + "\" article retrieved.")
      return render_template('post.html', post=post)

# Define the About Us page
@app.route('/about')
def about():
    logger.info("\"About Us\" page retrieved.")
    return render_template('about.html')
    
# Define the healthz endpoint
@app.route('/healthz')
def healthz():
  response = app.response_class(
     response=json.dumps({"result":"OK - healthy"}),
     status=200,
     mimetype='application/json'
  ) 
  return response
  
# Define the metrics endpoint
@app.route('/metrics')
def metrics():
  connectionCount = get_db_connection_count()
  postCount = get_post_count()
  response = app.response_class(
     response=json.dumps({"db_connection_count": connectionCount, "post_count": postCount}),
     status=200,
     mimetype='application/json'
  ) 
  return response

# Define the post creation functionality 
@app.route('/create', methods=('GET', 'POST'))
def create():
    if request.method == 'POST':
        title = request.form['title']
        content = request.form['content']

        if not title:
            flash('Title is required!')
        else:
            connection = get_db_connection()
            connection.execute('INSERT INTO posts (title, content) VALUES (?, ?)',
                         (title, content))
            connection.commit()
            connection.close()
            logger.info("\"" + str(title) + "\" article created.")
            return redirect(url_for('index'))

    return render_template('create.html')

# start the application on port 3111
# expanded logging with tips from https://stackoverflow.com/questions/3220284/how-to-customize-the-time-format-for-python-logging
if __name__ == "__main__":
   
   logger=logging.getLogger()
   logger_formatter=logging.Formatter('%(levelname)s:%(name)s:%(asctime)s %(message)s', datefmt='[%d/%b/%Y %H:%M:%S]')
   logger.setLevel(logging.DEBUG)

   logger_debug_handler = logging.StreamHandler(sys.stdout)
   logger_debug_handler.setLevel(logging.DEBUG)
   logger_debug_handler.setFormatter(logger_formatter)
   logger.addHandler(logger_debug_handler)
   
   logger_error_handler = logging.StreamHandler(sys.stderr)
   logger_error_handler.setLevel(logging.ERROR)
   logger_error_handler.setFormatter(logger_formatter)
   logger.addHandler(logger_error_handler)
    
   app.run(host='0.0.0.0', port='3111')
