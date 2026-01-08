"""
h26x-extractor

Usage:
  h26x-extractor [options] <input-file>...

Options:
  -v --verbose                   Enable human-readable output to stderr for all NALU types.
  -t --verbose-types TYPES       Comma-separated list of NALU types for human-readable output.
  -o --output-file FILE          Write JSON output to FILE instead of stdout.

Output:
  By default, JSON output is written to stdout.
  Use -v or -t to additionally print human-readable output to stderr.

Example:
  h26x-extractor file1.264 file2.264
  h26x-extractor -v file.264 2>/dev/null  # JSON only
  h26x-extractor -v file.264 > /dev/null  # Human-readable only
  h26x-extractor -o output.json file.264
"""

import json
import sys
import time
from docopt import docopt
from functools import partial
from . import __version__
from . import h26x_parser
from . import nalutypes


def main():
    args = docopt(__doc__, version=str(__version__), options_first=False)

    # Convert the comma-separated string into a list of integers
    nalu_types = []
    if args["--verbose-types"]:
        try:
            nalu_types = [int(n) for n in args["--verbose-types"].split(",")]
        except ValueError:
            print(
                "Error: --verbose-types must be a comma-separated list of integers",
                file=sys.stderr,
            )
            sys.exit(1)
    elif args["--verbose"]:
        # Add all types
        for i in range(32):
            nalu_types.append(i)

    verbose = len(nalu_types) > 0

    # Collect all NALUs for JSON output
    all_nalus = []

    def collect_nalu(parser, input_file, nalu: nalutypes.NALU, nalu_type, start, end):
        """
        Collect NALU data for JSON output and optionally print human-readable output to stderr.
        """
        # Build NALU data dict
        nalu_bytes = parser.byte_stream[start : end + 1].hex()
        rbsp_bytes = bytearray(nalu.s.tobytes()).hex()

        nalu_data = {
            "input_file": input_file,
            "position": {
                "start": start,
                "end": end,
                "length": end - start + 1,
            },
            "type": nalu_type,
            "type_name": nalutypes.get_description(nalu_type),
            "nalu_bytes": nalu_bytes,
            "rbsp_bytes": rbsp_bytes,
            "fields": nalu.to_dict(),
        }
        all_nalus.append(nalu_data)

        # Print human-readable output to stderr if verbose
        if verbose and nalu_type in nalu_types:
            print("", file=sys.stderr)
            print(
                "========================================================================================================",
                file=sys.stderr,
            )
            print("", file=sys.stderr)
            print(
                "NALU bytepos:\t[" + str(start) + ", " + str(end) + "]", file=sys.stderr
            )
            print("NALU offset:\t" + str(start) + " Bytes", file=sys.stderr)
            print(
                "NALU length:\t"
                + str(end - start + 1)
                + " Bytes (including start code)",
                file=sys.stderr,
            )
            print(
                "NALU type:\t"
                + str(nalu_type)
                + " ("
                + nalutypes.get_description(nalu_type)
                + ")",
                file=sys.stderr,
            )

            substr = nalu_bytes
            if len(substr) > 250:
                substr = substr[:250] + "..."
            print("NALU bytes:\t" + "0x" + substr, file=sys.stderr)
            substr = rbsp_bytes
            if len(substr) > 250:
                substr = substr[:250] + "..."
            print("NALU RBSP:\t" + "0x" + substr, file=sys.stderr)
            print("", file=sys.stderr)

            nalu.print_verbose(file=sys.stderr)

    start_time = time.time()

    for f in args["<input-file>"]:
        parser = h26x_parser.H26xParser(f)
        parser.set_allcallbacks(partial(collect_nalu, parser, f))
        parser.parse()

    stop_time = time.time()

    if verbose:
        print(
            "Parsing took " + str(stop_time - start_time) + " seconds", file=sys.stderr
        )

    # Output JSON
    output_file = args["--output-file"]
    if output_file:
        with open(output_file, "w") as out:
            json.dump(all_nalus, out, indent=2)
    else:
        print(json.dumps(all_nalus, indent=2))


if __name__ == "__main__":
    main()
