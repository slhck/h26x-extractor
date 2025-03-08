# h26x-extractor

[![PyPI version](https://img.shields.io/pypi/v/h26x-extractor.svg)](https://pypi.org/project/h26x-extractor)

Author: Werner Robitza, with contributions from @chemag, Paulo Sherring, Thomas Jammet.

Extracts NAL units from H.264 bitstreams and decodes their type and content, if supported.

⚠️ `h26x-extractor` is neither fast nor robust to bitstream errors. It's rather a playground for parsing bitstreams. Use with caution! This program is no longer maintained, PRs are welcome.

Contents:

- [Installation](#installation)
- [Status](#status)
- [Usage](#usage)
- [Programmatic usage (API)](#programmatic-usage-api)
- [API](#api)
- [Alternatives](#alternatives)

## Installation

Requirements: Python 3.9 or higher

Via pip:

    pip3 install h26x_extractor

## Status

Currently supported:

- Parsing of H.264 bitstreams
- Parsing of NALU
- Parsing of AUD
- Parsing of CodedSlice(s)
- Parsing of SPS
- Parsing of PPS
- Parsing of Prefix for Scalable Video Coding

Currently planned:

- Parsing of SEI
- Parsing of H.265 bitstreams

## Usage

If you installed the program via pip, you can run it directly:

    h26x-extractor [options] <input-file>...

Otherwise you can clone this repo and run it via:

    python3 -m h26x_extractor [options] <input-file>...

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

## Programmatic usage (API)

## API

This program has a simple API that can be used to integrate it into other Python programs.

For more information see the [API documentation](https://htmlpreview.github.io/?https://github.com/slhck/h26x-extractor/blob/master/docs/h26x_extractor.html).

Here is an example:

```python
from h26x_extractor.h26x_parser import H26xParser

def do_something(nalu):
    pass
    # do something with the NALU instance

H26xParser.set_callback("nalu", do_something)
H26xParser.parse()
```

The callback is called for each type of info found. Valid callbacks are:

- `sps`
- `pps`
- `slice`
- `aud`
- `nalu`
- `prefix`

The callback returns an instance of the NALU type. You can access the `s` property to get the whole data including the RBSP.
You can use the `set_allcallbacks` method to set callbacks for all types.

You can also call the `nalutypes` classes to decode the individual fields, e.g. `nalutypes.SPS`:

```python
from h26x_extractor.nalutypes import SPS
from bitstring import BitStream

nal_payload = "0x0000000167f4000d919b28283f6022000003000200000300641e28532c"
sps = SPS(BitStream(nal_payload))
sps.print_verbose()
```

See the `test/test.py` file for more examples.

## Alternatives

[h264bitstream](https://github.com/aizvorski/h264bitstream) is a proper H.264 parser.

FFmpeg can also parse bitstream data:

```
ffmpeg -i video.h264 -c copy -bsf:v trace_headers -f null - 2> output.txt
```

# License

The MIT License (MIT)

Copyright (c) 2017-2025 h26x-extractor contributors

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
