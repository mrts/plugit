"""
Uniform version handling module. Plugit-conforming packages MUST use the
`Version` objects defined here to declare their versions.

Version strings are in "major.minor[.patch] [sub]" format. The major number is
0 for initial, experimental releases of software. It is incremented for
releases that represent major milestones in a package. The minor number is
incremented when important new features are added to the package. The patch
number increments when bug-fix releases are made.

Additional trailing version information is used to indicate sub-releases.
These are "alpha 1, alpha 2, ..., alpha N" for alpha releases, where
functionality and API may change, "beta 1, beta 2, ..., beta N" for beta
releases, which only fix bugs and "pre 1, pre 2, ..., pre N" for final
pre-release release testing. The "pre-alpha" sub-release is special, marking a
version that is currently in development and not yet in release stage. As such
it cannot have a sub-release version number. A release without sub-release
information is considered final.

Packages have to utilise the `Version` class below for specifying their
versions, e.g.::

 from plugit import version

 VERSION = version.Version(0, 1)
 # or
 VERSION = version.Version(0, 1, 2)
 # or
 VERSION = version.Version(1, 0, 3, version.PRE_ALPHA)
 # or
 VERSION = version.Version(1, 0, version.ALPHA, 1)

"""
import re

from plugit.exceptions import VersionError

PRE_ALPHA, ALPHA, BETA, PRERELEASE, FINAL = range(5)

SUBRELEASE_DICT = {
    PRE_ALPHA:  'pre-alpha',
    ALPHA:      'alpha',
    BETA:       'beta',
    PRERELEASE: 'prerelease',
}

SUBRELEASE_DICT_REVERSE = dict((value, key) for key, value in
    SUBRELEASE_DICT.items())


def SubreleaseError():
    """
    A factory function for creating a particularly complex yet informative
    VersionError instance.
    """
    return VersionError("Subrelease has to be one of %s." %
            ", ".join("%s (%s)" %
                (SUBRELEASE_DICT[key], key)
                for key in sorted(SUBRELEASE_DICT.keys())))

class Version(object):
    """
    Class for representing package versions.

    `Version` objects have human-readable string representation and defined
    ordering. When comparing versions, non-release versions (i.e. versions
    that *have subrelease numbers*) have less priority than release versions,
    e.g.::

    >>> v = Version(1, 2, 3, BETA, 1)
    >>> v2 = Version(0, 1)
    >>> v2 > v
    True
    >>> v3 = Version(1, 2, 3)
    >>> v3 > v2
    True

    Usage::

    >>> v = Version(0, 1)
    >>> v
    Version(major=0, minor=1)
    >>> print v
    0.1
    >>> print Version(0, 1, subrelease=0)
    0.1 pre-alpha
    >>> print Version(0, 1, subrelease=1, subrellevel=1)
    0.1 alpha 1

    >>> Version(1, 2, 3, 0)
    Version(major=1, minor=2, patch=3, subrelease=0)
    >>> Version(1, 2, 3, PRE_ALPHA)
    Version(major=1, minor=2, patch=3, subrelease=0)

    >>> v = Version(1, 2, 3, BETA, 1)
    >>> v
    Version(major=1, minor=2, patch=3, subrelease=2, subrellevel=1)
    >>> print v
    1.2.3 beta 1
    """
    def __init__(self, major, minor, patch=None, subrelease=None,
            subrellevel=None):
        self.major = _to_int(major, "Major number")
        self.minor = _to_int(minor, "Minor number")
        self.patch = _to_int_or_none(patch, "Patch number")
        self.subrelease = _to_int_or_none(subrelease, "Subrelease number")
        if (self.subrelease is not None and
                self.subrelease not in SUBRELEASE_DICT):
            raise SubreleaseError()
        if self.subrelease == PRE_ALPHA and subrellevel is not None:
            raise VersionError("Pre-alpha release can have no subrelease "
                    "level number.")
        self.subrellevel = _to_int_or_none(subrellevel,
                "Subrelease level number")

    def __str__(self):
        format = '%(major)s.%(minor)s'
        params = self.__dict__.copy()
        if self.patch is not None:
            format += '.%(patch)s'
        if self.subrelease is not None:
            format += ' %(subrelease)s'
            params['subrelease'] = SUBRELEASE_DICT[self.subrelease]
        if self.subrellevel is not None:
            format += ' %(subrellevel)s'
        return format % params

    def as_tuple(self):
        return (self.major, self.minor, self.patch, self.subrelease,
            self.subrellevel)

    def __repr__(self):
        return 'Version(%s)' % ', '.join(['%s=%s' %
            (label, getattr(self, label))
            for label in sorted(self.__dict__.keys())
            if getattr(self, label) is not None])

    def __lt__(self, other):
        # non-release versions are always lower priority
        if self.subrelease is not None and other.subrelease is None:
            return True
        if other.subrelease is not None and self.subrelease is None:
            return False

        return self.as_tuple() < other.as_tuple()

    def __gt__(self, other):
        return other < self

    def __le__(self, other):
        return not (other < self)

    def __ge__(self, other):
        return not (self < other)

    def __eq__(self, other):
        return self.as_tuple() == other.as_tuple()

    def __ne__(self, other):
        return not (self == other)

    def __hash__(self):
        return hash(self.as_tuple())


VERSION_RE = re.compile(r'^(?P<major>\d+)\.(?P<minor>\d+)(\.(?P<patch>\d+))?'
        r'( (?P<subrelease>[-a-z]+)( (?P<subrellevel>\d+))?)?$')
def from_string(version_string):
    """
    Factory function that creates `Version` objects from version strings.

    To specify strings in right format, create a `Version` object and convert
    it to string to get the canonical representation.

    Usage:

    >>> from_string('1.2.1 beta 5')
    Version(major=1, minor=2, patch=1, subrelease=2, subrellevel=5)
    >>> from_string('1.2')
    Version(major=1, minor=2)

    :param version_string: the string that specifies the version
    :return: a Version object
    """
    match = VERSION_RE.match(version_string)
    if not match:
        raise VersionError("Incorrect version string. Please generate it in "
                "the manner of 'str(Version(1, 2, 0, ALPHA, 1))'.")
    result = match.groupdict()
    if result['subrelease'] is not None:
        if result['subrelease'] not in SUBRELEASE_DICT_REVERSE:
            raise SubreleaseError()
        result['subrelease'] = SUBRELEASE_DICT_REVERSE[result['subrelease']]
    return Version(**result)

def _to_int(value, label):
    try:
        return int(value)
    except (TypeError, ValueError):
        raise VersionError("%s has to be an integer." % label)

def _to_int_or_none(value, label):
    if value is None:
        return value
    return _to_int(value, label)
