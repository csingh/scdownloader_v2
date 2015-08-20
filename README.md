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
* run 'python3 download_things.py -h' to see usage details
* Example usage (user likes): 'python3 download_things.py csingh91' to download csingh91's liked tracks
* Example usage (playlist/set): 'python3 download_things.py http://soundcloud.com/csingh91/sets/mixes' to download tracks from csingh91's "mixes" playlist

#Notes
* script will keep track of downloaded files, and skip them on next run (data saved to "dl_data.json" by default)