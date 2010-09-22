class DatastoreSession(ModificationTrackingDict):
    @classmethod
    def get_session(cls, store, name, **kwargs):
        """TODO"""
        raise NotImplementedError()

    def save_session(self, response, store, name, **kwargs):
        """TODO"""
        raise NotImplementedError()


class MemcacheSession(ModificationTrackingDict):
    @classmethod
    def get_session(cls, store, name, **kwargs):
        """TODO"""
        raise NotImplementedError()

    def save_session(self, response, store, name, **kwargs):
        """TODO"""
        raise NotImplementedError()
