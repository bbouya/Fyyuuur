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
from datetime import datetime
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

def total_num_of_upcoming_shows(id):
    return Venue.query.join(Venue.shows).filter(Show.start_time > datetime.now()).count()

def total_num_of_past_shows(id):
  return Venue.query.join(Venue.shows).filter(Show.start_time < datetime.now()).count()


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

  # TODO: replace with real venues data.
  # num_upcoming_shows should be aggregated based on number of upcoming shows per venue.
  
  VenuesListAll=[]

  venue_city = Venue.query.with_entities(Venue.city, Venue.state).distinct().order_by(Venue.city).order_by(Venue.state).all()

  allVenuesList = [] 
  for city, state in venue_city:
    groupedVenues = Venue.query.filter(Venue.city == city, Venue.state == state).all()
    venuesLocation = [city, state, groupedVenues]
    allVenuesList.append(venuesLocation)

  def ResponseObject(responseList):
    for x in responseList:
      object= {
        "city": x[0],
        "state": x[1],
        "venues": []
      }
      venues = x[2]
      for X in venues:
        sub_object={
          "id": X.id,
          "name": X.name,
          "num_upcoming_shows": total_num_of_upcoming_shows(X.id)
        }

        object["venues"].append(sub_object)

      VenuesListAll.append(object)

  ResponseObject(allVenuesList)

  return render_template('pages/venues.html', areas=VenuesListAll)


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
  # shows the venue page with the given venue_id
  # TODO: replace with real venue data from the venues table, using venue_id
  showVenue = Venue.query.get(venue_id)
  def past_shows(venue_id):
    return db.session.query(Show.venue_id, Show.artist_id, Artist.name, Artist.image_link, Show.start_time).join(Artist).filter(Show.venue_id == venue_id).filter(Show.start_time < datetime.now()).all()

  def upcoming_shows(venue_id):
    return db.session.query(Show.venue_id, Show.artist_id, Artist.name, Artist.image_link, Show.start_time).join(Artist).filter(Show.venue_id == venue_id).filter(Show.start_time > datetime.now()).all()

  Venue_Data={
  "id": showVenue.id,
  "name": showVenue.name,
  "genres": showVenue.genres,
  "address": showVenue.address,
  "city": showVenue.city,
  "state": showVenue.state,
  "phone": showVenue.phone,
  "website": showVenue.website_link,
  "facebook_link": showVenue.facebook_link ,
  "seeking_talent": showVenue.seeking_talent,
  "seeking_description": showVenue.seeking_description,
  "image_link": showVenue.image_link,
  "past_shows": [],
  "upcoming_shows": [],
  "past_shows_count": total_num_of_past_shows(venue_id),
  "upcoming_shows_count": total_num_of_upcoming_shows(venue_id),
  
  }

  past_shows = past_shows(venue_id)
  for show in past_shows:
    pastShows={
      "artist_id": show.artist_id,
      "artist_name": show.name,
      "artist_image_link": show.image_link,
      "start_time": show.start_time.strftime('%m/%d/%Y')
    }

    Venue_Data["past_shows"].append(pastShows)

  upcoming_shows = upcoming_shows(venue_id)
  for shows in upcoming_shows:
    upcomingShows={
      "artist_id": shows.artist_id,
      "artist_name": shows.name,
      "artist_image_link": shows.image_link,
      "start_time": shows.start_time.strftime('%m/%d/%Y')
    }
    Venue_Data["past_shows"].append(upcomingShows)
    
  return render_template('pages/show_venue.html', venue=Venue_Data)



#  Create Venue
#  ----------------------------------------------------------------

@app.route('/venues/create', methods=['GET'])
def create_venue_form():
  form = VenueForm()
  return render_template('forms/new_venue.html', form=form)

@app.route('/venues/create', methods=['POST'])
def create_venue_submission():
  #this is not secure but since we haven't done how to propaly
  #manage secret keys in this course, I guess we will leave it
  #till then so we can write meta={'csrf': True} or just leave
  #it as it is session secure.
  form = VenueForm(request.form, meta={'csrf': False})

  if form.validate():
    try:
      venue = Venue(
          name = form.name.data,
          city = form.city.data,
          state = form.state.data,
          address = form.address.data,
          phone = form.phone.data,
          genres = form.genres.data,
          image_link = form.image_link.data,
          facebook_link = form.facebook_link.data,
          website_link = form.website_link.data,
          seeking_talent = form.seeking_talent.data,
          seeking_description = form.seeking_description.data
      )

      db.session.add(venue)
      db.session.commit()
      flash('Venue, ' + form.name.data + ' was successfully listed!')
    except ValueError as e:
        print(e)
        db.session.rollback()
    finally:
        db.session.close()
  else:
      message = []
      for field, err in form.errors.items():
          message.append(field + ' ' + '|'.join(err))
      flash('Errors ' + str(message))
  return render_template('pages/home.html')

  


@app.route('/venues/<venue_id>', methods=['DELETE'])
def delete_venue(venue_id):
  # TODO: Complete this endpoint for taking a venue_id, and using
  # SQLAlchemy ORM to delete a record. Handle cases where the session commit could fail.
  #deleteVenue = Venue.query.get(venue_id)
  Venue.query.filter_by(id=venue_id).delete()
  try:
    db.session.commit()
    flash('Venue was successfully deleted.')
  except:
    db.session.rollback()
    print("MY MESSAGE ERROR: ", sys.exc_info())
    flash('An error occurred. Venue could not be deleted.')
  finally:
    db.session.close()
  return redirect(url_for('home.html'))



#  Artists
#  ----------------------------------------------------------------
@app.route('/artists')
def artists():
  # TODO: replace with real data returned from querying the database
  data = db.session.query(Artist.id, Artist.name).all()
  return render_template('pages/artists.html', artists=data)

@app.route('/artists/search', methods=['POST'])
def search_artists():
  # TODO: implement search on artists with partial string search. Ensure it is case-insensitive.
  # seach for "A" should return "Guns N Petals", "Matt Quevado", and "The Wild Sax Band".
  # search for "band" should return "The Wild Sax Band".

  # search_term=request.form('search_term', '')
  # search_result = Artist.query.filter(Artist.name.ilike(f'%{search_term}%')).all()
  # search_count = Artist.query.count(Artist.name.ilike(f'%{search_term}%')).count()
  # response = searchResponseBody(search_count, search_result)


  search_term=request.form['search_term']
 
  if search_term == "":
         flash('Please specify the name of the artist in your searchs.')
         return redirect(url_for('artists'))


def searchResponseBody(search_count, search_result):
  response={
    'count': search_count,
    'data': []
  }

  for result in search_result:
    venue ={
      'id': result.id,
      'name': result.name,
      'num_upcoming_shows': total_num_of_upcoming_shows(result.id)
    }

    response['data'].append(venue)
    return response
  return render_template('pages/search_artists.html', results=response, search_term=request.form('search_term', ''))


@app.route('/artists/<int:artist_id>')
def show_artist(artist_id):
  # shows the artist page with the given artist_id
  # TODO: replace with real artist data from the artist table, using artist_id

  showArtist = Artist.query.get(artist_id)

  def past_shows(artist_id):
      return db.session.query(Show.venue_id, Show.artist_id, Artist.name, Artist.image_link, Show.start_time).join(Venue).filter(Show.artist_id == artist_id).filter(Show.start_time < datetime.now()).all()

  def upcoming_shows(artist_id):
      return db.session.query(Show.venue_id, Show.artist_id, Artist.name, Artist.image_link, Show.start_time).join(Venue).filter(Show.artist_id == artist_id).filter(Show.start_time > datetime.now()).all()

  Artist_Data={
  "id": showArtist.id,
  "name": showArtist.name,
  "genres": showArtist.genres,
  "city": showArtist.city,
  "state": showArtist.state,
  "phone": showArtist.phone,
  "website": showArtist.website_link,
  "facebook_link": showArtist.facebook_link ,
  "seeking_talent": showArtist.seeking_venue,
  "seeking_description": showArtist.seeking_description,
  "image_link": showArtist.image_link,
  "past_shows": [],
  "upcoming_shows": [],
  "past_shows_count": total_num_of_past_shows(artist_id),
  "upcoming_shows_count": total_num_of_upcoming_shows(artist_id),
  
  }

  past_shows = past_shows(artist_id)
  for show in past_shows:
    pastShows={
      "artist_id": show.artist_id,
      "artist_name": show.name,
      "artist_image_link": show.image_link,
      "start_time": show.start_time.strftime('%m/%d/%Y')
    }

    Artist_Data["past_shows"].append(pastShows)

  upcoming_shows = upcoming_shows(artist_id)
  for show in upcoming_shows:
    upcomingShows={
      "artist_id": show.artist_id,
      "artist_name": show.name,
      "artist_image_link": show.image_link,
      "start_time": show.start_time.strftime('%m/%d/%Y')
    }

    Artist_Data["past_shows"].append(upcomingShows)
  return render_template('pages/show_artist.html', artist=Artist_Data)


#  Update
#  ----------------------------------------------------------------
@app.route('/artists/<int:artist_id>/edit', methods=['GET'])
def edit_artist(artist_id):
  form = ArtistForm()
  # TODO:artist with ID <artist_id>
  artist_data = Artist.query.get(artist_id)
  return render_template('forms/edit_artist.html', form=form, artist=artist_data)


@app.route('/artists/<int:artist_id>/edit', methods=['POST'])
def edit_artist_submission(artist_id):
  # TODO: take values from the form submitted, and update existing
  # artist record with ID <artist_id> using the new attributes

  form = ArtistForm(request.form)
  if form.validate():
    try:
      edit_artist = Artist.query.get(artist_id)   

      edit_artist.name = form.name.data
      edit_artist.city = form.city.data 
      edit_artist.state = form.state.data
      edit_artist.phone = form.phone.data
      edit_artist.genres = form.genres.data
      edit_artist.facebook_link = form.facebook_link.data
      edit_artist.image_link = form.image_link.data
      edit_artist.website_link = form.website_link.data
      edit_artist.seeking_venue = form.seeking_venue.data
      edit_artist.seeking_description = form.seeking_description.data
      db.session.add(edit_artist)
      db.session.commit()

      flash('Artist ' + form.name.data + ' was successfully updated!')

    except:
      db.session.rollback()
      flash('An error occurred. Artist ' + form.name.data + ' could not be updated.')

    finally: 
      db.session.close()
  else: 
      flash('Opps form error')

  return redirect(url_for('show_artist', artist_id=artist_id))



@app.route('/venues/<int:venue_id>/edit', methods=['GET'])
def edit_venue(venue_id):
  form = VenueForm()
  #populate form with values from venue with ID <venue_id>
  venue_data = Venue.query.get(venue_id)

  return render_template('forms/edit_venue.html', form=form, venue=venue_data)


@app.route('/venues/<int:venue_id>/edit', methods=['POST'])
def edit_venue_submission(venue_id):
  # TODO: take values from the form submitted, and update existing
  # venue record with ID <venue_id> using the new attributes
  form = VenueForm(request.form)
  if form.validate():

    try:
      venue_edit = Venue.query.get(venue_id)   

      venue_edit.name = form.name.data
      venue_edit.city = form.city.data 
      venue_edit.state = form.state.data
      venue_edit.address = form.address.data
      venue_edit.phone = form.phone.data
      venue_edit.genres = form.genres.data
      venue_edit.facebook_link = form.facebook_link.data
      venue_edit.image_link = form.image_link.data
      venue_edit.website_link = form.website_link.data
      venue_edit.seeking_talent = form.seeking_talent.data
      venue_edit.seeking_description = form.seeking_description.data
      db.session.add(venue_edit)
      db.session.commit()

      flash('Venue ' + form.name.data + ' was successfully updated!')

    except:
      db.session.rollback()
      flash('An error occurred. Venue ' + form.name.data + ' could not be updated.')

    finally: 
      db.session.close()

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
  # called upon submitting the new artist 
  form = ArtistForm(request.form)
  if form.validate():
    try:

      artists = Artist(
        name = form.name.data,
        city =  form.city.data,
        state = form.state.data,
        phone = form.phone.data,
        genres = form.genres.data,
        facebook_link = form.facebook_link.data,
        image_link = form.image_link.data,
        website_link = form.website_link.data,
        seeking_venue = form.seeking_venue.data,
        seeking_description = form.seeking_description.data
        )
      db.session.add(artists)
      db.session.commit()

    # on successful db insert, flash success
      flash('Artist ' + form.name.data + ' was successfully listed!')
    # TODO: on unsuccessful db insert, flash an error instead.
    # e.g., flash('An error occurred. Artist ' + data.name + ' could not be listed.'
    except:
      db.session.rollback()
      print(sys.exc_info())
      flash('An error occurred. Artist ' + form.name.data + ' could not be listed.')
    finally:
      db.session.close()
  else :
    flash('form problems')

  return render_template('pages/home.html')



#  Shows
#  ----------------------------------------------------------------
@app.route('/shows')
def shows():
  
  # displays list of shows at /shows
  # TODO: replace with real venues data.

  shows = db.session.query(Show.venue_id, Venue.name, Show.artist_id, Artist.name, Artist.image_link, Show.start_time).join(Venue).join(Artist).filter(Show.venue_id == Venue.id, Show.artist_id == Artist.id).all()
  print(shows)
  data_show=[]
  for show_data in shows:
    object={
      "venue_id": show_data[0],
      "venue_name": show_data[1],
      "artist_id": show_data[2],
      "artist_name": show_data[3],
      "artist_image_link": show_data[4],
      "start_time": show_data[5].strftime('%m/%d/%Y')
    }
    data_show.append(object)
  return render_template('pages/shows.html', shows=data_show)


@app.route('/shows/create')
def create_shows():
  form = ShowForm()
  return render_template('forms/new_show.html', form=form)

@app.route('/shows/create', methods=['POST'])
def create_show_submission():
  # called to create new shows in the database
  form = ShowForm(request.form)
  if form.validate():
    try:
      show = Show(
          artist_id = form.artist_id.data,
          venue_id = form.venue_id.data,
          start_time = form.start_time.data
      )

      db.session.add(show)
      db.session.commit()
      flash('Show was successfully listed!')
    except:
      db.session.rollback()
      flash('An error occured! Show could not be listed!')
  else:
    flash('form problem')

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