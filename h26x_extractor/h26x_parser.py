# h26x-parser.py
#
# The MIT License (MIT)
#
# Copyright (c) 2017 Werner Robitza
#
# Permission is hereby granted, free of charge, to any person obtaining a
# copy of this software and associated documentation files (the
# "Software"), to deal in the Software without restriction, including
# without limitation the rights to use, copy, modify, merge, publish,
# distribute, sublicense, and/or sell copies of the Software, and to
# permit persons to whom the Software is furnished to do so, subject to
# the following conditions:
#
# The above copyright notice and this permission notice shall be included
# in all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS
# OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF
# MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT.
# IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY
# CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT,
# TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE
# SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.>

import os

from bitstring import BitStream

from . import nalutypes


class H26xParser:
    """
    H.264 extractor for Annex B streams.
    """

    VALID_CALLBACKS = ["sps", "pps", "slice", "aud", "prefix", "nalu"]
    startCodePrefixShort = b"\x00\x00\x01"

    def __init__(self, f, use_bitstream=None, nalu_types=[]):
        """
        Create a new extractor for a .264/h264 file in Annex B format.

        f: input file
        use_bitstream: blob to use as bitstream (for testing)
        """
        if use_bitstream:
            self.byte_stream = bytearray.fromhex(use_bitstream)
        else:
            fn, ext = os.path.splitext(os.path.basename(f))
            valid_input_ext = [".264", ".h264"]
            # TODO: extend for H.265
            # valid_input_ext = ['.264', 'h264', '.265', '.h265']
            if ext not in valid_input_ext:
                raise RuntimeError("Valid input types: " + str(valid_input_ext))
            bitstream_file = f
            self.file = bitstream_file
            # Open file as byte stream:
            with open(bitstream_file, "rb") as f:
                self.byte_stream = f.read()
                self.byte_stream = bytearray(self.byte_stream)
        self.nalu_pos = self._get_nalu_pos()
        self.callbacks = {}

    def getRSBP(self, start, end):
        """
        Get the Rbsp from the NAL unit.
        """
        rbsp_enc = self.byte_stream[start:end]
        rbsp_dec = list()
        i = 0
        i_max = len(rbsp_enc)
        while i < i_max:
            if (i + 2 < i_max) and (rbsp_enc[i : i + 3] == b"\x00\x00\x03"):
                rbsp_dec.append(rbsp_enc[i])
                rbsp_dec.append(rbsp_enc[i + 1])
                i += 2
            else:
                rbsp_dec.append(rbsp_enc[i])
            i += 1
        return rbsp_dec

    def set_allcallbacks(self, fun):
        """
        Set a callback function for all types of NALUs.
        """
        for name in self.VALID_CALLBACKS:
            self.set_callback(name, fun)

    def set_callback(self, name, fun):
        """
        Set a callback function for raw data extracted. The function will be called with the raw
        bytes of the complete NALU. Valid callbacks are:

        - aud: for every AUD found
        - nalu: for every complete NAL unit found
        - sps: for every SPS NAL unit found
        - pps: for every PPS NAL unit found
        - slice: for every VCL NAL unit found with a slice in it (args: data, buffer_size, first_mb_in_slice)

        Raw data for all callbacks never includes the start code, but all the NAL headers, except
        for the "nalu" callback.
        """
        if name not in self.VALID_CALLBACKS:
            raise RuntimeError(
                name
                + " is not a valid callback. Choose one of "
                + str(self.VALID_CALLBACKS)
                + "."
            )
        if not callable(fun):
            raise RuntimeError(str(fun) + " is not a callable function")

        self.callbacks[name] = fun

    def __call(self, name, *args):
        """
        Calls a given callback, and silently skips if it is not implemented.

        name: name of the callback, e.g. "nalu", "aud", whatever
        args: will be expanded to the list of arguments, so you can call this with:
              self.__call("foo", arg1, arg2, ...)
        """
        if name not in self.VALID_CALLBACKS:
            return
        if name not in self.callbacks.keys():
            return
        else:
            self.callbacks[name](*args)

    def _get_nalu_pos(self):
        """
        Find the start codes in the input file.
        """
        size = self.byte_stream.__len__()
        nals = []
        retnals = []

        pos = 0
        while pos < size:
            is4bytes = False
            retpos = self.byte_stream.find(self.startCodePrefixShort, pos)
            if retpos == -1:
                break
            if self.byte_stream[retpos - 1] == 0:
                retpos -= 1
                is4bytes = True
            if is4bytes:
                pos = retpos + 4
            else:
                pos = retpos + 3
            val = hex(self.byte_stream[pos])
            val = "{0:#0{1}x}".format(self.byte_stream[pos], 4)
            bitField = BitStream(val)
            fb = bitField.read(1).uint
            nri = bitField.read(2).uint
            type = bitField.read(5).uint
            nals.append((pos, is4bytes, fb, nri, type))
        for i in range(0, len(nals) - 1):
            start = nals[i][0]
            if nals[i + 1][1]:
                end = nals[i + 1][0] - 5
            else:
                end = nals[i + 1][0] - 4
            retnals.append((start, end, nals[i][1], nals[i][2], nals[i][3], nals[i][4]))
        start = nals[-1][0]
        end = self.byte_stream.__len__() - 1
        retnals.append((start, end, nals[-1][1], nals[-1][2], nals[-1][3], nals[-1][4]))
        return retnals

    def parse(self):
        """
        Parse the bitstream and extract each NALU.
        Call the respective callbacks for each NALU type found.
        """

        self._get_nalu_pos()

        for idx, (start, end, is4bytes, fb, nri, type) in enumerate(self.nalu_pos):
            # print("NAL#%d: %d, %d, %d, %d, %d" % (idx, start, end, fb, nri, type))
            if is4bytes:
                _start = start - 4
            else:
                _start = start - 3

            rbsp_payload = self.getRSBP(start + 1, end + 1)

            # Parse the current NALU
            rbsp_payload_bs = BitStream(bytearray(rbsp_payload))
            if type == nalutypes.NAL_UNIT_TYPE_SPS:
                nalu_sps = nalutypes.SPS(rbsp_payload_bs)
                self.__call("sps", nalu_sps, type, _start, end)
            elif type == nalutypes.NAL_UNIT_TYPE_PPS:
                nalu_pps = nalutypes.PPS(rbsp_payload_bs)
                self.__call("pps", nalu_pps, type, _start, end)
            elif type == nalutypes.NAL_UNIT_TYPE_AUD:
                aud = nalutypes.AUD(rbsp_payload_bs)
                self.__call("aud", aud, type, _start, end)
            elif type in [nalutypes.NAL_UNIT_TYPE_CODED_SLICE_NON_IDR, nalutypes.NAL_UNIT_TYPE_CODED_SLICE_IDR, nalutypes.NAL_UNIT_TYPE_CODED_SLICE_AUX]:
                nalu_slice = nalutypes.CodedSlice(rbsp_payload_bs, nalu_sps, nalu_pps, type)
                self.__call("slice", nalu_slice, type, _start, end)
            elif type == nalutypes.NAL_UNIT_TYPE_PREFIX:
                nalu_prefix = nalutypes.Prefix(rbsp_payload_bs)
                self.__call("prefix", nalu_prefix, type, _start, end)
            else:
                other = nalutypes.NALU(rbsp_payload_bs)
                self.__call("nalu", other, type, _start, end)
