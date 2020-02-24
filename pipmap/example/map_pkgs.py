import sys

from pipmap import Mapper


def main():
    mapper = Mapper(
        reqs="requirements.txt",
        fmt="json",
        # debug=True
    )
    return mapper.map()


if "__main__" == __name__:
    rc = 1
    try:
        pkg_info = main()
        print(pkg_info)
        rc = 0
    except Exception as e:
        print(f'Error: {e}', file=sys.stderr)
    sys.exit(rc)
