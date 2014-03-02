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
    # instead of having a bunch of @property getters, define
    # attrs to grab from .gist here.
    _gist_attrs = ['id', 'tags', 'files', 'active', 'edit', 'updated_at', 
                   'created_at']

    system_tags = ['#inactive']

    def __init__(self, gist, name, tags, active=True):
        self.gist = gist
        self.name = name
        self.tags = tags
        self.active = active

    def update_from_gist(self):
        desc = self.gist.description
        if desc is None:
            desc = ''
        hashtags = _hashtags(desc)
        self.name = TaggedGist._name(desc)
        self.tags = TaggedGist._tags(hashtags)
        active = "#inactive" not in hashtags
        self.active = active

    @staticmethod
    def from_gist(gist):
        tg = TaggedGist(gist, None, None)
        tg.update_from_gist()
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

    def revisions_for_file(self, filename):
        " returns revisions applicable to file "
        revisions = []
        for state in self.gist.history:
            # only use commits that contain the gist file
            if filename not in state.raw_data['files']:
                continue

            revisions.append(state)
        return revisions

    def get_revision(self, commit_id):
        " get revision by id "
        for state in self.gist.history:
            if commit_id == state.version:
                return state

    def get_revision_file(self, commit_id, filename):
        " get the file object for a specific file"
        state = self.get_revision(commit_id)
        if state:
            return state.raw_data['files'][filename]

    @property
    def files(self):
        return self.gist.files

    def __getattr__(self, name):
        if name in self._gist_attrs:
            return getattr(self.gist, name)
        raise AttributeError("{name} not found on .gist".format(name=name))

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

    def select(self, gist_id):
        gist_id = str(gist_id)
        return self._tagged_gists[gist_id]

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
        self.update_gist(tagged_gist)
        return tagged_gist

    def update_gist(self, gist):
        assert gist.id in self._tagged_gists
        gist.update_from_gist()
        assert isinstance(gist, TaggedGist)
        self._tagged_gists[gist.id] = gist

def gisthub(user, password):
    g = github.Github(user, password, user_agent="nbx")
    return GistHub(g)
