import re, sys, operator

from plugit import version
from plugit.exceptions import VersionError

CMP_OP_MAP = {
    '<':  operator.lt,
    '<=': operator.le,
    '==': operator.eq,
    '!=': operator.ne,
    '>=': operator.ge,
    '>':  operator.gt,
}

# ",?\s*(?=%s)" % "|".join(CMP_OP_MAP.keys())
DEP_SPLIT_RE = re.compile(r',?\s*(?=<|<=|!=|==|>=|>)')
VER_DEP_RE = re.compile(r'(?P<cmp><|<=|!=|==|>=|>)\s*(?P<ver>[-a-z0-9. ]+)')

def _parse(ver_deps):
    chunks = DEP_SPLIT_RE.split(ver_deps)
    ret = []
    for chunk in chunks:
        ret.append(VER_DEP_RE.match(chunk).groupdict())
    return ret

def is_installed(appname, ver_deps=None, additional_paths=None):
    if additional_paths:
        for path in additional_paths:
            sys.path.insert(0, path)
    try:
        __import__(appname)
        app = sys.modules[appname]
    except ImportError:
        return False

    if not ver_deps:
        return True

    for ver in _parse(ver_deps):
        if CMP_OP_MAP[ver['cmp']](app.VERSION,
                version.from_string(ver['ver'])):
            return True

    raise VersionError("Application %s installed version %s does not "
            "satisfy the version dependencies %s."
            % (appname, str(app.VERSION), str(ver_deps)))

def python_version_supported(python_versions):
    # or platform.python_version_tuple()?
    python_version = version.Version(sys.version_info[:3])
    for ver in _parse(python_versions):
        if CMP_OP_MAP[ver['cmp']](python_version,
                version.from_string(ver['ver'])):
            return True
    return False

def platform_supported(platforms):
    if sys.platform in platforms:
        return True
    return False

def best_version(versions):
    """Not implemented."""
    return None
