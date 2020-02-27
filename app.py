###############################################################################################
# This script creates a Flask app that provides web routes to API information
# generated from the analysis of Hawaii's sqlite weather database in the sql_alchemy.ipynb file
###############################################################################################

###### GETTING STARTED #################

# importing flask and dependencies
import numpy as np
import sqlalchemy
from sqlalchemy.ext.automap import automap_base
from sqlalchemy.orm import Session
from sqlalchemy import create_engine, func
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import datetime as dt
from datetime import timedelta
from itertools import chain
from flask import Flask, jsonify

# creating the app
app = Flask(__name__)

#################################################
# Database Setup
#################################################

# defining sqlite database path
db_path = "resources/hawaii.sqlite"

# creating engine
engine = create_engine(f"sqlite:///{db_path}")

# reflect an existing database into a new model
base = automap_base()

# reflect the tables
classes = base.prepare(engine, reflect=True)

# Save references to each table
Measurement = base.classes.measurement
Station = base.classes.station

#######################################
######## DEFINING ROUTES ##############
#######################################

######## home page route #############
@app.route("/")
def home():
    
    print("The server received a request for the 'Home' page...")
    
    return (
        f"Micah's Hawaii Weather API: 2010-01-01 to 2017-08-23 <br/><br/>"
        f"Available Routes:<br/>"
        f"For precipitation info:<br/>"
        f"/api/v1.0/precipitation<br/><br/>"
        f"For station info:<br/>"
        f"/api/v1.0/stations<br/><br/>"
        f"For temperature info a year back from last date recorded:<br/>"
        f"/api/v1.0/tobs<br/><br/>"
        f"Type in a start date within range in format YYYY-MM-DD to see min, max, and avg temps from that date forward(without single quotes)<br/>"
        f"Your correctly formatted date will replace 'yourstart' in the following url<br/>"
        f"/api/v1.0/yourstart<br/><br/>"
        f"Type start and end date similarly in place of 'yourstart' and 'yourend' to see the aforementioned stats within that range.<br/>"
        f"/api/v1.0/yourstart/yourend"
    )

###### precipitation route ###########
@app.route("/api/v1.0/precipitation")    
def prcp():
    
    print("The server received a request for the 'Precipitation' page...")
    
    # Create our session (link) from Python to the DB
    session = Session(engine)
    
    # getting latest date
    # ordering dates by descending, selecting the first
    last_date_recorded = session.query(Measurement.date).order_by(Measurement.date.desc()).first()
    
    # value stays the same; changing variable from query result to a string
    # to split it in the next step
    last_date_recorded = last_date_recorded[0]

    # getting year, month, and day of last day recorded in the correct format
    # for the datetime object
    year, month, day = map(int, last_date_recorded.split("-"))
    
    # query to get precipitation data
    # getting one year from the last date recorded
    year_from_last_date = dt.datetime(year, month, day) - dt.timedelta(days = 365)

    # query for date and precipitation data for all days on and after 'year_from_last_date'
    prcp_query = session.query(Measurement.date, Measurement.prcp).\
                    filter(Measurement.date >= year_from_last_date).\
                    all()
    
    session.close()
    
    prcp_data = []
    
    # creating dictionary for precipitation data
    for date, prcp in prcp_query:
        prcp_dict = {}
        prcp_dict["date"] = date
        prcp_dict["prcp"] = prcp
        prcp_data.append(prcp_dict)
        
    return jsonify(prcp_data)
    
########### stations route ###############
@app.route("/api/v1.0/stations")
def stations():
    print("The server received a request for the 'Stations' page...")
    
    # create session
    session = Session(engine)
    
    # query to get stations
    station_query = session.query(Station.id, Station.station, Station.name, Station.latitude, Station.longitude, Station.elevation).all()
    
    # close session
    session.close()
    
    # Create dict of all station data and jsonify 
    stations_full = []
    
    for id, station, name, latitude, longitude, elevation in station_query:
        stations_dict = {}
        stations_dict["id"] = id
        stations_dict["station"] = station
        stations_dict["name"] = name
        stations_dict["lat"] = latitude
        stations_dict["lng"] = longitude
        stations_dict["elevation"] = elevation
        stations_full.append(stations_dict)
    
    # returning all stations jsonified
    return jsonify(stations_full)

########## observed temperature route #############
@app.route("/api/v1.0/tobs")
def tobs():
    print("The server received a request for the 'Temperature' page...")
    
    # create session
    session = Session(engine)
    
        
    # getting latest date
    # ordering dates by descending, selecting the first
    last_date_recorded = session.query(Measurement.date).order_by(Measurement.date.desc()).first()
    
    # value stays the same; changing variable from query result to a string
    # to split it in the next step
    last_date_recorded = last_date_recorded[0]

    # getting year, month, and day of last day recorded in the correct format
    # for the datetime object
    year, month, day = map(int, last_date_recorded.split("-"))

    # getting one year from the last date recorded
    year_from_last_date = dt.datetime(year, month, day) - dt.timedelta(days = 365)

    # query for date and tobs data for all days on and after 'year_from_last_date'
    temp_query = session.query(Measurement.date, Measurement.tobs).\
                filter(Measurement.date >= year_from_last_date).\
                all()
    
    session.close()
    
    tobs_data = []
    
    # creating dictionary for precipitation data
    for date, tobs in temp_query:
        tobs_dict = {}
        tobs_dict["date"] = date
        tobs_dict["tobs"] = tobs
        tobs_data.append(tobs_dict)
        
    return jsonify(tobs_data)
           
####### start date route ###################
@app.route("/api/v1.0/<start>")

def start_date(start):
    
    session = Session(engine)
    
    # calculates TMIN, TAVG, and TMAX for all dates greater than and equal to the start date provided.
    start_query = session.query(func.min(Measurement.tobs), func.avg(Measurement.tobs),func.max(Measurement.tobs)).\
                filter(Measurement.date >= start).\
                all()
    
    # getting results of query in dictionary and jsonifying
    start_temps = []
    
    for tmin, tavg, tmax in start_query:
        start_dict = {}
        start_dict["min"] = tmin
        start_dict["avg"] = tavg
        start_dict["max"] = tmax
        start_temps.append(start_dict)
        
    # returning jsonified results
    return jsonify(start_temps)

######### end date route #################
@app.route("/api/v1.0/<start>/<end>")
def start_end(start, end):
    
    # creating session 
    session = Session(engine)
    
    # calculates the TMIN, TAVG, and TMAX for dates between the start and end date inclusive.
    start_end_query = session.query(func.min(Measurement.tobs), func.avg(Measurement.tobs), func.max(Measurement.tobs)).\
                    filter(Measurement.date >= start).\
                    filter(Measurement.date <= end).\
                    all()
    
    # closing session
    session.close()
    
    # creating dictionary for start_end_query data and return json response
    start_end_data = []
    
    for tmin, tavg, tmax in start_end_query:
        start_end_dict = {}
        start_end_dict["min"] = tmin
        start_end_dict["avg"] = tavg
        start_end_dict["max"] = tmax
        start_end_data.append(start_end_dict)
    
    # returning jsonified response
    return jsonify(start_end_data)

if __name__ == "__main__":
    app.run(debug=True)




