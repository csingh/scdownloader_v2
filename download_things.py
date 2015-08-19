import config
from helpers import *
import soundcloud
from track import Track

import logging
import traceback

import argparse
import os

def print_and_log_info(message):
    print(message)
    logging.info(message)

def get_playlist_tracks(playlist_url, num_songs=50, offset=0):
    logging.debug("Processing playlist at %s." % playlist_url)
    
    r = client.get('/resolve', url=username_or_url)
    get_url = "playlists/" + str(r.id)
    logging.debug("Playlist ID: %s." % str(r.id))
    
    pl = client.get(get_url, limit=num_songs, offset=offset)
    tracks = pl.tracks
    tracks = [Track(x) for x in tracks]

    logging.debug("Got %s tracks." % str(len(tracks)))

    return tracks

def get_favorite_tracks(username, num_songs=50, offset=0):
    logging.debug("Processing favorites for user %s." % username)

    get_url = 'users/%s/favorites' % str(username)
    tracks = client.get(get_url, limit=num_songs, offset=offset)
    tracks = [Track(x) for x in tracks]
    tracks.reverse() # process old to new

    logging.debug("Got %s tracks." % str(len(tracks)))

    return tracks

if __name__ == '__main__':
    try:
        # logger config
        logging.basicConfig(
            filename='scdownloader.log',
            format='%(asctime)s | %(levelname)s | %(module)s | %(message)s',
            datefmt='%m/%d/%Y %I:%M:%S %p',
            level=logging.DEBUG
        )

        # parse command line args
        parser = argparse.ArgumentParser()
        parser.add_argument("username_or_url", help="SoundCloud username, or URL to a SoundCloud playlist")
        parser.add_argument("--num_songs", help="Number of tracks to process (default %s)" % config.num_songs, type=int)
        parser.add_argument("--dry_run", help="Display tracks but don't download", action="store_true")
        parser.add_argument("--mp3_path", help="Path for image downloads (default: %s)" % config.downloads_dir)
        parser.add_argument("--img_path", help="Path for image downloads (default: %s)" % config.images_dir)
        parser.add_argument("--dl_data", help="Path for download data JSON file (default: %s)" % config.dl_data_filename)
        args = parser.parse_args()

        username_or_url = args.username_or_url
        num_songs = args.num_songs or config.num_songs
        dry_run = args.dry_run
        images_dir = args.img_path or config.images_dir
        downloads_dir = args.mp3_path or config.downloads_dir
        dl_data_filename = args.dl_data or config.dl_data_filename

        logging.debug("username/url: %s" % username_or_url)
        logging.debug("num_songs: %s" % num_songs)
        logging.debug("dry_run: %s" % dry_run)
        logging.debug("mp3_path: %s" % downloads_dir)
        logging.debug("img_path: %s" % images_dir)
        logging.debug("dl_data: %s" % dl_data_filename)

        # create download and images directory
        if not os.path.exists(downloads_dir):
            os.makedirs(downloads_dir)
        if not os.path.exists(images_dir):
            os.makedirs(images_dir)

        # open previous download data json
        saved_data = load_json_data(dl_data_filename)
        if saved_data is None:
            logging.debug("Could not load %s, continuing..." % dl_data_filename)
            saved_data = []

        # create SoundCloud client
        logging.debug("client_id: %s", config.client_id)
        client = soundcloud.Client(client_id=config.client_id)

        tracks = []

        # check if arg is username or set url
        if username_or_url.find("/sets/") != -1:
            # process playlist/set
            tracks = get_playlist_tracks(username_or_url)
        else:
            # process user favs
            tracks = get_favorite_tracks(username_or_url)

        count = 0
        for track in tracks:
            count += 1
            info = {
                "count" : count,
                "total" : len(tracks),
                "username" : track.username,
                "title" : track.title
            }
            print_and_log_info("%(count)s of %(total)s: %(username)s - %(title)s" % info)

    except Exception as ex:
        print(ex)
        print("\n\nERROR:\n\n");
        print(traceback.format_exc())
        logging.critical(traceback.format_exc())
    finally:
        print("\nDone.")
