from flask_sqlalchemy import SQLAlchemy
from flask import Flask, render_template, request, Response, flash, redirect, url_for
from flask_moment import Moment


db = SQLAlchemy()


class Venue(db.Model):
		__tablename__ = 'Venue'

		id = db.Column(db.Integer, primary_key=True)
		name = db.Column(db.String(), nullable = False)
		city = db.Column(db.String(120), nullable = False)
		state = db.Column(db.String(120), nullable = False)
		address = db.Column(db.String(120), nullable = False)
		phone = db.Column(db.String(120))
		genres = db.Column(db.String(300), nullable = False)
		image_link = db.Column(db.String(500))
		facebook_link = db.Column(db.String(120))
		website_link = db.Column(db.String(500))
		seeking_talent = db.Column(db.Boolean, default = False)
		seeking_description = db.Column(db.String())

		show = db.relationship("Show", backref = "venue", lazy = True)

		def __repr__(self):
			return f'\n<Venue: {self.id}, name: {self.name}, city: {self.city}, state: {self.state}, address: {self.address}, phone: {self.phone}, image_link: {self.image_link}, facebook_link: {self.facebook_link}, genres: {self.genres}, website: {self.website_link}, shows: {self.show}> \n\n\n\n'


class Artist(db.Model):
		__tablename__ = 'Artist'

		id = db.Column(db.Integer, primary_key=True)
		name = db.Column(db.String(), nullable = False)
		city = db.Column(db.String(120), nullable = False)
		state = db.Column(db.String(120), nullable = False)
		phone = db.Column(db.String(120))
		genres = db.Column(db.String(300), nullable = False)
		image_link = db.Column(db.String(500))
		facebook_link = db.Column(db.String(120))
		website_link = db.Column(db.String(500))
		seeking_venues = db.Column(db.Boolean, default = False)
		seeking_description = db.Column(db.String())

		show = db.relationship("Show", backref = "artist", lazy = True)

		def __repr__(self):
			return f'<Artist: {self.id}, name: {self.name}, city: {self.city}, state: {self.state}, phone: {self.phone}, genres: {self.genres}, image_link: {self.image_link}, facebook_link: {self.facebook_link}, shows: {self.show}> \n\n\n'


class Show(db.Model):
	__tablename__ = "Show"
	id = db.Column(db.Integer, primary_key = True)
	artist_id = db.Column(db.Integer, db.ForeignKey('Artist.id'), nullable = False)
	venue_id = db.Column(db.Integer, db.ForeignKey('Venue.id'), nullable = False)
	date = db.Column(db.DateTime, nullable = False)

