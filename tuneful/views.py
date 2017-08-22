from flask import render_template

from . import app
from . import models
from .database import session

@app.route("/", methods=["GET"])
def names():
    songs = session.query(models.Song).all()
    files = []
    for song in songs:
        files.append(song.file)
    return render_template("index.html",
                           files=files)