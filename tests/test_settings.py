"""
Tests for updating settings.
"""
import os, sys
from nose.tools import assert_raises
from lib2to3.pgen2.parse import ParseError

from plugit.settingshandler import SettingsFileUpdater

TESTDATADIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data')

def test_parse():
    nonexisting = lambda: SettingsFileUpdater(
            os.path.join(TESTDATADIR, "n o n e x i s t i n g"))
    unparseable = lambda: SettingsFileUpdater(
            os.path.join(TESTDATADIR, 'invalid.txt'))
    assert_raises(IOError, nonexisting)
    assert_raises(ParseError, unparseable)

def test_update_settings():
    new_settings = {
            'A_TUPLE': ('Neque', 'porro', ('quisquam', 'est'),),
            'A_DICT': {'dolorem': 3600},
            'A_STRING': 'ipsum',
            'AN_INT': 42,
            'A_BOOL': True,
    }

    append_settings = {
            'NONEMPTY_TUPLE': 'porro',
            'EMPTY_TUPLE': ('quisquam', 'est', True, 34),
            'NONEMPTY_DICT': {'qui': 'dolorem', 'ipsum' : 42},
            'EMPTY_DICT' : {'quia': True, 'dolor': {'sit': 'amet'}},
            }

    updater = SettingsFileUpdater(os.path.join(TESTDATADIR,
        'testsettings.py'))
    updater.update(new_settings, append_settings)
    updater.save(os.path.join(TESTDATADIR, 'tmpsettings.py'))

    settings_module = 'tests.data.tmpsettings'
    __import__(settings_module, level=1)
    settings = sys.modules[settings_module]
    for key, val in new_settings.iteritems():
        assert getattr(settings, key) == val
