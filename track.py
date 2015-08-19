import soundcloud

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

        if type(object) is soundcloud.resource.Resource:
            self.init_from_sc_resource(object)
        elif type(object) is dict:
            self.init_from_dict(object)
        else:
            raise TypeError("Unsupported type: %s." % str(type(object)))

    def init_from_sc_resource(self, sc_resource):
        self.username = sc_resource.user["username"]
        self.title = sc_resource.title
        self.permalink = sc_resource.permalink_url
        self.description = sc_resource.description
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

    def get_dl_link(self, client_id):
        dl_link = self.stream_url

        if self.download_url is not None:
            dl_link = self.download_url

        dl_link = dl_link + "?client_id=" + client_id

        return dl_link
