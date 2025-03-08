# Changelog


## v0.10.0 (2025-03-08)

* Bump version to 0.10.0.

* Update readme.

* Add temporal SVC parse, fix vui parse (#10)

  * [feat] add h264 temporal SVC parse

  * [fix] fix vui parse

* Fix PEP 625 naming.

* Link to API docs.


## v0.9.0 (2025-02-05)

* Bump version to 0.9.0.

* Remove irrelevant comment.

* Update copyright, readme.

* Update tests.

* Drop python 3.8 support.

* Refactor and finish the parser implementation (#9)

  * feat: refactor and finish the parser implementation

  * Complete SPS, PPS implementation
  * Factorize and complete slice parsing in CodedSlice class
  * Move verbose support in the main process
  * add option --verbose-types to display only some NALU types

  * feat: add set_allcallbacks helper function

  * Add set_allcallbacks helper function to set all callbacks in one go
  * Change the order of callback arguments to have the nalu first
  * Fix a typo in h26x_parser.py

  * test: update test.py

  * docs(README): update README

* Update README.

* [feat] add parse VUI in SPS for h264 (#8)


## v0.8.1 (2023-01-08)

* Bump version to 0.8.1.

* Organize imports.

* Update module structure, readme.


## v0.8.0 (2021-11-12)

* Bump version to 0.8.0.

* Remove unneeded imports.

* Rename test dir.

* Apply formatting with black.

* Parse as bytearray instead of BitStream.

* Update copyright year.

* Add requirements.txt.

* Update badge link.

* Update README.


## v0.7.0 (2021-03-10)

* Bump version to 0.7.0.

* Add python_requires to setup.py.

* Remove release script.


## v0.6 (2021-03-06)

* Bump version to 0.6.

* Switch version to string.

* Format setup.py and switch to markdown.

* Update badge URL.


## v0.5 (2020-12-30)

* Bump version to 0.5.

* Apply formatting.

* Rm python 2.x support, README fixes.

* Fix frame_crop_left_offset typo (#5)

* Formatting.

* Import local package for tests.

* Add pypi badge.

* Add missing gitchangelog template.


## v0.4 (2020-04-12)

* Bump version to 0.4.

* Update release script.

* Update readme.

* H26x_extractor: add deeper slice_header parsing (#4)

  Includes:
  * passing the SPS and PPS NALUs to CodedSliceIDR and CodedSliceNonIDR
    (which need them to go further)
  * adding an optional concept of order in the verbose printing, so that
    NALU parameters are printed in the order they are parsed
  * implementing ordering in SPS, PPS, and CodedSliceIDR NALUs
  * fix on the SPS parser based on profile_idc values, per 2016-02
    standard (Section 7.3.2.1.1, page 44). Note in particular that the if
    loop does not include value 144
  * fix minor type (s/slice_gropu_change_rate_minus1/slice_group_change_rate_minus1/)

  Tested:
  ```
  $ h26x-extractor -v file.264
  ...
  SPS (payload size: 21.0 Bytes)
  +--------------------------------------+---------+
  | field                                | value   |
  +======================================+=========+
  | profile_idc                          | 66      |
  +--------------------------------------+---------+
  | constraint_set0_flag                 | 1       |
  +--------------------------------------+---------+
  | constraint_set1_flag                 | 1       |
  +--------------------------------------+---------+
  | constraint_set2_flag                 | 0       |
  +--------------------------------------+---------+
  | constraint_set3_flag                 | 0       |
  +--------------------------------------+---------+
  ...
  NALU type:  5 (Coded slice of an IDR picture)
  NALU bytes: 0x000000016588841afffffc2f14000416fd78e06380de6a1306bb224a722233e54ffa7cb9526c188ed1189699e7c6fd1a2307f757de5c3fca2f3d22b7fc667ccb6ff6b6a8dabb515b59fe53f8a7d83a8beb6ff17988adbfde818bdf2dafc5e7a2b5fde4a0bca4156137f8ceadff19bd5bfe233e152fbefbefbe2fab6dfe...
  NALU RBSP:  0x88841afffffc2f14000416fd78e06380de6a1306bb224a722233e54ffa7cb9526c188ed1189699e7c6fd1a2307f757de5c3fca2f3d22b7fc667ccb6ff6b6a8dabb515b59fe53f8a7d83a8beb6ff17988adbfde818bdf2dafc5e7a2b5fde4a0bca4156137f8ceadff19bd5bfe233e152fbefbefbe2fab6dfed6d62d6ad7...

  CodedSliceIDR (payload size: 4538.0 Bytes)
  +----------------------+---------+
  | field                | value   |
  +======================+=========+
  | first_mb_in_slice    | 0       |
  +----------------------+---------+
  | slice_type           | 7       |
  +----------------------+---------+
  | slice_type_clear     | I       |
  +----------------------+---------+
  | pic_parameter_set_id | 0       |
  +----------------------+---------+
  | frame_num            | 0       |
  +----------------------+---------+
  | idr_pic_id           | 0       |
  ...
  ```

* Fix offset-by-one (#3)

  * h26x-extractor: add a simple parsing test

  Needed to refactor the parser constructor in order to allow testing
  binary blobs.

  Tested:

  Before the AUD fix patch:

  ```
  $ ./tests/simple_parsing.py

  ========================================================================================================

  NALU bytepos: [0, 5]
  NALU offset:  0 Bytes
  NALU length:  6 Bytes (including start code)
  NALU type:  9 (Access unit delimiter)
  NALU bytes: 0x000000010910
  NALU RBSP:

  E
  ======================================================================
  ERROR: testAUDParser (__main__.ParsingTest)
  Simple AUD parsing.
  ----------------------------------------------------------------------
  Traceback (most recent call last):
    File "./tests/simple_parsing.py", line 17, in testAUDParser
      ex.parse()
    File "/usr/local/lib/python3.7/site-packages/h26x_extractor-0.3-py3.7.egg/h26x_extractor/h26x_parser.py", line 209, in parse
      aud = nalutypes.AUD(rbsp_payload, self.verbose)
    File "/usr/local/lib/python3.7/site-packages/h26x_extractor-0.3-py3.7.egg/h26x_extractor/nalutypes.py", line 120, in __init__
      self.primary_pic_type = self.s.read('uint:3')
    File "/usr/lib/python3.7/site-packages/bitstring.py", line 3902, in read
      value, self._pos = self._readtoken(name, self._pos, length)
    File "/usr/lib/python3.7/site-packages/bitstring.py", line 2016, in _readtoken
      "Tried to read {0} bits when only {1} available.".format(int(length), self.length - pos))
  bitstring.ReadError: Reading off the end of the data. Tried to read 3 bits when only 0 available.

  ----------------------------------------------------------------------
  Ran 1 test in 0.003s

  FAILED (errors=1)
  ```

  After the AUD fix patch:

  ```
  $ ./tests/simple_parsing.py

  ========================================================================================================

  NALU bytepos: [0, 5]
  NALU offset:  0 Bytes
  NALU length:  6 Bytes (including start code)
  NALU type:  9 (Access unit delimiter)
  NALU bytes: 0x000000010910
  NALU RBSP:  0x10

  AUD (payload size: 1.0 Bytes)
  +------------------+---------+
  | field            |   value |
  +==================+=========+
  | primary_pic_type |       0 |
  +------------------+---------+
  .
  ----------------------------------------------------------------------
  Ran 1 test in 0.001s

  OK
  ```

  * h26x_extractor: fix offset-by-1 in NALU parser

  Tested:

  Before the AUD fix patch:

  ```
  $ ./tests/simple_parsing.py

  ========================================================================================================

  NALU bytepos: [0, 5]
  NALU offset:  0 Bytes
  NALU length:  6 Bytes (including start code)
  NALU type:  9 (Access unit delimiter)
  NALU bytes: 0x000000010910
  NALU RBSP:

  E
  ======================================================================
  ERROR: testAUDParser (__main__.ParsingTest)
  Simple AUD parsing.
  ----------------------------------------------------------------------
  Traceback (most recent call last):
    File "./tests/simple_parsing.py", line 17, in testAUDParser
      ex.parse()
    File "/usr/local/lib/python3.7/site-packages/h26x_extractor-0.3-py3.7.egg/h26x_extractor/h26x_parser.py", line 209, in parse
      aud = nalutypes.AUD(rbsp_payload, self.verbose)
    File "/usr/local/lib/python3.7/site-packages/h26x_extractor-0.3-py3.7.egg/h26x_extractor/nalutypes.py", line 120, in __init__
      self.primary_pic_type = self.s.read('uint:3')
    File "/usr/lib/python3.7/site-packages/bitstring.py", line 3902, in read
      value, self._pos = self._readtoken(name, self._pos, length)
    File "/usr/lib/python3.7/site-packages/bitstring.py", line 2016, in _readtoken
      "Tried to read {0} bits when only {1} available.".format(int(length), self.length - pos))
  bitstring.ReadError: Reading off the end of the data. Tried to read 3 bits when only 0 available.

  ----------------------------------------------------------------------
  Ran 1 test in 0.003s

  FAILED (errors=1)
  ```

  After the AUD fix patch:

  ```
  $ ./tests/simple_parsing.py

  ========================================================================================================

  NALU bytepos: [0, 5]
  NALU offset:  0 Bytes
  NALU length:  6 Bytes (including start code)
  NALU type:  9 (Access unit delimiter)
  NALU bytes: 0x000000010910
  NALU RBSP:  0x10

  AUD (payload size: 1.0 Bytes)
  +------------------+---------+
  | field            |   value |
  +==================+=========+
  | primary_pic_type |       0 |
  +------------------+---------+
  .
  ----------------------------------------------------------------------
  Ran 1 test in 0.001s

  OK
  ```


## v0.3 (2020-03-15)

* Bump version to 0.3.

* Add release script.

* Python 3.7 and 3.8.

* Rename changelog.


## v0.2 (2017-08-02)

* Many updates.


## v0.1 (2017-07-17)

* Initial commit.


