class PlugitError(RuntimeError):
    pass

class SettingsError(PlugitError):
    pass

class VersionError(PlugitError):
    pass

class FetchError(PlugitError):
    pass
