try:
    from japong.main import main
except ImportError:
    import os
    import sys

    sys.path.insert(0, os.path.realpath('.'))

    from crawler.main import main


main()
