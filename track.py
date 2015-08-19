import soundcloud
import helpers

class Track:
    def __init__(self, object):
        # Note to self:
        # likes = client.get('/users/<username>/favorites')
        #       -> type(likes) = <class 'soundcloud.resource.ResourceList'>
        #       -> type(likes[0]) = <class 'soundcloud.resource.Resource'>
        # r = client.get('/resolve', url=<playlist_url>)
        #       -> type(r.tracks) = <type 'list'>
        #       -> type(r.tracks[0]) = <type 'dict'>
        self.username = None;
        self.title = None;
        self.permalink = None;
        self.description = None;
        self.stream_url = None;
        self.download_url = None;
        self.artwork_url = None;
        self.filename = None;

        if type(object) is soundcloud.resource.Resource:
            self.init_from_sc_resource(object)
        elif type(object) is dict:
            self.init_from_dict(object)
        else:
            raise TypeError("Unsupported type: %s." % str(type(object)))

        self.filename = helpers.slugify(self.username) + "-" + helpers.slugify(self.title)

        # just to be safe... shouldn't hurt.
        self.username = helpers.convert_to_ascii(self.username);
        self.title = helpers.convert_to_ascii(self.title);
        self.permalink = helpers.convert_to_ascii(self.permalink);
        self.description = helpers.convert_to_ascii(self.description);
        self.stream_url = helpers.convert_to_ascii(self.stream_url);
        self.download_url = helpers.convert_to_ascii(self.download_url);
        self.artwork_url = helpers.convert_to_ascii(self.artwork_url);

    def init_from_sc_resource(self, sc_resource):
        self.username = sc_resource.user["username"]
        self.title = sc_resource.title
        self.permalink = sc_resource.permalink_url
        self.description = sc_resource.description

        # set stream_url if it exists
        if "stream_url" in sc_resource.keys():
            self.stream_url = sc_resource.stream_url

        # set download_url if it exists
        if "download_url" in sc_resource.keys():
            self.download_url = sc_resource.download_url
        
        # if no artwork, use artist's avatar
        if sc_resource.artwork_url is not None:
            self.artwork_url = sc_resource.artwork_url
        else:
            self.artwork_url = sc_resource.user["avatar_url"]

        # get 500x500 link instead of thumbnail
        self.artwork_url = self.artwork_url.replace("-large", "-t500x500")

    def init_from_dict(self, dict_obj):
        self.username = dict_obj["user"]["username"]
        self.title = dict_obj["title"]
        self.permalink = dict_obj["permalink_url"]
        self.description = dict_obj["description"]

        # set stream_url if it exists
        if "stream_url" in dict_obj:
            self.stream_url = dict_obj["stream_url"]

        # set download_url if it exists
        if "download_url" in dict_obj:
            self.download_url = dict_obj["download_url"]

        # if no artwork, use artist's avatar
        if dict_obj["artwork_url"] is not None:
            self.artwork_url = dict_obj["artwork_url"]
        else:
            self.artwork_url = dict_obj["user"]["avatar_url"]

        # get 500x500 link instead of thumbnail
        self.artwork_url = self.artwork_url.replace("-large", "-t500x500")

    def get_download_link(self, client_id):
        if self.stream_url is None and self.download_url is None:
            return None

        download_link = self.stream_url

        if self.download_url is not None:
            download_link = self.download_url

        download_link = download_link + "?client_id=" + client_id

        return download_link

    def to_dict(self):
        d = {}
        d["username"] = self.username;
        d["title"] = self.title;
        d["permalink"] = self.permalink;
        d["description"] = self.description;
        d["stream_url"] = self.stream_url;
        d["download_url"] = self.download_url;
        d["artwork_url"] = self.artwork_url;
        d["filename"] = self.filename;

        return d

    def __str__(self):
        s  = "username: " + str(self.username )+ "\n"
        s += "title: " + str(self.title )+ "\n"
        s += "filename: " + str(self.filename )+ "\n"
        s += "permalink: " + str(self.permalink )+ "\n"
        s += "stream_url: " + str(self.stream_url )+ "\n"
        s += "download_url: " + str(self.download_url )+ "\n"
        s += "artwork_url: " + str(self.artwork_url )+ "\n"
        s += "description: " + str(self.description)

        return s
