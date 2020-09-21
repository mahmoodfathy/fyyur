from app import db
#----------------------------------------------------------------------------#
# Models.
#----------------------------------------------------------------------------#

class Venue(db.Model):
    __tablename__ = 'Venue'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String)
    city = db.Column(db.String(120))
    state = db.Column(db.String(120))
    address = db.Column(db.String(120))
    phone = db.Column(db.String(120))
    image_link = db.Column(db.String(500))
    genres = db.Column(db.ARRAY(db.String()))
    facebook_link = db.Column(db.String(120))
    seeking_talent = db.Column(db.Boolean,default=False)
    seeking_description = db.Column(db.String(700))
    website = db.Column(db.String(120))
    shows = db.relationship('Show', backref="venue", passive_deletes='all')

    def __repr__(self):
      return '<Venue {}, {} , {}>'.format(self.name,self.city,self.state)

    # TODO: implement any missing fields, as a database migration using Flask-Migrate

class Artist(db.Model):
    __tablename__ = 'Artist'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String)
    city = db.Column(db.String(120))
    state = db.Column(db.String(120))
    phone = db.Column(db.String(120))
    genres = db.Column(db.ARRAY(db.String()))
    image_link = db.Column(db.String(500))
    facebook_link = db.Column(db.String(120))
    seeking_venue = db.Column(db.Boolean, default=False)
    seeking_description = db.Column(db.String(700))
    website = db.Column(db.String(120))
    shows = db.relationship('Show', backref="artist", passive_deletes='all')

    def __repr__(self):
      return '<Artist {}, {}>'.format(self.name,self.city)

    # TODO: implement any missing fields, as a database migration using Flask-Migrate

# TODO Implement Show and Artist models, and complete all model relationships and properties, as a database migration.
class Show(db.Model):
  __tablename__='Show'
  id = db.Column(db.Integer,primary_key=True)
  artist_id = db.Column(db.Integer,db.ForeignKey('Artist.id',ondelete='CASCADE'),nullable=False)
  venue_id = db.Column(db.Integer,db.ForeignKey('Venue.id',ondelete='CASCADE'),nullable=False)
  start_time = db.Column(db.DateTime,nullable=False)

  def __repr__(self):
    return '<Show {}{}>'.format(self.artist_id, self.venue_id)