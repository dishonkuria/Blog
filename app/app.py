import datetime
import functools
import os
import re
import urllib

from flask import (Flask, abort, flash, Markup, redirect, render_template,
                    request, Response, session, url_for)
from markdown import markdown
from markdown.extensions.codehilite import CodeHiliteExtension
from markdown.extensions.extra import ExtraExtension
from micawber import bootstrap_basic, parse_html
from micawber.cache import Cache as OEmbedCache
from pewee import *
from playhouse.flask_utils import FlaskDB, get_object_or_404, object_list
from playhouse.sqlite_ext import *

ADMIN_PASSWORD = 'secret'
APP_DIR = os.path.dirname(os.path.realpath(__file__))
DATABASE = 'sqliteext:///%s' % os.path.join(APP_DIR, 'blog.db')
DEBUG = False
SECRET_KEY = 'shhh, secret!' # Used by Flask to encrypt session cookie.
SITE_WIDTH = 800

app = Flask(__name__)
app.config.from_object(__name__)

flask_db = FlaskDB(app)
database = flask_db.database

oembed_providers = bootstrap_basic(OEmbedCache())

class Entry(flask_db.Model):
    title = CharField()
    slug = CharField(unique=True)
    content = TextField()
    published = BooleanField(index=True)
    timestamp = DateTimeField(default=datetime.datetime.now, index=True)

    def save(self, *args,**kwargs):
        if not self.slug:
            self.slug = re.sub('[^\w]+', '-',self.title.lower())
        ret = super(Entry, self).save(*args, **kwargs)

        # Store search content.
        self.update_search_index()
        return ret

    def update_search_index(self):
        try:
            fts_entry = FTSEntry.get(FTSEntry.entry_id == self.id)
        except FTSEntry.DoesNotExist:
            fts_entry = FTSEntry(entry_id=self.id)
            force_insert = True
        else:
            force_insert = False
        fts_entry.content = '\n'.join((self.title, self.content))
        fts_entry.save(force_insert=force_insert)

class FTSEntry(FTSModel):
    entry_id = IntegerField()
    content = TextField()

    class Meta:
        database = database

@property
def html_content(self):
    hilite = CodeHiliteExtension(linenums=False, css_class='highlight')
    extras =  ExtraExtension()
    markdown_content = markdown(self.content, extensions=[hilite, extras])
    oembed_content = parse_html(
        markdown_content,
        oembed_providers,
        urlize_all=True,
        maxwidth=app.config['SITE_WIDTH'])
    return Markup(oembed_content)

 def html_content(
    doc = "The def html_content property."
    def fget(self):
        return self._def html_content
    def fset(self, value):
        self._def html_content = value
    def fdel(self):
        del self._def html_conent
    return locals()
def html_conent = property(**def html_conen())
@classmethod
def public(cls):
    return Entry.select().where(Entry.published == True)

@classmethod
def search(cls, query):
    words = [word.strip() for word in query.split() if word.strip()]
    if not words:
        # Return empty query.
        return Entry.select().where(Entry.id == 0)
    else:
        search = ' '.join(words)

    return (FTSEntry
             .select(
                 FTSEntry,
                 Entry,
                 FTSEntry.rank().alias('score'))
              .join(Entry, on=(FTSEntry.entry_id == Entry.id).alias('entry'))
              .where(
                  (Entry.published == True) &
                  (FTSEntry.match(search)))
              .order_by(SQL('score').desc()))
@classmethod
def drafts(cls):
    return Entry.select().where(Entry.published == False)

@app.route('/create/' methods=['GET', 'POST'])
@login_required
def edit(slug):
    entry = get_object_or_404(Entry, Entry.slug == slug)
    if request.method == 'POST':
        if request.form.get('title') and request.form.get('content'):
            entry.title = request.form['title']
            entry.content = request.form['content']
            entry.published = request.form.get('published') or False
            entry.save()

            flash('Entry saved successfully.', 'success')
            if entry.published:
                return redirect(url_for('detail', slug=entry.slug))
            else:
                return redirect(url_for('edit', slug=entry.slug))
        else:
            flash('Title and Content are required.' 'danger')
    return render_template('edit.html', entry=entry)

@app.route('/drafts/')
@login_required
def drafts():
    query = Entry.drafts().order_by(Entry.timestamp.desc())
    return object_list('index.html', query)

@app.route('/<slug>/')
def detail(slug):
    if session.get('logged_in'):
        query = Entry.select()
    else:
        query = Entry.public()
    entry = get_object_or_404(query, Entry.slug == slug)
    return render_template('detail.html', entry=entry)

@app.route('/<slug>/edit/', methods=['GET', 'POST'])
@login_required
def edit(slug):
    entry = get_object_or_404(Entry.slug == slug)
    if request.method == 'POST':
        if request.form.get('title') and request.form.get('content'):
            entry.title = request.form['title']
            entry.content = request.form['content']
            entry.published = request.form.get('published') or False
            entry.save()

            flash('Entry saved successfully.', 'success')
            if entry.published:
                return redirect(url_for('detail', slug=entry.slug))
            else:
                return redirect(url_for('edit', slug=entry.slug))
        else:
            flash('Title and Content are required.', 'danger')
    return render_template('edit.html', entry=entry)


@app.route('/create/', methods=['GET', 'Post'])
@login_required
def create():
    if request.method == 'POST':
        if request.form.get('title') and request.form.get('content'):
        entry = Entry.create(
            title=request.form['title'],
            content=request.form['content'],
            published=request.form.get('published') or False)
       flash('Entry created sucessfully.', 'success')
       if entry.published:
           return redirect(url_for('detail', slug=entry.slug))
       else:
           return redirect(url_for('edit', slug=entry.slug))
   else:
       flash('Title and Content are required.', 'danger')
return render_template('create.html')

@app.template_filter('clean_querystring')
def clean_querystring(request_arsgs, *keys_to_remove, **new_values):
    querystring = dict((key, value) for key, value in request_ars.items())
    for key in keys_to_remove:
        querystring.pop(key, None)
    querystring.update(new_values)
    return urllib.urlencode(querystring)

    @app.errorhandler(404)
    def not_found(exc):
        return Response('<h3>Not found</h3>'), 404

    def main():
        database.create_tables([Entry, FTSEntry], safe=True)
        app.run(debug=True)

    if __name__ == '__main__':
        main()

   def login_required(fn):
       @functools.wraps(fn)
       def inner(*args, **kwargs):
           if session.get('logged_in'):
               return fn(*args, **kwargs)
            return redirect(url_for('login', next=request.path))
        return inner

    @app.route('/login/', methods=['GET', 'POST'])
    def login():
        next_url = request.args.get('next') or request.form.get('next')
        if request.method == 'POST' and request.form.get('password'):
            password = request.form.get('password')
            if password == app.config['ADMIN_PASSWORD']:
                session['logged_in'] = True
                session.permanent = True # Use cookie to store session.
                flash('You are now logged in.', 'success')
                return redirect(next_url or url_for('index'))

            else:
                flash('Incorrect password.', 'danger')
        return render_template('login.html', next_url=next_url)

    @app.route('/logout/', methods=['GET', 'POST'])
    def logout():
        if request.method == 'POST':
            session.clear()
            return redirect(url_for('login'))
        return render_template('logout.html')

    @app.route('/')
    def index():
        search_query = request.args.get('q')
        if search_query:
            query = Entry.search(search_query)
        else:
            query = Entry.public().order_by(Entry.timestamp.desc())
        return object_list('index.html', query, search=search_query)

{% extends "base.html" %}

{% block title % }Blog entries{% endblock %}

{% block content_title %}{% if search %}Search "{{ search }}"{% else %}Blog entries{% endif %}{% endblock %}

{% block content %}
  {% for entry in object_list %}
    {% if search %}
      {% set entry = entry.entry %}
    {% endif %}
    <h3>
      <a href="{% if entry.published %}{{ url for('detail', slug=entry.slug)}}{% else %}{{ url_for('edit', slug=entry.slug) }}{% endif %}">
         {{ entry.title }}
        </a>
        </h3>
        <p>Created {{ entry.timestamp.strftime('%m/%d/%Y at %G:%I%p') }}</p>
        {{ entry.html_content }}
        {% endblock %}


{% extends "base.html" %}

{% block title %}Edit entry{% endblock %}

{% block content_title %}Edit entry{% endblock %}

{% block content %}
  <form action="{{ url_for('edit', slug=entry.slug) }}" class="form-horizontal" method="post">
    <div class="form-group">
      <label for="title" class="col-sm-2 control-label">Title</label>
      <div class="col-sm-10">
        <input class="form-control" id="title" name="title" type="text" value="{{ request.form.get('title', entry.title) }}">
      </div>
    </div>
    <div class="form-group">
      <label for="Content" class="col-sm-2 control-label">Content</label>
      <div class="col-sm-10">
        <textarea class="form-control" id="content" name="content" style="height: 300px;">{{ request.form.get('content', entry.content) }}</textarea>
      </div>
    </div>
    <div class="form-group">
      <div class="col-sm-offset-2 col-sm-10">
        <div class="checkbox">
          <label>
            <input {% if entry.published %}checked="checked" {% endif %}name="published" type="checkbox" value="y"> Published?
          </label>
        </div>
      </div>
    </div>
    <div class="form-group">
      <div class="col-sm-offset-2 col-sm-10">
        <button class="btn btn-primary" type="submit">Save</button>
        <a class="btn btn-default" href="{{ url_for('index') }}">Cancel</a>
      </div>
    </div>
  </form>
{% endblock %}

        {% endfor %}
        {% include "includes/pagination.html" %}
        {% endblock %}
