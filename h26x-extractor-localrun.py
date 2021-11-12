"""
h26x-extractor 0.2

Usage:
  h26x-extractor [options] <input-file>...

Options:
  -v --verbose                       Enable verbose output

Example:
  h26x-extractor -v file1.264 file2.264

Install from sources: 
  python .\setup.py install
  python -m h26x_extractor --version
if a build directory exists, remove it with:
  rm build
  rm dist
  rm h26x_extractor.egg-info
After installation, you can run the program with:
  h26x-extractor -v file1.264 file2.264

"""
import sys, time
sys.path.append('h26x_extractor/')
from docopt import docopt
from h26x_extractor import __version__
from h26x_extractor import h26x_parser

def timeit(method):
    def timed(*args, **kw):
        ts = time.time()
        result = method(*args, **kw)
        te = time.time()
        print('%r  %2.2f ms' % \
                (method.__name__, (te - ts) * 1000))
        return result
    return timed

args = docopt(__doc__, version=str(__version__), options_first=False)

def main():
    for f in args["<input-file>"]:
        ex = h26x_parser.H26xParser(f, verbose=args["--verbose"])
        ex.parse()

if __name__ == "__main__":
    if args["--verbose"] == True:
      timeit(main)()
    else:
      main()
    if args["--verbose"] == True:
      print('Verbose is true')
    else:
      print('Verbose is false')