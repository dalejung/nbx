"""
Interface with github gists with tagging.

This file should have no knowledge of notebooks and only deal with
gists and tagging.
"""
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
        # unique identifier name
        self.suffix = " [{0}].ipynb".format(self.id)
        self.key_name = self.name + self.suffix

    def strip_gist_id(self, name):
        suffix = " [{0}].ipynb".format(self.id)
        # really we're assuming this will only match once, seems fine
        return key_name.replace(suffix, '')

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

    @property
    def updated_at(self):
        return self.gist.updated_at

    @property
    def created_at(self):
        return self.gist.created_at

    @property
    def public(self):
        return self.gist.public

    @property
    def id(self):
        return self.gist.id

    @property
    def files(self):
        return self.gist.files

    def __repr__(self):
        out = "TaggedGist(name={name}, active={active}, public={public}, tags={tags})"
        return out.format(public=self.public, **self.__dict__)

class GistHub(object):
    def __init__(self, hub):
        self.hub = hub
        self.user = hub.get_user()
        self._tagged_gists = None

    def _get_gists(self):
        gists = self.user.get_gists()
        return gists

    def query(self, tag=None, active=True, filter_tag=None, drop_filter=True):
        """
        Query gists by our tag format.
        Always returns gists grouped by tags.
        """
        tagged_gists = self._get_tagged_gists().values()

        tagged_gists = self._filter_active(tagged_gists, active)

        filter_tag = self._normalize_tag(filter_tag)
        if filter_tag:
            tagged_gists = self._filter_tag(tagged_gists, filter_tag)

        if not drop_filter:
            filter_tag = None

        return self._select_tag(tagged_gists, tag, filter_tag=filter_tag)

    def _normalize_tag(self, tag):
        if tag is None:
            tag = []
        if isinstance(tag, basestring):
            tag = [tag]

        # allow tag in both hashtag and bare form
        tag = map(lambda t: t.startswith("#") and t or '#'+t, tag)
        return tag

    def _filter_tag(self, gists, filter_tag):
        """
        Filter out the gists that don't match all the filtered tags.
        """
        filter_tag = self._normalize_tag(filter_tag)
        gists = filter(lambda gist: set(gist.tags).issuperset(filter_tag), gists)
        return gists

    def _select_tag(self, gists, select_tag, filter_tag=None):
        """
        Group by tag and then select tag groups
        """
        select_tag = self._normalize_tag(select_tag)

        # group active gists into tags
        tagged = {}
        for gist in gists:
            gist_tags = set(gist.tags)
            if select_tag:
                gist_tags = gist_tags.intersection(select_tag)
            if filter_tag:
                gist_tags = gist_tags.difference(filter_tag)

            for gtag in gist_tags:
                nb_list = tagged.setdefault(gtag, [])
                # should not get duplicate names since we use gist.id in
                # key_name
                if gist.key_name in nb_list:
                    raise Exception("{0} has duplciates for {1}".format(gtag, gist.key_name))
                nb_list.append(gist)
        return tagged

    def _filter_active(self, gists, active):
        if active is None:
            return gists
        gists = filter(lambda gist: gist.active == active, gists)
        return gists

    def _get_tagged_gists(self):
        if self._tagged_gists is None:
            gists = self._get_gists()
            tagged_gists = [(gist.id, TaggedGist.from_gist(gist))
                            for gist in gists if gist.description]
            tagged_gists = dict(tagged_gists)
            self._tagged_gists = tagged_gists
        return self._tagged_gists

    def refresh_gist(self, gist_id):
        if hasattr(gist_id, 'id'):
            gist_id = gist_id.id
        gist = self.hub.get_gist(gist_id)
        tagged_gist = self._tagged_gists[gist_id]
        tagged_gist.gist = gist
        return tagged_gist


def gisthub(user, password):
    g = github.Github(user, password, user_agent="nbx")
    return GistHub(g)