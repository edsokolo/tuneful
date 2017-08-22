import os.path
import json

from flask import request, Response, url_for, send_from_directory
from werkzeug.utils import secure_filename
from jsonschema import validate, ValidationError

from . import models
from . import decorators
from . import app
from .database import session
from .utils import upload_path

post_schema = {
    "properties" : {
        "file" : {
            "type" : "object",
            "required" :["id"],
            "properties" : {
                "id" : {"type:" : "int"}
            }
        }
    },
    "required" :
        ["file"]
}

@app.route("/api/songs", methods=["GET"])
@decorators.accept("application/json")
def songs_get():
    """Get a list of posts """
#    title_like = request.args.get("title_like")
#    body_like = request.args.get("body_like")

    # Get and filter the posts from the database
    songs = session.query(models.Song)
#    if title_like:
    #        posts = posts.filter(models.Post.title.contains(title_like))
    #
    #    if body_like:
    #        posts = posts.filter(models.Post.body.contains(body_like))
    songs = songs.order_by(models.Song.id)

    # Convert the posts to JSON and return a response
    data = json.dumps([song.as_dictionary() for song in songs])
    return Response(data, 200, mimetype="application/json")

@app.route("/api/songs/<int:id>", methods=["GET"])
@decorators.accept("application/json")
def song_get(id):
    """ Single post endpoint """
    # Get the post from the database
    song = session.query(models.Song).get(id)

    # Check whether the post exists
    # If not return a 404 with a helpful message
    if not song:
        message = "Could not find song with id {}".format(id)
        data = json.dumps({"message": message})
        return Response(data, 404, mimetype="application/json")

    # Return the post as JSON
    data = json.dumps(song.as_dictionary())
    return Response(data, 200, mimetype="application/json")

@app.route("/api/songs", methods=["POST"])
def songs_post():
    """ Add a new post """
    data = request.json

    # Check that the JSON supplied is valid
    # If not you return a 422 Unprocessable Entity
    try:
        validate(data, post_schema)
    except ValidationError as error:
        data = {"message": error.message}
        return Response(json.dumps(data), 422, mimetype="application/json")

    # Add the post to the database
    sA = models.Song()
    file_name = data["file"]["name"]
    song = models.File(name=file_name, song=sA)
    session.add(song)
    session.commit()

    # Return a 201 Created, containing the post as JSON and with the
    # Location header set to the location of the post
    data = json.dumps(song.as_dictionary())
    headers = {"Location": url_for("song_get", id=song.id)}
    return Response(data, 201, headers=headers,
                    mimetype="application/json")

@app.route("/api/songs/<int:id>", methods=["DELETE"])
@decorators.accept("application/json")
def post_delete_song(id):
    """ Deletes a post """
    # Delete the post from the database
    song = session.query(models.Song).get(id)
    file = song.file

    # Check whether the song exists
    # If not return a 404 with a helpful message
    if not song:
        message = "Could not find song with id {}".format(id)
        data = json.dumps({"message": message})
        return Response(data, 404, mimetype="application/json")

    # Return the post as JSON
    message = "Song with id {} is deleted".format(id)
    data = json.dumps({"message": message})
    session.delete(file)
    session.delete(song)
    session.commit()
    return Response(data, 200, mimetype="application/json")

@app.route("/api/songs/<int:id>", methods=["PUT"])
@decorators.accept("application/json")
@decorators.require("application/json")
def post_put_song(id):
    """ Single post endpoint """
    song = session.query(models.Song).get(id)
    file = song.file
    data = request.json

    # Check that the JSON supplied is valid
    # If not you return a 422 Unprocessable Entity
    try:
        validate(data, post_schema)
    except ValidationError as error:
        data = {"message": error.message}
        return Response(json.dumps(data), 422, mimetype="application/json")

    # Check whether the post exists
    # If not return a 404 with a helpful message
    if not song:
        message = "Could not find song with id {}".format(id)
        data = json.dumps({"message": message})
        return Response(data, 404, mimetype="application/json")

    # Return the post as JSON
    song.id = data["id"]
    song.file.id = data["file"]["id"]
    song.file.name = data["file"]["name"]
    session.commit()
    return Response(data, 202, mimetype="application/json")