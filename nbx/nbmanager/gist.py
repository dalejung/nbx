import github

def _hashtags(desc):
    if not desc:
        return []
    tags = [tag for tag in desc.split(" ") if tag.startswith("#")]
    return tags

class TaggedGist(object):
    system_tags = ['#inactive']

    def __init__(self, gist, name, tags):
        self.gist = gist
        self.name = name
        self.tags = tags

    @staticmethod
    def from_gist(gist):
        desc = gist.description
        if desc is None:
            desc = ''
        hashtags = _hashtags(desc)
        name = TaggedGist._name(desc)
        tags = TaggedGist._tags(hashtags)
        tg = TaggedGist(gist, name, tags)
        active = "#inactive" not in hashtags
        tg.active = active
        return tg

    @staticmethod
    def _name(desc):
        words = [w for w in desc.split() if not w.startswith("#")]
        name = " ".join(words)
        return name

    @classmethod
    def _tags(cls, hashtags):
        tags = hashtags[:]
        for tag in cls.system_tags:
            try:
                tags.remove(tag)
            except:
                pass
        return tags

    def __repr__(self):
        out = "TaggedGist(name={name}, active={active}, tags={tags})"
        return out.format(**self.__dict__)

class GistHub(object):
    def __init__(self, hub):
        self.hub = hub
        self.user = hub.get_user()
        self._cache = {}

    def _get_gists(self):
        gists = self.user.get_gists()
        return gists

    def query(self, tag=None, active=True):
        """
        Query gists by our tag format.
        Always returns gists grouped by tags.
        """
        tagged_gists = self._get_tagged_gists()

        if active is not None:
            tagged_gists = self.filter_active(tagged_gists, active)

        return self.filter_tag(tagged_gists, tag)

    def filter_tag(self, gists, tag):
        if isinstance(tag, basestring):
            tag = [tag]
        if tag is None:
            tag = []

        tag = map(lambda t: t.startswith("#") and t or '#'+t, tag)

        # group active gists into tags
        tagged = {}
        for gist in gists:
            gist_tags = set(gist.tags).intersection(tag)
            for gtag in gist_tags:
                nb_list = tagged.setdefault(gtag, [])
                nb_list.append(gist)
        return tagged

    def filter_active(self, gists, active):
        gists = filter(lambda gist: gist.active, gists)
        return gists

    def _get_tagged_gists(self):
        if self._cache.get('tagged_gists', None) is None:
            gists = self._get_gists()
            tagged_gists = [TaggedGist.from_gist(gist) for gist in gists if gist.description]
            self._cache['tagged_gists'] = tagged_gists
        return self._cache['tagged_gists']


def gist_hub(user, password):
    g = github.Github(user, password, user_agent="nbx")
    return GistHub(g)
