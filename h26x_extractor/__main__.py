"""
h26x-extractor

Usage:
  h26x-extractor [options] <input-file>...

Options:
  -v --verbose                       Enable verbose output

Example:
  h26x-extractor -v file1.264 file2.264
"""
import time
from docopt import docopt
from . import __version__
from . import h26x_parser

args = docopt(__doc__, version=str(__version__), options_first=False)


def main():
    for f in args["<input-file>"]:
        ex = h26x_parser.H26xParser(f, verbose=args["--verbose"])
        ex.parse()


if __name__ == "__main__":
    start = time.time()
    main()
    stop = time.time()
    if args["--verbose"]:
        print(main.__name__ + " took " + str(stop - start) + " seconds")
