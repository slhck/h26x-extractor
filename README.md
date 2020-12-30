# h26x-extractor

[![PyPI version](https://badge.fury.io/py/h26x-extractor.svg)](https://badge.fury.io/py/h26x-extractor)

Author: Werner Robitza, with contributions from @chemag

Extracts NAL units from H.264 bitstreams and decodes their type and content, if supported.

**Note:** This is not a replacement for a proper tool like [h264bitstream](https://github.com/aizvorski/h264bitstream). `h26x-extractor` is not fast and not robust, but rather a playground for parsing bitstreams. Use with caution!

# Installation

Requirements: Python 3.5 or higher

Via pip:

    pip3 install h26x-extractor

# Status

Currently supported:

- Parsing of H.264 bitstreams
- Parsing of NALU
- Parsing of AUD
- Parsing of CodedSliceIDR
- Parsing of CodedSliceNonIDR
- Parsing of SPS
- Parsing of PPS

Currently planned:

- Parsing of SEI
- Parsing of VUI
- Parsing of H.265 bitstreams

# Usage

    h26x-extractor [options] <input-file>...

You can pass the `-v` flag to enable verbose output, e.g. the following. You will get, for each NAL unit:

- The byte position range
- The offset from the start of the stream
- The overall length including start code
- The type (also translated in plaintext)
- Its content in raw bytes, encoded as hex
- Its RBSP content
- A table with its content decoded, if supported

Example:

    NALU bytepos:   [0, 28]
    NALU offset:    0 Bytes
    NALU length:    29 Bytes (including start code)
    NALU type:      7 (Sequence parameter set)
    NALU bytes:     0x0000000167f4000d919b28283f6022000003000200000300641e28532c
    NALU RBSP:      0xf4000d919b28283f602200000002000000641e28532c

    SPS (payload size: 22.0 Bytes)
    +--------------------------------------+---------+
    | field                                | value   |
    +======================================+=========+
    | constraint_set0_flag                 | 0       |
    +--------------------------------------+---------+
    | constraint_set1_flag                 | 0       |
    +--------------------------------------+---------+
    ....

# Programmatic usage

You can also use this library in your code, e.g.:

```python
from h26x_extractor.h26x_parser import H26xParser

H26xParser.set_callback("nalu", do_something)
H26xParser.parse()
def do_something(bytes):
    # do something with the NALU bytes
```

The callback is called for each type of info found. Valid callbacks are:

- `sps`
- `pps`
- `slice`
- `aud`
- `nalu`

The raw data for all callbacks includes the RBSP.

You can also call the `nalutypes` classes to decode the individual fields, e.g. `nalutypes.SPS`:

```python
from h26x_extractor.h26x_parser import H26xParser
from h26x_extractor.nalutypes import SPS

H26xParser.set_callback("sps", parse_sps)
H26xParser.parse()
def parse_sps(bytes):
    sps = SPS(bytes)
    sps.print_verbose()
```

# License

The MIT License (MIT)

Copyright (c) 2017-2020 Werner Robitza

Permission is hereby granted, free of charge, to any person obtaining a
copy of this software and associated documentation files (the
"Software"), to deal in the Software without restriction, including
without limitation the rights to use, copy, modify, merge, publish,
distribute, sublicense, and/or sell copies of the Software, and to
permit persons to whom the Software is furnished to do so, subject to
the following conditions:

The above copyright notice and this permission notice shall be included
in all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS
OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF
MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT.
IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY
CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT,
TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE
SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
