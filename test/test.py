#!/usr/bin/env python3

"""Simple unittest usage."""

import unittest
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from h26x_extractor import h26x_parser


class ParsingTest(unittest.TestCase):
    def print_nalu(nalu, *args):
        nalu.print_verbose()

    def testAUDParser(self):
        """Simple AUD parsing."""
        blob = "000000010910"
        # create parser
        ex = h26x_parser.H26xParser(None, use_bitstream=blob)
        ex.set_allcallbacks(ParsingTest.print_nalu)
        # make sure decode is happy
        ex.parse()


if __name__ == "__main__":
    unittest.main()
