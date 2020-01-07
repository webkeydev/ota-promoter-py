import os

_curdir = '.'
_separator = '/'


def S_IFMT(mode):
    return mode & 0o170000


def exists(path):
    """Test whether a path exists.  Returns False for broken symbolic links"""
    try:
        os.stat(path)
    except OSError:
        return False
    return True


def isdir(s):
    """Return true if the pathname refers to an existing directory."""
    try:
        st = os.stat(s)
    except OSError:
        return False

    S_IFDIR = 0o040000  # directory
    return S_IFMT(st.st_mode) == S_IFDIR


def dir_name(p):
    dirs = p.rstrip(_separator).split(_separator)
    return _separator.join(dirs[:-1])


def rm_dirs(directory):
    if not exists(directory):
        return

    for entry in os.ilistdir(directory):
        is_dir = entry[1] == 0x4000
        path = directory + _separator + entry[0]
        if is_dir:
            rm_dirs(path)
        else:
            os.remove(path)
    os.rmdir(directory)


def makedirs(name, exist_ok=False):
    head, tail = split(name)
    if not tail:
        head, tail = split(head)
    if head and tail and not exists(head):
        try:
            makedirs(head, exist_ok=exist_ok)
        except FileExistsError:
            pass

        cdir = _curdir
        if isinstance(tail, bytes):
            cdir = bytes(_curdir, 'ASCII')

        if tail == cdir:
            return
    try:
        os.mkdir(name)
    except OSError:
        if not exist_ok or not isdir(name):
            raise


def walk(directory):
    dirs = []
    files = []
    walk_dirs = []

    for entry in os.ilistdir(directory):
        is_dir = entry[1] == 0x4000
        path= directory + _separator + entry[0]
        if is_dir:
            dirs.append(path)
            walk_dirs.append(path)
        else:
            files.append(path)

    for new_path in walk_dirs:
        yield from walk(new_path)
    yield dirs, files


def path_join(a, b):
    a = a.rstrip("/")
    return a+"/"+b


def split(path):
    res = path.split(_separator)
    if len(res) is 1:
        return '', res[0]

    if res[-1] is not '':
        head = _separator.join(res[:-1])
        return head, res[-1]

    if res[-1] is '':
        return path.rstrip("/"), ''

    return '', ''
