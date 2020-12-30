"""
h26x-extractor 0.2

Usage:
  h26x-extractor [options] <input-file>...

Options:
  -v --verbose                       Enable verbose output

Example:
  h26x-extractor -v file1.264 file2.264
"""

from docopt import docopt

from . import __version__

from . import h26x_parser


def main():
    args = docopt(__doc__, version=str(__version__), options_first=False)
    for f in args["<input-file>"]:
        ex = h26x_parser.H26xParser(f, verbose=args["--verbose"])
        ex.parse()


if __name__ == "__main__":
    main()
