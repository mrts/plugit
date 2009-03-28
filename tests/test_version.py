from nose.tools import assert_raises

from plugit.version import from_string, Version
from plugit.exceptions import VersionError

def test_invalid():
    no_args = lambda: Version()
    assert_raises(TypeError, no_args)

    few_args = lambda: Version(0)
    assert_raises(TypeError, few_args)

    invalid_args = lambda: Version("a", "b", "c")
    assert_raises(VersionError, invalid_args)
    try:
        invalid_args()
    except VersionError, e:
        assert str(e) == "Major number has to be an integer."

    invalid_subrelease = lambda: Version(1, 2, subrelease=4)
    assert_raises(VersionError, invalid_subrelease)
    try:
        invalid_subrelease()
    except VersionError, e:
        assert str(e) == "Subrelease has to be one of pre-alpha (0), alpha (1), beta (2), prerelease (3)."

    prealpha_with_subrellevel = lambda: Version(1, 2, subrelease=0,
            subrellevel=1)
    assert_raises(VersionError, prealpha_with_subrellevel)
    try:
        prealpha_with_subrellevel()
    except VersionError, e:
        assert str(e) == "Pre-alpha release can have no subrelease level number."

def test_ordering():
    v0 = Version(0,1)
    v1 = Version(1,2)
    v2 = Version(1,2,1)
    v3 = Version(1,2,1,2,2)
    v4 = Version(1,2,1,2,3)
    v5 = Version(major=1, patch=1, minor=2, subrellevel=2, subrelease=2)

    assert v1 > v0
    assert v1 >= v0
    assert v0 < v1
    assert v0 <= v1
    assert v2 > v1
    assert v0 > v3
    assert v4 > v3

    assert v1 != v2
    assert v3 == v5

def test_fromstring():
    assert from_string('1.1') == Version(1, 1)
    assert from_string('1.1 beta 1') == Version(1, 1,
            subrelease=2, subrellevel=1)
    assert from_string('356.42.376 pre-alpha') == Version(356, 42, 376, 0)

    invalid_str = lambda: from_string('foo')
    assert_raises(VersionError, invalid_str)
    try:
        invalid_str()
    except VersionError, e:
        assert str(e) == "Incorrect version string. Please generate it in the manner of 'str(Version(1, 2, 0, ALPHA, 1))'."

    invalid_subrel = lambda: from_string('1.2 bar 1')
    assert_raises(VersionError, invalid_subrel)
    try:
        invalid_subrel()
    except VersionError, e:
        assert str(e) == "Subrelease has to be one of pre-alpha (0), alpha (1), beta (2), prerelease (3)."
