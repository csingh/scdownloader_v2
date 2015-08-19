import config
from helpers import *
import soundcloud
from track import Track

import logging
import traceback

import argparse
import os

import mutagen
from mutagen.id3 import ID3, APIC, USLT

def print_and_log_info(message):
    print(message)
    logging.info(message)

def print_and_log_debug(message):
    print(message)
    logging.debug(message)

def print_and_log_error(message):
    print(message)
    logging.error(message)

def get_playlist_tracks(playlist_url, num_tracks=50, offset=0):
    logging.debug("Processing playlist at %s." % playlist_url)
    
    r = client.get('/resolve', url=username_or_url)
    get_url = "playlists/" + str(r.id)
    logging.debug("Playlist ID: %s." % str(r.id))
    
    pl = client.get(get_url, limit=num_tracks, offset=offset)
    tracks = pl.tracks
    tracks = [Track(x) for x in tracks]

    logging.debug("Got %s tracks." % str(len(tracks)))

    return tracks

def get_favorite_tracks(username, num_tracks=50, offset=0):
    logging.debug("Processing favorites for user %s." % username)

    get_url = 'users/%s/favorites' % str(username)
    tracks = client.get(get_url, limit=num_tracks, offset=offset)
    tracks = [Track(x) for x in tracks]

    logging.debug("Got %s tracks." % str(len(tracks)))

    return tracks

def edit_id3_tags(track, mp3_path, img_path):
    # Edit Artist/Title ID3 tags
    # http://stackoverflow.com/questions/18369188/python-add-id3-tags-to-mp3-file-that-has-no-tags
    logging.debug("Adding artist/title ID3 tags...")
    meta = mutagen.File(mp3_path, easy=True)
    meta["title"] = track.title
    meta["artist"] = track.username
    meta.save()

    # Embed description into lyrics field
    if track.description is not None:
        logging.debug("Writing description to lyrics field...")
        audio = ID3(mp3_path)
        audio.add(USLT(encoding=3, lang=u'eng', desc=u'desc', text=track.description))
        audio.save()

    # Embed album art
    if track.artwork_url is not None:
        logging.debug("Adding album art...")
        audio = ID3(mp3_path)
        audio.add(
            APIC(
                encoding=3, # 3 is for utf-8
                mime='image/jpeg', # image/jpeg or image/png
                type=3, # 3 is for the cover image
                desc='Cover',
                data=open(img_path, "rb").read()
            )
        )
        audio.save()

# this method is used to make repeated calls to soundcloud api
# in order to retrieve the number of tracks specified
# since the soundcloud api doesn't always use the 'limit' argument
# properly (ie. give it 50, and it sometimes returns 49 tracks), we
# have to manualyl keep track of how many items were returned, in
# order to know the next call's offset value
def get_tracks(username_or_url, get_tracks_method, num_tracks):
    all_tracks = []
    num_tracks_retrieved = 0
    num_tracks_left = num_tracks
    offset = 0
    max_limit = 100

    while (num_tracks_retrieved < num_tracks):
        # calculate how many tracks to retreive
        num_tracks_left = num_tracks - num_tracks_retrieved
        limit = max_limit if (num_tracks_left > max_limit) else num_tracks_left

        logging.debug("Retreiving tracks %(start)s - %(end)s of %(total)s" %
            {
                "start" : offset+1,
                "end" : offset+limit,
                "total" : num_tracks
            })

        # get the tracks
        tracks = get_tracks_method(username_or_url, limit, offset)

        if len(tracks) == 0:
            break

        # update vars
        offset += len(tracks)
        num_tracks_retrieved += len(tracks)

        # append to all_tracks
        all_tracks = all_tracks + tracks

    return all_tracks

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
        parser.add_argument("--num_tracks", help="Number of tracks to process (default %s)" % config.num_tracks, type=int)
        parser.add_argument("--dry_run", help="Display tracks but don't download", action="store_true")
        parser.add_argument("--mp3s_dir", help="Path for image downloads (default: %s)" % config.mp3s_dir)
        parser.add_argument("--images_dir", help="Path for image downloads (default: %s)" % config.images_dir)
        parser.add_argument("--dl_data", help="Path for download data JSON file (default: %s)" % config.dl_data_filename)
        args = parser.parse_args()

        username_or_url = args.username_or_url
        num_tracks = args.num_tracks or config.num_tracks
        dry_run = args.dry_run
        images_dir = args.images_dir or config.images_dir
        mp3s_dir = args.mp3s_dir or config.mp3s_dir
        dl_data_filename = args.dl_data or config.dl_data_filename

        logging.debug("username/url: %s" % username_or_url)
        logging.debug("num_tracks: %s" % num_tracks)
        logging.debug("dry_run: %s" % dry_run)
        logging.debug("mp3s_dir: %s" % mp3s_dir)
        logging.debug("images_dir: %s" % images_dir)
        logging.debug("dl_data: %s" % dl_data_filename)

        # create download and images directory
        if not os.path.exists(mp3s_dir):
            os.makedirs(mp3s_dir)
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

        # check if arg is username or playlist url
        # pick appropriate function to use later
        if username_or_url.find("/sets/") != -1:
            # process playlist/set
            tracks = get_tracks(username_or_url, get_playlist_tracks, num_tracks)
        else:
            # process user favs
            tracks = get_tracks(username_or_url, get_favorite_tracks, num_tracks)

        # iterate through and download tracks
        count = 0
        for t in tracks:
            try:
                count += 1
                info = {
                    "count" : count,
                    "total" : len(tracks),
                    "username" : t.username,
                    "title" : t.title
                }
                print_and_log_info("Processing %(count)s of %(total)s: %(username)s - %(title)s" % info)

                logging.debug(t)

                # get file paths
                mp3_path = os.path.join(mp3s_dir, t.filename + ".mp3")
                img_path = os.path.join(images_dir, t.filename + ".jpg")

                logging.debug("mp3_path: %s" % mp3_path)
                logging.debug("img_path: %s" % img_path)

                # TODO: skip track if already downloaded

                if not dry_run:
                    dl_link = t.get_download_link(config.client_id)

                    if dl_link is None:
                        print_and_log_info("Download link not available, skipping track.")
                        continue

                    logging.debug("dl_link: %s" % dl_link)

                    # download mp3 from link
                    download_file(dl_link, mp3_path)

                    # download album art
                    if t.artwork_url is not None:
                        download_file(t.artwork_url, img_path)

                    # only edit id3 tags if low quality (untagged) mp3 downloaded
                    # basically only if stream_url was provided and
                    # download_url was not
                    if t.download_url is None:
                        edit_id3_tags(t, mp3_path, img_path)
                    else:
                        logging.debug("HQ MP3 downloaded, skipping id3 editing")

                    # TODO: save to var for JSON

            except Exception as ex:
                print_and_log_error("Skipped track %s due to error:" % t.permalink)
                print_and_log_error(ex)
                logging.error(traceback.format_exc())

    except Exception as ex:
        print(ex)
        print("\n\nERROR:\n\n");
        print(traceback.format_exc())
        logging.critical(traceback.format_exc())
    finally:
        # TODO: save JSON
        print_and_log_info("Done.")
