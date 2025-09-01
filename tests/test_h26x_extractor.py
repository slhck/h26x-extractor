#!/usr/bin/env python3
import os
import sys
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from h26x_extractor import h26x_parser
from h26x_extractor.nalutypes import (
    NAL_UNIT_TYPE_CODED_SLICE_IDR,
    NAL_UNIT_TYPE_CODED_SLICE_NON_IDR,
    NAL_UNIT_TYPE_PPS,
    NAL_UNIT_TYPE_SEI,
    NAL_UNIT_TYPE_SPS,
)


class H264ParserTest(unittest.TestCase):
    def setUp(self):
        # Real H.264 stream data from the sample
        self.test_stream = (
            # SPS
            "000000016764000dacd94141fb011000000300100000030320f1429960"
            # PPS
            "0000000168ebe3cb22c0"
            # SEI (truncated for brevity)
            "0000010605ffffaadc45e9bde6d948b7"
            # IDR Slice (truncated)
            "0000016588840033fffef6ecbe053614"
        )
        self.parser = h26x_parser.H26xParser(None, use_bitstream=self.test_stream)

    def test_sps_parsing(self):
        """Test SPS parsing with real data"""

        def verify_sps(sps, type, start, end):
            self.assertEqual(type, NAL_UNIT_TYPE_SPS)
            # Verify key SPS fields from the sample output
            self.assertEqual(sps.profile_idc, 100)
            self.assertEqual(sps.level_idc, 13)
            self.assertEqual(sps.seq_parameter_set_id, 0)
            self.assertEqual(sps.chroma_format_idc, 1)
            self.assertEqual(sps.log2_max_frame_num_minus4, 0)
            self.assertEqual(sps.pic_order_cnt_type, 0)
            self.assertEqual(sps.log2_max_pic_order_cnt_lsb_minus4, 2)
            self.assertEqual(sps.num_ref_frames, 4)
            self.assertEqual(sps.pic_width_in_mbs_minus_1, 19)
            self.assertEqual(sps.pic_height_in_map_units_minus_1, 14)
            self.assertEqual(sps.frame_mbs_only_flag, 1)
            self.assertEqual(sps.direct_8x8_inference_flag, 1)
            self.assertEqual(sps.frame_cropping_flag, 0)
            self.assertEqual(sps.vui_parameters_present_flag, 1)

        self.parser.set_callback("sps", verify_sps)
        self.parser.parse()

    def test_pps_parsing(self):
        """Test PPS parsing with real data"""

        def verify_pps(pps, type, start, end):
            self.assertEqual(type, NAL_UNIT_TYPE_PPS)
            # Verify key PPS fields from the sample output
            self.assertEqual(pps.pic_parameter_set_id, 0)
            self.assertEqual(pps.seq_parameter_set_id, 0)
            self.assertEqual(pps.entropy_coding_mode_flag, 1)
            self.assertEqual(pps.pic_order_present_flag, 0)
            self.assertEqual(pps.num_slice_groups_minus1, 0)
            self.assertEqual(pps.num_ref_idx_l0_active_minus1, 2)
            self.assertEqual(pps.num_ref_idx_l1_active_minus1, 0)
            self.assertEqual(pps.weighted_pred_flag, 1)
            self.assertEqual(pps.weighted_bipred_idc, 2)
            self.assertEqual(pps.pic_init_qp_minus26, -3)
            self.assertEqual(pps.deblocking_filter_control_present_flag, 1)
            self.assertEqual(pps.transform_8x8_mode_flag, 1)

        self.parser.set_callback("pps", verify_pps)
        self.parser.parse()

    def test_idr_slice_parsing(self):
        """Test IDR slice parsing with real data"""

        def verify_slice(slice, type, start, end):
            if type != NAL_UNIT_TYPE_CODED_SLICE_IDR:
                return
            # Verify key slice fields from the sample output
            self.assertEqual(slice.first_mb_in_slice, 0)
            self.assertEqual(slice.slice_type, 7)
            self.assertEqual(slice.slice_type_str, "I")
            self.assertEqual(slice.pic_parameter_set_id, 0)
            self.assertEqual(slice.frame_num, 0)
            self.assertEqual(slice.idr_pic_id, 0)
            self.assertEqual(slice.pic_order_cnt_lsb, 0)
            self.assertEqual(slice.slice_qp_delta, -12)
            self.assertEqual(slice.disable_deblocking_filter_idc, 0)
            self.assertTrue(slice.is_idr)

        self.parser.set_callback("slice", verify_slice)
        self.parser.parse()

    def test_non_idr_slice_parsing(self):
        """Test non-IDR slice parsing with real data"""
        # Need to include SPS and PPS before the slice for proper parsing
        test_stream = (
            # SPS (from the sample)
            "000000016764000dacd94141fb011000000300100000030320f1429960"
            # PPS (from the sample)
            "0000000168ebe3cb22c0"
            # P-slice from the sample
            "00000001419a226c42bffe3885deb9a0e02ec93f6d972998046eb493be864470"
        )
        parser = h26x_parser.H26xParser(None, use_bitstream=test_stream)

        def verify_slice(slice, type, start, end):
            if type != NAL_UNIT_TYPE_CODED_SLICE_NON_IDR:
                return
            self.assertEqual(slice.first_mb_in_slice, 0)
            self.assertEqual(slice.slice_type, 5)
            self.assertEqual(slice.slice_type_str, "P")
            self.assertEqual(slice.frame_num, 1)
            self.assertEqual(slice.pic_order_cnt_lsb, 4)
            self.assertEqual(slice.slice_qp_delta, -10)
            self.assertFalse(slice.is_idr)

        parser.set_callback("slice", verify_slice)
        parser.parse()

    def test_rbsp_extraction(self):
        """Test RBSP extraction with emulation prevention bytes"""
        # Example with emulation prevention byte (0x000003)
        blob = "00000001670000039876"
        parser = h26x_parser.H26xParser(None, use_bitstream=blob)

        # Get RBSP from position after NAL header
        rbsp = parser.getRSBP(
            5, len(blob) // 2
        )  # divide by 2 because blob is hex string

        # Verify emulation prevention byte was removed
        expected = bytearray.fromhex("00009876")
        self.assertEqual(bytearray(rbsp), expected)

    def test_nalu_position_detection(self):
        """Test detection of NAL unit boundaries"""
        nalu_positions = self.parser._get_nalu_pos()

        # We should find 4 NAL units in our test stream
        self.assertEqual(len(nalu_positions), 4)

        # Verify NAL unit types in order
        expected_types = [
            NAL_UNIT_TYPE_SPS,
            NAL_UNIT_TYPE_PPS,
            NAL_UNIT_TYPE_SEI,
            NAL_UNIT_TYPE_CODED_SLICE_IDR,
        ]

        for pos, expected_type in zip(nalu_positions, expected_types):
            _, _, _, _, _, type = pos
            self.assertEqual(type, expected_type)


if __name__ == "__main__":
    unittest.main()
