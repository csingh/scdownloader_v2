from helpers import *
import soundcloud
from track import Track

import logging
import traceback

import argparse
import os
import sys

import mutagen
from mutagen.id3 import ID3, APIC, USLT

default_client_id = "9f37d30eaf2f7205b29d1e7409f8e4a7"
default_num_tracks = 50
default_mp3s_dir = "downloads"
default_dl_data_filename = "dl_data.json"

def print_and_log_info(message):
    print(message)
    logging.info(message)

def print_and_log_debug(message):
    print(message)
    logging.debug(message)

def print_and_log_error(message):
    print(message)
    logging.error(message)

def print_and_log_critical(message):
    print(message)
    logging.critical(message)

def get_playlist_tracks(playlist_url, num_tracks=50, offset=0):
    r = client.get('/resolve', url=playlist_url)
    get_url = "playlists/%s" % r.id
    pl = client.get(get_url, limit=num_tracks, offset=offset)    
    tracks = [Track(x) for x in pl.tracks]

    return tracks

def get_favorite_tracks(favs_url, num_tracks=50, offset=0):
    r = client.get('/resolve', url=favs_url)
    get_url = "users/%s/favorites" % r.id
    likes = client.get(get_url, limit=num_tracks, offset=offset)
    tracks = [Track(x) for x in likes]

    return tracks

# this method is used to make repeated calls to soundcloud api
# in order to retrieve the number of tracks specified
# since the soundcloud api doesn't always use the 'limit' argument
# properly (ie. give it 50, and it sometimes returns 49 tracks), we
# have to manualyl keep track of how many items were returned, in
# order to know the next call's offset value
def get_tracks(parse_url, method, num_tracks):
    all_tracks = []
    num_tracks_retrieved = 0
    num_tracks_left = num_tracks
    offset = 0
    max_limit = 100

    if method == 'favs':
        get_tracks_method = get_favorite_tracks
    elif method == 'playlist':
        get_tracks_method = get_playlist_tracks

    logging.debug("Retreiving tracks from %s." % parse_url)

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
        tracks = get_tracks_method(parse_url, limit, offset)

        logging.debug("Got %s tracks." % str(len(tracks)))

        if len(tracks) == 0:
            break

        # update vars
        offset += len(tracks)
        num_tracks_retrieved += len(tracks)

        # append to all_tracks
        all_tracks = all_tracks + tracks

    # if retrieving favs, then reverse the tracks order so we process from
    # oldest to newest don't need to do this for playlists since the newest
    # additions are at the bottom by default
    if method == 'favs':
        all_tracks.reverse()

    return all_tracks

# given an mp3 path, fill id3 tags using info from track, and album art
# from img_path
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

def download_track_and_edit_tags(dl_link, track, mp3_path, img_path):
    try:
        # download mp3 from link
        download_file(dl_link, mp3_path)

        # download album art
        if track.artwork_url is not None:
            download_file(track.artwork_url, img_path)

        # only edit id3 tags if low quality (untagged) mp3 downloaded
        # basically only if stream_url was provided and
        # download_url was not
        if track.download_url is None:
            edit_id3_tags(track, mp3_path, img_path)
        else:
            logging.debug("HQ MP3 downloaded, skipping id3 editing")

        return True
    except Exception as ex:
        print_and_log_error("Skipped track %s due to error:" % track.permalink)
        print_and_log_error(ex)
        logging.error(traceback.format_exc())
        return False

def download_the_things(tracks, num_tracks, dry_run, mp3s_dir, dl_data_filename):
    # create download and images directory
    create_dir_if_doesnt_exist(mp3s_dir)
    imgs_dir = os.path.join(mp3s_dir, "images")
    create_dir_if_doesnt_exist(imgs_dir)

    # open previous download data json
    logging.debug("Loading previously downloaded tracks from database...")
    saved_data = load_json_data(dl_data_filename)
    if saved_data is None:
        logging.debug("Could not load %s, continuing..." % dl_data_filename)
        saved_data = {}

    # iterate through and download tracks
    count = 0
    for t in tracks:
        count += 1
        info = {
            "count" : count,
            "total" : len(tracks),
            "username" : t.username,
            "title" : t.title
        }
        print_and_log_info("Processing %(count)s of %(total)s: %(username)s - %(title)s" % info)

        logging.debug(str(t))

        # get file paths
        mp3_path = os.path.join(mp3s_dir, t.filename + ".mp3")
        img_path = os.path.join(imgs_dir, t.filename + ".jpg")

        logging.debug("mp3_path: %s" % mp3_path)
        logging.debug("img_path: %s" % img_path)

        # skip track if already downloaded
        if t.permalink in saved_data:
            print_and_log_info("Track already downloaded, skipping...")
            continue

        # if not dry_run then download track
        if not dry_run:
            dl_link = t.get_download_link(default_client_id)
            if dl_link is None:
                print_and_log_info("Download link not available, skipping track.")
                continue

            logging.debug("dl_link: %s" % dl_link)

            if download_track_and_edit_tags(dl_link, t, mp3_path, img_path):
                # if download success, add to saved_data so we
                # can later write to JSON file
                saved_data[t.permalink] = t.to_dict()

    # save JSON
    if not dry_run:
        save_json_data(saved_data, dl_data_filename)

def parse_url_and_get_tracks(parse_url, num_tracks):
    parse_url = parse_url.strip()

    # list of playlists
    if parse_url[-5:] == 'sets/':
        print_and_log_info("Processing all sets from %s." % parse_url)

        playlists = client.get('/resolve', url=parse_url)

        for p in playlists:
            print_and_log_info("Processing tracks from playlist %s" % p.permalink)
            tracks = get_tracks(p.uri, 'playlist', num_tracks)

            username = p.user["permalink"]
            pl_name = p.permalink

            new_mp3s_dir = os.path.join(mp3s_dir, username, pl_name)
            new_dl_data_filename = os.path.join(mp3s_dir, username, pl_name, dl_data_filename)

            download_the_things(tracks, num_tracks, dry_run, new_mp3s_dir, new_dl_data_filename)

    # single playlist
    elif parse_url.find('/sets') != -1:
        r = client.get('/resolve', url=parse_url)

        username = r.user["permalink"]
        pl_name = r.permalink

        new_mp3s_dir = os.path.join(mp3s_dir, username, pl_name)
        new_dl_data_filename = os.path.join(mp3s_dir, username, pl_name, dl_data_filename)

        print_and_log_info("Processing tracks from playlist %s." % r.permalink)
        tracks = get_tracks(parse_url, 'playlist', num_tracks)
        download_the_things(tracks, num_tracks, dry_run, new_mp3s_dir, new_dl_data_filename)
    # user likes
    else:
        r = client.get('/resolve', url=parse_url)

        username = r.permalink
        likes_folder = '!_likes'

        new_mp3s_dir = os.path.join(mp3s_dir, username, likes_folder)
        new_dl_data_filename = os.path.join(mp3s_dir, username, likes_folder, dl_data_filename)

        print_and_log_info("Processing likes from %s." % r.permalink)
        tracks = get_tracks(parse_url, 'favs', num_tracks)
        download_the_things(tracks, num_tracks, dry_run, new_mp3s_dir, new_dl_data_filename)

#-------------------------------------------------------------------------------

if __name__ == '__main__':
    # logger config
    logging.basicConfig(
        filename='scdownloader.log',
        format='%(asctime)s | %(levelname)s | %(module)s | %(message)s',
        datefmt='%m/%d/%Y %I:%M:%S %p',
        level=logging.DEBUG
    )

    # parse command line args
    parser = argparse.ArgumentParser()
    parser.add_argument("parse_url", help="SoundCloud URL for user's likes, user's playlists, or specific playlist")
    parser.add_argument("--num_songs", help="Number of tracks to process (default %s)" % default_num_tracks, type=int)
    parser.add_argument("--dry_run", help="Display tracks but don't download", action="store_true")
    parser.add_argument("--mp3_path", help="Path for mp3 downloads (default: %s)" % default_mp3s_dir)
    parser.add_argument("--dl_data", help="Path for download data JSON file (default: %s)" % default_dl_data_filename)
    args = parser.parse_args()

    parse_url = args.parse_url
    num_tracks = args.num_songs or default_num_tracks
    dry_run = args.dry_run
    mp3s_dir = args.mp3_path or default_mp3s_dir
    dl_data_filename = args.dl_data or default_dl_data_filename

    logging.debug("parse_url: %s" % parse_url)
    logging.debug("num_tracks: %s" % num_tracks)
    logging.debug("dry_run: %s" % dry_run)
    logging.debug("mp3s_dir: %s" % mp3s_dir)
    logging.debug("dl_data: %s" % dl_data_filename)

    # create SoundCloud client
    logging.debug("client_id: %s", default_client_id)
    client = soundcloud.Client(client_id=default_client_id)

    # check URL to see if its for list of playlists. If it is, process each playlist. If not
    # pass URL through to download_the_things
    try:
        # parse url and get tracks
        parse_url_and_get_tracks(parse_url, num_tracks)
    except requests.exceptions.HTTPError:
        print_and_log_critical("Error while resolving SoundCloud URL, verify that it's valid.")
        logging.critical(traceback.format_exc())
    except:
        print_and_log_critical("ERROR:")
        print_and_log_critical(traceback.format_exc())

    print_and_log_info("Done.")
