"""
h26x-extractor

Usage:
  h26x-extractor [options] <input-file>...

Options:
  -v --verbose                   Enable verbose output for all types.
  -t --verbose-types TYPES       Comma-separated list of NALU types for verbose output.

Example:
  h26x-extractor -t 1,5,7 file1.264 file2.264
"""
import time
from docopt import docopt
from functools import partial
from . import __version__
from . import h26x_parser
from . import nalutypes

args = docopt(__doc__, version=str(__version__), options_first=False)

# Convert the comma-separated string into a list of integers
nalu_types = []
if args["--verbose-types"]:
    try:
        nalu_types = [int(n) for n in args["--verbose-types"].split(",")]
    except ValueError:
        print("Error: --verbose-types must be a comma-separated list of integers")
        exit(1)
elif (args["--verbose"]):
    # Add all types
    for i in range(32):
        nalu_types.append(i)

def print_nalu(parser, nalu: nalutypes.NALU, type, start, end):
    """
    Print the NALU information to the console if the type is in the verbose list.
    """

    if type not in nalu_types:
        return
    
    print("")
    print(
        "========================================================================================================"
    )
    print("")
    print("NALU bytepos:\t[" + str(start) + ", " + str(end) + "]")
    print("NALU offset:\t" + str(start) + " Bytes")
    print(
        "NALU length:\t"
        + str(end - start + 1)
        + " Bytes (including start code)"
    )
    print(
        "NALU type:\t"
        + str(type)
        + " ("
        + nalutypes.get_description(type)
        + ")"
    )

    substr = parser.byte_stream[start : end + 1].hex()
    if len(substr) > 250:
        substr = substr[:250] + "..."
    print("NALU bytes:\t" + "0x" + substr)
    substr = bytearray(nalu.s.tobytes()).hex()
    if len(substr) > 250:
        substr = substr[:250] + "..."
    print("NALU RBSP:\t" + "0x" + substr)
    print("")

    nalu.print_verbose()

def main():
    for f in args["<input-file>"]:
        
        # This is a good example of how to use the h26x_parser module
        # and how to set up callbacks for every NALU types.
        parser = h26x_parser.H26xParser(f)
        parser.set_allcallbacks(partial(print_nalu, parser))
        parser.parse()

if __name__ == "__main__":
    start = time.time()
    main()
    stop = time.time()
    if args["--verbose"]:
        print(main.__name__ + " took " + str(stop - start) + " seconds")
