Take your SoundCloud favourites offline!
===

#What
A Python script to download your SoundCloud favourites or playlists (with artist/title/image info embedded in ID3Tags)

#Pre-requisites:
* python 3 (tested with 3.4.2)
* mutagen for python
* soundcloud-python api

#Pre-req Install Instructions:
* Install [Python 3](https://www.python.org/downloads/)
* Install [pip](https://pip.pypa.io/en/latest/installing.html)
* Install [mutagen](https://bitbucket.org/lazka/mutagen) (run 'pip3 install mutagen')
* Install [soundcloud-python](https://github.com/soundcloud/soundcloud-python) (run 'pip3 install soundcloud')

#Finally
* run `python3 download_things.py -h` to see usage details

#Example Usage
get **csingh91**'s **likes**, but **don't download**:
>`python3 download_things.py http://soundcloud.com/csingh91/ --dry_run`

download **csingh91**'s **likes**:
>`python3 download_things.py http://soundcloud.com/csingh91/`

download **csingh91**'s **'mixes' playlist**:
>`python3 download_things.py http://soundcloud.com/csingh91/sets/mixes`

download **all playlists** from **csingh91**:
>`python3 download_things.py http://soundcloud.com/csingh91/sets/`

#Notes
* script will only process 50 songs by default. Use --num_songs argument to override this
* script will keep track of downloaded files, and skip them on next run (data saved to "dl_data.json" by default)
