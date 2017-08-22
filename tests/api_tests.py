import unittest
import os
import shutil
import json
try: from urllib.parse import urlparse
except ImportError: from urlparse import urlparse # Py2 compatibility
from io import StringIO

import sys; print(list(sys.modules.keys()))
# Configure our app to use the testing databse
os.environ["CONFIG_PATH"] = "tuneful.config.TestingConfig"

from tuneful import app
from tuneful import models
from tuneful.utils import upload_path
from tuneful.database import Base, engine, session

class TestAPI(unittest.TestCase):
    """ Tests for the tuneful API """

    def setUp(self):
        """ Test setup """
        self.client = app.test_client()

        # Set up the tables in the database
        Base.metadata.create_all(engine)

        # Create folder for test uploads
        os.mkdir(upload_path())

    def test_unsupported_accept_header(self):
        response = self.client.get("/api/songs",
            headers=[("Accept", "application/xml")]
        )

        self.assertEqual(response.mimetype, "application/json")
        self.assertEqual(response.status_code, 406)

        data = json.loads(response.data.decode("ascii"))
        self.assertEqual(data["message"],
                         "Request must accept application/json data")

    def test_get_songs(self):
        sA = models.Song()
        sB = models.Song()
        songA = models.File(name="Song A")
        songB = models.File(name="Song B")
        songA.song = sA
        songB.song = sB
        session.add_all([songA, songB])
        session.commit()

        response = self.client.get("/api/songs",
                headers=[("Accept", "application/json")])

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.mimetype, "application/json")

        data = json.loads(response.data.decode("ascii"))
        self.assertEqual(len(data), 2)

        songA = data[0]
        sA = songA["file"]
        self.assertEqual(sA["file_name"], "Song A")
        self.assertEqual(sA["file_id"], 1)

        songB = data[1]
        sB = songB["file"]
        self.assertEqual(sB["file_name"], "Song B")
        self.assertEqual(sB["file_id"], 2)

    def test_get_song(self):
        sA = models.Song()
        sB = models.Song()
        songA = models.File(name="Song A")
        songB = models.File(name="Song B")
        songA.song = sA
        songB.song = sB
        session.add_all([songA, songB])
        session.commit()

        response = self.client.get("/api/songs/{}".format(songA.song_id),
                                   headers=[("Accept", "application/json")])

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.mimetype, "application/json")

        data = json.loads(response.data.decode("ascii"))

        songA = data
        sA = songA["file"]
        self.assertEqual(sA["file_name"], "Song A")
        self.assertEqual(sA["file_id"], 1)

    def test_post_song(self):
        """ Posting a new post """
        data = {
            "id": 1,
            "file": {
                "id": 1,
                "name": "SongA"
            }
        }

        response = self.client.post("/api/songs",
            data=json.dumps(data),
            content_type="application/json",
            headers=[("Accept", "application/json")]
            )

        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.mimetype, "application/json")
        self.assertEqual(urlparse(response.headers.get("Location")).path,
                         "/api/songs/1")

        data = json.loads(response.data.decode("ascii"))
        self.assertEqual(data["id"], 1)
        self.assertEqual(data["name"], "SongA")

        songs = session.query(models.Song).all()
        self.assertEqual(len(songs), 1)
        song = songs[0]
        file = song.file
        self.assertEqual(file.name, "SongA")
        self.assertEqual(file.id, 1)

    def test_delete(self):
        sA = models.Song()
        sB = models.Song()
        songA = models.File(name="Song A")
        songB = models.File(name="Song B")
        songA.song = sA
        songB.song = sB
        session.add_all([songA, songB])
        session.commit()

        response = self.client.get("/api/songs/{}".format(songA.song_id),
                                   headers=[("Accept", "application/json")])

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.mimetype, "application/json")

        data = json.loads(response.data.decode("ascii"))

        songA = data
        sA = songA["file"]
        self.assertEqual(sA["file_name"], "Song A")
        self.assertEqual(sA["file_id"], 1)

        response = self.client.delete("/api/songs/{}".format(sA["file_id"]),
            headers=[("Accept", "application/json")])

        response = self.client.get("/api/songs/{}".format(sA["file_id"]),
            headers=[("Accept", "application/json")])

        self.assertEqual(response.status_code, 404)
        self.assertEqual(response.mimetype, "application/json")

        data = json.loads(response.data.decode("ascii"))
        self.assertEqual(data["message"], "Could not find song with id 1")


    def test_post_put(self):
        """ Editing a post """
        data = {
            "id": 1,
            "file": {
                "id": 1,
                "name": "SongA"
            }
        }

        response = self.client.post("/api/songs",
            data=json.dumps(data),
            content_type="application/json",
            headers=[("Accept", "application/json")]
            )

        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.mimetype, "application/json")
        self.assertEqual(urlparse(response.headers.get("Location")).path,
                         "/api/songs/1")

        response = self.client.get("/api/songs",
                headers=[("Accept", "application/json")])

        data = json.loads(response.data.decode("ascii"))
        song = data[0]
        self.assertEqual(song["id"], 1)
        self.assertEqual(song["file"]["file_id"], 1)
        self.assertEqual(song["file"]["file_name"], "SongA")

        songs = session.query(models.Song).all()
        self.assertEqual(len(songs), 1)

        song = songs[0]
        self.assertEqual(song.id, 1)
        self.assertEqual(song.file.name, "SongA")

        data = {
            "id": 1,
            "file": {
                "id": 1,
                "name": "SongA remix"
            }
        }

        response = self.client.put("/api/songs/1",
                        data=json.dumps(data),
                        content_type="application/json",
                        headers=[("Accept", "application/json")]
                        )
        self.assertEqual(response.status_code, 202)
        self.assertEqual(response.mimetype, "application/json")

        response = self.client.get("/api/songs/1",
            headers=[("Accept", "application/json")])

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.mimetype, "application/json")

        data = json.loads(response.data.decode("ascii"))

        song = data
        file = song["file"]
        self.assertEqual(song["id"], 1)
        self.assertEqual(file["file_name"], "SongA remix")


    def tearDown(self):
        """ Test teardown """
        session.close()
        # Remove the tables and their data from the database
        Base.metadata.drop_all(engine)

        # Delete test upload folder
        shutil.rmtree(upload_path())


if __name__ == "__main__":
    unittest.main()