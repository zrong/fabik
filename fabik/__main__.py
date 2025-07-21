
import sys
import os

if __name__ == '__main__':
    if not __package__:
        path = os.path.join(os.path.dirname(__file__), os.pardir)
        sys.path.insert(0, path)
    import fabik.cli
    fabik.cli.main()