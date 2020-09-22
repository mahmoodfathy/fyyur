#----------------------------------------------------------------------------#
# Imports
#----------------------------------------------------------------------------#

import json
import dateutil.parser
import babel
from flask import Flask, render_template, request, Response, flash, redirect, url_for
from flask_moment import Moment
from flask_sqlalchemy import SQLAlchemy
import logging
from logging import Formatter, FileHandler
from flask_wtf import Form
from forms import *
from flask_migrate import Migrate
from sqlalchemy import func

#----------------------------------------------------------------------------#
# App Config.
#----------------------------------------------------------------------------#

app = Flask(__name__)
moment = Moment(app)
app.config.from_object('config')
db = SQLAlchemy(app)


# TODO: connect to a local postgresql database
Migrate(app,db)

from models import *
#----------------------------------------------------------------------------#
# Filters.
#----------------------------------------------------------------------------#

def format_datetime(value, format='medium'):
  date = dateutil.parser.parse(value)
  if format == 'full':
      format="EEEE MMMM, d, y 'at' h:mma"
  elif format == 'medium':
      format="EE MM, dd, y h:mma"
  return babel.dates.format_datetime(date, format,locale="en")

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
  #       num_shows should be aggregated based on number of upcoming shows per venue.
  venues_areas = db.session.query(func.count(Venue.id), Venue.city, Venue.state).group_by(Venue.city, Venue.state).all()
  # print(venues_areas)
  data = []
  cities = []
  states = []

  for a in venues_areas:
      venues = Venue.query.filter_by(state=a.state).filter_by(city=a.city).all()
      print(venues)
      venues_data = []

      for venue in venues:
          venues_data.append({
              "id": venue.id,
              "name": venue.name,
              "num_upcoming_shows": len(
                  Show.query.filter(Show.venue_id == 1).filter(Show.start_time > datetime.now()).all())
          })
          cities.append(a.city)
          states.append(a.state)
          data.append({
              "city": a.city,
              "state": a.state,
              "venues": venues_data

          })
  duplictae_cities_list, cities_indices = determine_duplicate(cities)
  duplictae_states_list, states_indices = determine_duplicate(states)
  print(duplictae_cities_list, cities_indices)
  print(duplictae_states_list, states_indices)
  cities_indices_set = set(cities_indices)
  intersection = list(cities_indices_set.intersection(states_indices))
  print(intersection)
  for city, state in zip(cities, states):
      if (city == duplictae_cities_list[cities_indices[0]]) and (state == duplictae_states_list[states_indices[0]]):
          data.pop(intersection[0])
          break
  print(data)
  print(cities, states)
  # data=[{
  #   "city":"New York",
  #   "state": "NY",
  #   "venues": [{
  #     "id": 1,
  #     "name": "The Musical Hop",
  #     "num_upcoming_shows": 0,
  #   }, {
  #     "id": 3,
  #     "name": "Park Square Live Music & Coffee",
  #     "num_upcoming_shows": 1,
  #   }]
  # }, {
  #   "city": "New York",
  #   "state": "NY",
  #   "venues": [{
  #     "id": 2,
  #     "name": "The Dueling Pianos Bar",
  #     "num_upcoming_shows": 0,
  #   },
  #       {
  #           "id": 3,
  #           "name": "Park Square Live Music & Coffee",
  #           "num_upcoming_shows": 1,
  #       }
  #   ]
  # }]
  return render_template('pages/venues.html', areas=data);

@app.route('/venues/search', methods=['POST'])
def search_venues():
  # TODO: implement search on artists with partial string search. Ensure it is case-insensitive.
  # seach for Hop should return "The Musical Hop".
  # search for "Music" should return "The Musical Hop" and "Park Square Live Music & Coffee"
  search_term = request.form['search_term']
  venues_search = Venue.query.filter(Venue.name.ilike(f'%{search_term}%')).all()
  data = []
  for venue in venues_search:
      data.append({
          "id":venue.id,
          "name":venue.name,
          "num_upcoming_shows":len(Show.query.join(Artist).filter(Show.venue_id==venue.id).filter(Show.start_time>datetime.now()).all())

      })

  response={
    "count": len(venues_search),
    "data": data
  }
  return render_template('pages/search_venues.html', results=response, search_term=request.form.get('search_term', ''))

@app.route('/venues/<int:venue_id>')
def show_venue(venue_id):
  # shows the venue page with the given venue_id
  # TODO: replace with real venue data from the venues table, using venue_id
  venue = Venue.query.get(venue_id)
  print(venue)
  if not venue:
    return render_template('errors/404.html')
  past_shows_result =  Show.query.join(Artist).filter(Show.venue_id==venue_id).filter(Show.start_time<datetime.now()).all()
  past_shows = []
  upcoming_shows_result= Show.query.join(Artist).filter(Show.venue_id==venue_id).filter(Show.start_time>datetime.now()).all()
  upcoming_shows = []
  for past_show in past_shows_result:
    past_shows.append({
      "artist_id":past_show.artist_id,
      "artist_name":past_show.artist.name,
      "artist_image_link":past_show.artist.image_link,
      "start_time": past_show.start_time.strftime('%Y-%m-%d %H:%M:%S')

    })
  for upcoming_show in upcoming_shows_result:
    upcoming_shows.append({
      "artist_id": upcoming_show.artist_id,
      "artist_name": upcoming_show.artist.name,
      "artist_image_link": upcoming_show.artist.image_link,

      "start_time": upcoming_show.start_time.strftime('%Y-%m-%d %H:%M:%S')
    })
  data={
    "id": venue.id ,
    "name": venue.name,
    "genres": venue.genres,
    "address": venue.address,
    "city":venue.city ,
    "state": venue.state,
    "phone": venue.phone,
    "website": venue.website,
    "facebook_link": venue.facebook_link,
    "seeking_talent": venue.seeking_talent,
    "seeking_description": venue.seeking_description,
    "image_link": venue.image_link,
    "past_shows": past_shows,
    "upcoming_shows": upcoming_shows,
    "past_shows_count": len(past_shows),
    "upcoming_shows_count": len(upcoming_shows),
  }

  return render_template('pages/show_venue.html', venue=data)

#  Create Venue
#  ----------------------------------------------------------------

@app.route('/venues/create', methods=['GET'])
def create_venue_form():
  form = VenueForm()
  # if form.validate_on_submit():
  #   return redirect(url_for('/venues/create'))


  return render_template('forms/new_venue.html', form=form)

@app.route('/venues/create', methods=['POST'])
def create_venue_submission():
  form = VenueForm()
  # TODO: insert form data as a new Venue record in the db, instead
  # TODO: modify data to be the data object returned from db insertion
  error=False
  try:
    name = request.form['name']

    phone = request.form['phone']
    city = request.form['city']
    state = request.form['state']
    address = request.form['address']
    image_link = request.form['image_link']
    genres = request.form.getlist('genres')


    seeking_talent = request.form.get('seeking_talent')
    if seeking_talent == 'y':
      seeking_talent = True
    # else:
    #     seeking_talent = False


    seeking_description = request.form['seeking_description']
    website = request.form['website']

    facebook_link = request.form['facebook_link']
    print(name, city,state,address,image_link,genres,facebook_link,seeking_talent,seeking_description,website)
    venue = Venue(name=name, phone=phone, city=city, state=state, address=address, image_link=image_link, genres=genres,facebook_link=facebook_link,seeking_talent=seeking_talent,seeking_description=seeking_description,website=website)
    print(venue)
    if form.validate_on_submit():
      return redirect(url_for('create_venue_form'))
    db.session.add(venue)
    db.session.commit()


  except:
    error = True
    db.session.rollback()


  finally:
    db.session.close()
    # on successful db insert, flash success

    # TODO: on unsuccessful db insert, flash an error instead.
    # e.g., flash('An error occurred. Venue ' + data.name + ' could not be listed.')
    # see: http://flask.pocoo.org/docs/1.0/patterns/flashing/
    if error:
      flash('An error occurred. Venue ' + request.form['name'] + ' could not be listed.')
    if not error:
      flash('Venue ' + request.form['name'] + ' was successfully listed!')

    return redirect(url_for('index'))





@app.route('/venues/<venue_id>/delete', methods=['POST'])
def delete_venue(venue_id):
    venue = Venue.query.get(venue_id)
    print(venue)
    error=False
    try:
        db.session.delete(venue)
        db.session.commit()
    except:
        error=True
        db.session.rollback()
    finally:
        db.session.close()
        if not error:
            flash("deleted successfully")

        if error:
            flash('couldnot delete venue')
    return render_template('pages/home.html')

  # TODO: Complete this endpoint for taking a venue_id, and using
  # SQLAlchemy ORM to delete a record. Handle cases where the session commit could fail.

  # BONUS CHALLENGE: Implement a button to delete a Venue on a Venue Page, have it so that
  # clicking that button delete it from the db then redirect the user to the homepage


#  Artists
#  ----------------------------------------------------------------
@app.route('/artists')
def artists():
  # TODO: replace with real data returned from querying the database
  data = Artist.query.all()
  return render_template('pages/artists.html', artists=data)

@app.route('/artists/search', methods=['POST'])
def search_artists():
  # TODO: implement search on artists with partial string search. Ensure it is case-insensitive.
  # seach for "A" should return "Guns N Petals", "Matt Quevado", and "The Wild Sax Band".
  # search for "band" should return "The Wild Sax Band".
  search_term = request.form['search_term']
  artist_search = Artist.query.filter(Artist.name.ilike(f'%{search_term}%')).all()
  print(artist_search)
  data = []
  for artist in artist_search :
      data.append({
          "id":artist.id,
          "name":artist.name,
          "num_upcoming_shows":len(Show.query.join(Venue).filter(Show.artist_id == artist.id).filter(
    Show.start_time > datetime.now()).all())
      })

  response={
    "count": len(artist_search),
    "data":data
  }
  return render_template('pages/search_artists.html', results=response, search_term=request.form.get('search_term', ''))

@app.route('/artists/<int:artist_id>',methods=['GET'])
def show_artist(artist_id):
  # shows the venue page with the given venue_id
  # TODO: replace with real venue data from the venues table, using venue_id
  artist = Artist.query.get(artist_id)
  print(artist)
  if not artist:
    return render_template('errors/404.html')
  past_shows_result = Show.query.join(Venue).filter(Show.artist_id == artist_id).filter(Show.start_time < datetime.now()).all()
  past_shows = []
  upcoming_shows_result = Show.query.join(Venue).filter(Show.artist_id == artist_id).filter(
    Show.start_time > datetime.now()).all()
  upcoming_shows = []
  for past_show in past_shows_result:
    past_shows.append({
      "venue_id": past_show.venue_id,
      "venue_name": past_show.venue.name,
      "artist_image_link": past_show.venue.image_link,
      "start_time": past_show.start_time.strftime('%Y-%m-%d %H:%M:%S')
    })
  for upcoming_show in upcoming_shows_result:
    upcoming_shows.append({
      "venue_id": upcoming_show.venue_id,
      "venue_name": upcoming_show.venue.name,
      "artist_image_link": upcoming_show.venue.image_link,
      "start_time": upcoming_show.start_time.strftime('%Y-%m-%d %H:%M:%S')
    })
  data={
    "id": artist.id,
    "name": artist.name,
    "genres": artist.genres,
    "city": artist.city,
    "state": artist.city,
    "phone": artist.phone,
    "website": artist.website,
    "facebook_link": artist.facebook_link,
    "seeking_venue": artist.seeking_venue,
    "seeking_description":artist.seeking_description,
    "image_link": artist.image_link,
    "past_shows": past_shows,
    "upcoming_shows": upcoming_shows,
    "past_shows_count": len(past_shows),
    "upcoming_shows_count": len(upcoming_shows),
  }

  return render_template('pages/show_artist.html', artist=data)

#  Update
#  ----------------------------------------------------------------
@app.route('/artists/<int:artist_id>/edit', methods=['GET'])
def edit_artist(artist_id):
  form = ArtistForm()
  artist = Artist.query.get(artist_id)
  if artist:

      form.name.data = artist.name
      form.city.data = artist.city
      form.state.data = artist.state
      form.phone.data = artist.phone
      form.genres.data = artist.genres
      form.facebook_link.data = artist.facebook_link
      form.image_link.data = artist.image_link
      form.website.data = artist.website
      form.seeking_venue.data = artist.seeking_venue
      form.seeking_description.data = artist.seeking_description
  # artist={
  #   "id": 4,
  #   "name": "Guns N Petals",
  #   "genres": ["Rock n Roll"],
  #   "city": "San Francisco",
  #   "state": "CA",
  #   "phone": "326-123-5000",
  #   "website": "https://www.gunsnpetalsband.com",
  #   "facebook_link": "https://www.facebook.com/GunsNPetals",
  #   "seeking_venue": True,
  #   "seeking_description": "Looking for shows to perform at in the San Francisco Bay Area!",
  #   "image_link": "https://images.unsplash.com/photo-1549213783-8284d0336c4f?ixlib=rb-1.2.1&ixid=eyJhcHBfaWQiOjEyMDd9&auto=format&fit=crop&w=300&q=80"
  # }
  # TODO: populate form with fields from artist with ID <artist_id>
  return render_template('forms/edit_artist.html', form=form, artist=artist)

@app.route('/artists/<int:artist_id>/edit', methods=['POST'])
def edit_artist_submission(artist_id):

  # TODO: take values from the form submitted, and update existing
  # artist record with ID <artist_id> using the new attributes
  error = False
  artist = Artist.query.get(artist_id)

  try:
      artist.name = request.form['name']

      artist.phone = request.form['phone']
      artist.city = request.form['city']
      artist.state = request.form['state']
      artist.image_link = request.form['image_link']
      artist.genres = request.form.getlist('genres')

      artist.facebook_link = request.form['facebook_link']
      artist.seeking_venue = request.form.get('seeking_venue')
      if artist.seeking_venue == 'y':
          artist.seeking_venue = True

      artist.seeking_description = request.form['seeking_description']
      artist.website = request.form['website']
      print(artist.name, artist.city, artist.state, artist.image_link, artist.genres, artist.facebook_link)
      db.session.commit()




  except:
      error = True
      db.session.rollback()

  finally:
      db.session.close()
      # on successful db insert, flash success

      # TODO: on unsuccessful db insert, flash an error instead.
      # e.g., flash('An error occurred. Venue ' + data.name + ' could not be listed.')
      # see: http://flask.pocoo.org/docs/1.0/patterns/flashing/
      if error:
          flash('An error occurred. Artist ' + request.form['name'] + ' could not be updated.')
      if not error:
          flash('Artist ' + request.form['name'] + ' was successfully updated!')
      return redirect(url_for('show_artist', artist_id=artist_id))




@app.route('/venues/<int:venue_id>/edit', methods=['GET'])
def edit_venue(venue_id):
  form = VenueForm()
  venue = Venue.query.get(venue_id)
  if venue:

      form.name.data = venue.name
      form.address.data = venue.address
      form.city.data = venue.city
      form.state.data = venue.state
      form.phone.data = venue.phone
      form.genres.data = venue.genres
      form.facebook_link.data = venue.facebook_link
      form.image_link.data = venue.image_link
      form.website.data = venue.website
      form.seeking_talent.data = venue.seeking_talent
      form.seeking_description.data = venue.seeking_description
  # venue={
  #   "id": 1,
  #   "name": "The Musical Hop",
  #   "genres": ["Jazz", "Reggae", "Swing", "Classical", "Folk"],
  #   "address": "1015 Folsom Street",
  #   "city": "San Francisco",
  #   "state": "CA",
  #   "phone": "123-123-1234",
  #   "website": "https://www.themusicalhop.com",
  #   "facebook_link": "https://www.facebook.com/TheMusicalHop",
  #   "seeking_talent": True,
  #   "seeking_description": "We are on the lookout for a local artist to play every two weeks. Please call us.",
  #   "image_link": "https://images.unsplash.com/photo-1543900694-133f37abaaa5?ixlib=rb-1.2.1&ixid=eyJhcHBfaWQiOjEyMDd9&auto=format&fit=crop&w=400&q=60"
  # }
  # TODO: populate form with values from venue with ID <venue_id>
  return render_template('forms/edit_venue.html', form=form, venue=venue)

@app.route('/venues/<int:venue_id>/edit', methods=['POST'])
def edit_venue_submission(venue_id):
  # TODO: take values from the form submitted, and update existing
  # venue record with ID <venue_id> using the new attributes
  error = False
  venue = Venue.query.get(venue_id)

  try:
      venue.name = request.form['name']

      venue.phone = request.form['phone']
      venue.address = request.form['address']
      venue.city = request.form['city']
      venue.state = request.form['state']
      venue.image_link = request.form['image_link']
      venue.genres = request.form.getlist('genres')

      venue.facebook_link = request.form['facebook_link']
      venue.seeking_talent = request.form.get('seeking_talent')
      if venue.seeking_talent == 'y':
          venue.seeking_talent = True

      venue.seeking_description = request.form['seeking_description']
      venue.website = request.form['website']
      print(venue.name, venue.address, venue.city, venue.state, venue.image_link, venue.genres, venue.facebook_link)
      db.session.commit()




  except:
      error = True
      db.session.rollback()

  finally:
      db.session.close()
      # on successful db insert, flash success

      # TODO: on unsuccessful db insert, flash an error instead.
      # e.g., flash('An error occurred. Venue ' + data.name + ' could not be listed.')
      # see: http://flask.pocoo.org/docs/1.0/patterns/flashing/
      if error:
          flash('An error occurred. Venue ' + request.form['name'] + ' could not be updated.')
      if not error:
          flash('Venue ' + request.form['name'] + ' was successfully updated!')
      return redirect(url_for('show_venue', venue_id=venue_id))


#  Create Artist
#  ----------------------------------------------------------------

@app.route('/artists/create', methods=['GET'])
def create_artist_form():
  form = ArtistForm()
  return render_template('forms/new_artist.html', form=form)

@app.route('/artists/create', methods=['POST'])
def create_artist_submission():
  # called upon submitting the new artist listing form
  # TODO: insert form data as a new Venue record in the db, instead
  # TODO: modify data to be the data object returned from db insertion
  form = ArtistForm()


  error=False
  try:
    name = request.form['name']

    phone = request.form['phone']
    city = request.form['city']
    state = request.form['state']
    image_link = request.form['image_link']
    genres = request.form.getlist('genres')

    facebook_link = request.form['facebook_link']
    seeking_venue = request.form.get('seeking_venue')
    if seeking_venue == 'y':
      seeking_venue = True


    seeking_description = request.form['seeking_description']
    website = request.form['website']
    print(name, city,state,image_link,genres,facebook_link)
    artist = Artist(name=name, phone=phone, city=city, state=state, image_link=image_link, genres=genres,facebook_link=facebook_link,seeking_venue=seeking_venue,seeking_description=seeking_description,website=website)
    print(Artist)
    if form.validate_on_submit():
        return redirect(url_for('create_artist_form'))
    db.session.add(artist)
    db.session.commit()


  except:
    error = True
    db.session.rollback()

  finally:
    db.session.close()
    # on successful db insert, flash success

    # TODO: on unsuccessful db insert, flash an error instead.
    # e.g., flash('An error occurred. Venue ' + data.name + ' could not be listed.')
    # see: http://flask.pocoo.org/docs/1.0/patterns/flashing/
    if error:
      flash('An error occurred. Artist ' + request.form['name'] + ' could not be listed.')
    if not error:
      flash('Artist ' + request.form['name'] + ' was successfully listed!')
    return render_template('pages/home.html')


#  Shows
#  ----------------------------------------------------------------

@app.route('/shows')
def shows():
  # displays list of shows at /shows
  # TODO: replace with real venues data.
  #       num_shows should be aggregated based on number of upcoming shows per venue.
  shows = Show.query.join(Artist).join(Venue).all()
  data=[]
  for show in shows:
      data.append({
          "venue_id": show.venue_id,
          "venue_name":show.venue.name,
          "artist_id": show.artist_id,
          "artist_name": show.artist.name,
          "artist_image_link": show.artist.image_link,
          "start_time": show.start_time.strftime('%Y-%m-%d %H:%M:%S')
      })

  return render_template('pages/shows.html', shows=data)

@app.route('/shows/create')
def create_shows():
  # renders form. do not touch.
  form = ShowForm()
  return render_template('forms/new_show.html', form=form)

@app.route('/shows/create', methods=['POST'])
def create_show_submission():
  # called to create new shows in the db, upon submitting new show listing form
  # TODO: insert form data as a new Show record in the db, instead
  error = False
  try:
    artist_id = request.form['artist_id']
    venue_id = request.form['venue_id']
    start_time = request.form['start_time']
    print(artist_id,venue_id,start_time)
    show = Show(artist_id=artist_id,venue_id=venue_id,start_time=start_time)

    db.session.add(show)
    db.session.commit()
  except:
    error = True
    db.session.rollback()
  finally:
    db.session.close()
    if error:
      flash('An error occurred. Show could not be listed.')
    if not error:
      flash('Show was successfully listed')

  # on successful db insert, flash success

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
    app.run(debug=True)

# Or specify port manually:
'''
if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
'''
