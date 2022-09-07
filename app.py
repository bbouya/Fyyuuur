#----------------------------------------------------------------------------#
from html.entities import name2codepoint
from itertools import count
import json
import string
from types import CoroutineType
from unicodedata import name
import dateutil.parser
import babel
from flask import Flask, render_template, request, Response, flash, redirect, url_for, abort
from flask_moment import Moment
from flask_migrate import Migrate
from flask_sqlalchemy import SQLAlchemy
import logging
from logging import Formatter, FileHandler
from flask_wtf import Form
from forms import *
from flask_wtf import FlaskForm
import sys
from models import Artist, Venue, Show, db

import collections
collections.Callable = collections.abc.Callable
#----------------------------------------------------------------------------#
# App Config.
#----------------------------------------------------------------------------#

app = Flask(__name__)
moment = Moment(app)
app.config.from_object('config')
# db = SQLAlchemy(app)
db.init_app(app)
migrate = Migrate(app,db)

# TODO: connect to a local postgresql database

#----------------------------------------------------------------------------#

# Filters.
#----------------------------------------------------------------------------#

def format_datetime(value, format='medium'):
  date = dateutil.parser.parse(value)
  if format == 'full':
      format="EEEE MMMM, d, y 'at' h:mma"
  elif format == 'medium':
      format="EE MM, dd, y h:mma"
  return babel.dates.format_datetime(date, format, locale='en')

app.jinja_env.filters['datetime'] = format_datetime

#----------------------------------------------------------------------------#
# Controllers.
#----------------------------------------------------------------------------#

@app.route('/')
def index():
  return render_template('pages/home.html')


#  Venues
#  ----------------------------------------------------------------

@app.route('/venues')
def venues():
  query = Venue.query.order_by('state', 'city', 'name').all()
  list_of_data = []
  for x in query:
    list_of_data.append(x.city.strip() +"|"+ x.state.strip())  
  
  areas_data = set(list_of_data)
  data_all = [] 
  for x in areas_data:
    dic = {}
    dic['city'] = x.split("|")[0]
    dic['state'] = x.split("|")[1]
    venues = []
    for x in Venue.query.filter(Venue.city == dic['city'] , Venue.state == dic['state']).all():
      dictio = {}
	    
      dictio['id'] = x.id
      dictio['name'] = x.name
      dictio['num_upcoming_shows'] = len(x.show)
      venues.append(dictio)
  	  
    dic['venues'] = venues
    data_all.append(dic)

  return render_template('pages/venues.html', areas=data_all);

@app.route('/venues/search', methods=['POST'])
def search_venues():
	
	search_term = "%{}%".format(request.form.get('search_term', '').replace(" ", "\ "))
	resp = {}
	resp['data'] = []
	for x in Venue.query.filter(Venue.name.ilike(search_term)).all():
		data = {}
		data['id'] = x.id
		data['name'] = x.name
		data['num_upcoming_shows'] = len(x.show)
		resp['data'].append(data)
	resp['count'] = len(resp['data'])
	return render_template('pages/search_venues.html', results=resp, search_term=request.form.get('search_term', ''))

@app.route('/venues/<int:venue_id>')
def show_venue(venue_id):
	venue = Venue.query.get(venue_id)
	setattr(venue, 'past_shows', [])
	setattr(venue, 'upcoming_shows', [])
	current_time = datetime.now()
	past_show_count = 0
	upcoming_shows_count = 0
	shows = db.session.query(Artist, Show.date).join(Show).filter(Show.venue_id == venue_id)
	for artist, date in shows:
		temp = {'artist_id': artist.id,'artist_name': artist.name,'artist_image_link': artist.image_link,'start_time': str(date)}
		if date < current_time:
			venue.past_shows.append(temp)
			past_show_count += 1
		else:
			venue.upcoming_shows.append(temp)
			upcoming_shows_count += 1
	setattr(venue, 'past_show_count', past_show_count)
	setattr(venue, 'upcoming_show_count', upcoming_shows_count)
	setattr(venue, 'genres', venue.genres.split(' , '))
	setattr(venue, 'facebook_link', venue.facebook_link)
	setattr(venue, 'website', venue.website_link)

	
	return render_template('pages/show_venue.html', venue=venue)


#  Create Venue
#  ----------------------------------------------------------------

@app.route('/venues/create', methods=['GET'])
def create_venue_form():
  form = VenueForm()
  return render_template('forms/new_venue.html', form=form)

@app.route('/venues/create', methods=['POST'])
def create_venue_submission():

	error = False
	try:
		name = request.form['name']
		city = request.form['city']
		state = request.form['state']
		address = request.form['address']
		phone = int(request.form['phone'])
		genres = " , ".join(request.form.getlist('genres'))
		facebook_link = request.form['facebook_link']
		image_link = request.form['image_link']
		website_link = request.form['website_link']
		seeking_talent = False
		if 'seeking_talent' in request.form.keys():
			seeking_talent = True
		seeking_description = request.form['seeking_description']
		venue = Venue(name = name, city = city, state = state, address = address, phone = phone, genres = genres, image_link = image_link, website_link = website_link, seeking_talent = seeking_talent, seeking_description = seeking_description)
		db.session.add(venue)
		db.session.commit()
	except Exception as e:
		db.session.rollback()
		error = True
		print(e)
	finally:
		db.session.close()
	
	if error:
		flash('An error occured. Venue ' + request.form['name'] + ' could not be listed.')
	else:
		flash('Venue ' + request.form['name'] + ' was it successfully listed!')

	return render_template('pages/home.html')

@app.route('/venues/<venue_id>', methods=['DELETE'])
def delete_venue(venue_id):
  # TODO: Complete this endpoint for taking a venue_id, and using
  # SQLAlchemy ORM to delete a record. Handle cases where the session commit could fail.
  venue = db.session.query(Venue).filter(Venue.id == venue_id).first()
  if not venue:
        flash('No artist to delete')
        return redirect('/artists')
  if len(venue.shows) != 0:
        flash('You can\'t delete artists linked to some shows')
        return redirect('/artists/'+str(venue))
  db.session.delete(venue)
  db.session.commit()
  return redirect('/venues')

  # BONUS CHALLENGE: Implement a button to delete a Venue on a Venue Page, have it so that
  # clicking that button delete it from the db then redirect the user to the homepage
  return None

#  Artists
#  ----------------------------------------------------------------
@app.route('/artists')
def artists():
  # TODO: replace with real data returned from querying the database
  artist = db.session.query(Artist).all()
  data = []
  for a in artist:
    data.append({
      "id":a.id,
      "name":a.name
    })
  return render_template('pages/artists.html', artists=data)

@app.route('/artists/search', methods=['POST'])
def search_artists():
  global search_data
  # TODO: implement search on artists with partial string search. Ensure it is case-insensitive.(ilike does this)
  # seach for "A" should return "Guns N Petals", "Matt Quevado", and "The Wild Sax Band".
  # search for "band" should return "The Wild Sax Band".
  search_term = request.form.get('search_term', '')
  artist_search = db.session.query(Artist).filter((Artist.name.ilike('%{}%'.format(search_term)))).all()
  response={
    "count": 0,
    "data": []
  }
  for artist in artist_search:
        search_data = {
            "id": artist.id,
            "name": artist.name,
            "num_upcoming_shows": len(artist.shows)
        }
  response["data"].append(search_data)
  response['count'] = len(response['data'])

  return render_template('pages/search_artists.html', results=response, search_term=request.form.get('search_term', ''))

@app.route('/artists/<int:artist_id>')
def show_artist(artist_id):

	current_time = datetime.now()
	artist = Artist.query.get(artist_id)
	setattr(artist, 'past_shows', [])
	setattr(artist, 'upcoming_shows', [])
	past_shows_count = 0
	upcoming_shows_count = 0
	showses = db.session.query(Venue, Show.date).join(Show).filter(Show.artist_id == artist_id)
	for venue, date in showses:
		temp = {'venue_id': venue.id,'venue_name': venue.name,'venue_image_link': venue.image_link,'start_time': str(date)}
		if date < current_time:
			artist.past_shows.append(temp)
			past_shows_count += 1
		else:
			artist.upcoming_shows.append(temp)
			upcoming_shows_count += 1
	setattr(artist, 'past_shows_count', past_shows_count)
	setattr(artist, 'upcoming_shows_count', upcoming_shows_count)
	setattr(artist, 'website', artist.website_link)
	setattr(artist, 'genres', artist.genres.split(' , '))
	setattr(artist, 'seeking_venue', artist.seeking_venues)
	return render_template('pages/show_artist.html', artist=artist)

#  Update
#  ----------------------------------------------------------------
@app.route('/artists/<int:artist_id>/edit', methods=['GET'])
def edit_artist(artist_id):
  artist = Artist.query.filter(Artist.id == artist_id).first()
  if not artist:
        flash('Venue not found!', 'error')
        return redirect('/venues')
   # TODO: populate form with values from venue with ID <venue_id>
  form = ArtistForm(request.form)
  form.name.data =  artist.name,
  form.city.data = artist.city,
  form.state.data = artist.state,
  form.phone.data = artist.phone,
  form.website_link.data = artist.website,
  form.city.data = artist.city,
  form.seeking_venue.data = artist.seeking_venue
  form.seeking_description.data = artist.seeking_description,
  form.image_link.data = artist.image_link    
  # TODO: populate form with fields from artist with ID <artist_id>
  return render_template('forms/edit_artist.html', form=form, artist=artist)

@app.route('/artists/<int:artist_id>/edit', methods=['POST'])
def edit_artist_submission(artist_id):
  artist = Artist.query.filter(Artist.id == artist_id).first()
  form = ArtistForm(request.form) 
  form.validate() # TODO: take values from the form submitted, and update existing
  # artist record with ID <artist_id> using the new attributes
  try:
    artist.name = form['name']
    artist.genres =form['genres']
    artist.city = form['city']
    artist.state= form['state']
    artist.phone = form['phone']
    artist.website = form['website_link']
    artist.facebook_link = form['city']
    artist.seeking_venue = form['seeking_venue']
    artist.seeking_description =form['seeking_description']
    artist.image_link=form['image_link']
    db.session.commit()
  except Exception:
          error = True
          db.session.rollback()
          print(sys.exc_info())
  finally:
          db.session.close()

  if error:
          flash('An error occurred. Artist '+ name + ' could not be updated.')
  if not error:
          flash('Artist '+ name + ' was successfully updated!','success')

  return redirect(url_for('show_artist', artist_id=artist_id))

@app.route('/venues/<int:venue_id>/edit', methods=['GET'])
def edit_venue(venue_id):
  venue = Venue.query.filter(Venue.id == venue_id).first()
  if not venue:
        flash('Venue not found!', 'error')
        return redirect('/venues')
   # TODO: populate form with values from venue with ID <venue_id>
  form = VenueForm(request.form)
  form.name.data =  venue.name,
  form.city.data = venue.city,
  form.state.data = venue.state,
  form.phone.data = venue.phone,
  form.website_link.data = venue.website,
  form.city.data = venue.city,
  form.seeking_talent.data = venue.seeking_talent
  form.seeking_description.data = venue.seeking_description,
  form.image_link.data = venue.image_link    
      
 
  return render_template('forms/edit_venue.html', form=form, venue=venue)

@app.route('/venues/<int:venue_id>/edit', methods=['POST'])
def edit_venue_submission(venue_id):
  # TODO: take values from the form submitted, and update existing
  # Request data
  venue = Venue.query.filter(Venue.id == venue_id).first()

  
  form = VenueForm(request.form)
  venue.name = form['name']
  venue.genres=form['genres']
  venue.city = form['city']
  venue.state= form['state']
  venue.phone = form['phone']
  venue.website = form['website_link']
  venue.facebook_link = form['city']
  venue.seeking_talent = form['seeking_talent']
  venue.seeking_description =form['seeking_description']
  venue.image_link=form['image_link']
  # venue record with ID <venue_id> using the new attributes
  db.session.commit()
  return redirect(url_for('show_venue', venue_id=venue_id))

#  Create Artist
#  ----------------------------------------------------------------

@app.route('/artists/create', methods=['GET'])
def create_artist_form():
  form = ArtistForm()
  return render_template('forms/new_artist.html', form=form)

#Create artist
@app.route('/artists/create', methods=['POST'])
def create_artist_submission():
	error = False
	
	try:
		name = request.form['name']
		city = request.form['city']
		state = request.form['state']
		phone = int(request.form['phone'])
		genres = " , ".join(request.form.getlist('genres'))
		facebook_link = request.form['facebook_link']
		image_link = request.form['image_link']
		website_link = request.form['website_link']
		seeking_venues = False
		if 'seeking_venue' in request.form.keys():
			seeking_venues = True
		seeking_description = request.form['seeking_description']
		artist = Artist(name = name, city = city, state = state, phone = phone, genres = genres, facebook_link = facebook_link, image_link = image_link, website_link = website_link, seeking_venues = seeking_venues, seeking_description = seeking_description)
		db.session.add(artist)
		db.session.commit()
	except Exception as e:
		db.session.rollback()
		error = True
		print(e)
	finally:
		db.session.close()

	if error:
		flash('An error occurred. Artist ' + request.form['name'] + ' could not be listed error.')
	else:
		flash('Artist  ' + request.form['name'] + '  was successfully listed')
	return render_template('pages/home.html')



#  Shows
#  ----------------------------------------------------------------
@app.route('/shows')
def shows():
	data_show = []
	for x in Show.query.all():
		data_show.append({
			"venue_id": x.venue.id,
			"venue_name":x.venue.name,
			"artist_id": x.artist.id,
			"artist_image_link": x.artist.image_link,
			"start_time": str(x.date)
			})

	return render_template('pages/shows.html', shows=data_show)


@app.route('/shows/create')
def create_shows():
  # renders form. do not touch.
  form = ShowForm()
  return render_template('forms/new_show.html', form=form)

@app.route('/shows/create', methods=['POST'])
def create_show_submission():
  # called to create new shows in the db, upon submitting new show listing form
  # TODO: insert form data as a new Show record in the db, instead
    data = request.form
    show = Show()
    artist = db.session.query(Artist).filter_by(id=data['artist_id']).first()#filtering using the foreign key to find a venues existence;    
    # Check if artist to link exists
    if not artist:
        flash('Wrong user for the show!')
        return redirect('/shows/create')
    venue = db.session.query(Venue).filter_by(id=data['venue_id']).first()#filtering using the foreign key to find a venues existence
    # Check if Venue to link to the show exist
    if not venue:
        flash('Wrong venue for the show!')
        return redirect('/shows/create')
    try:
        show.start_time = dateutil.parser.parse(data['start_time'])
    except:
        flash('Wrong date for the show!')
        return redirect('/shows/create')
    show.artist_id = artist.id
    show.venue_id = venue.id
    db.session.add(show)
    db.session.commit()
  # on successful db insert, flash success
    flash('Show was successfully listed!')
  # TODO: on unsuccessful db insert, flash an error instead.
  # e.g., flash('An error occurred. Show could not be listed.')
  # see: http://flask.pocoo.org/docs/1.0/patterns/flashing/
    return render_template('pages/home.html')

@app.errorhandler(404)
def not_found_error(error):
    return render_template('errors/404.html'), 404

@app.errorhandler(500)
def server_error(error):
    return render_template('errors/500.html'), 500


if not app.debug:
    file_handler = FileHandler('error.log')
    file_handler.setFormatter(
        Formatter('%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]')
    )
    app.logger.setLevel(logging.INFO)
    file_handler.setLevel(logging.INFO)
    app.logger.addHandler(file_handler)
    app.logger.info('errors')

#----------------------------------------------------------------------------#
# Launch.
#----------------------------------------------------------------------------#

# Default port:
if __name__ == '__main__':
    app.run()

# Or specify port manually:
'''
if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
'''