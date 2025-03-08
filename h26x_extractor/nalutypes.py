# nalutypes.py
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

from bitstring import BitStream
from tabulate import tabulate
import math

# NAL REF IDC codes
NAL_REF_IDC_PRIORITY_HIGHEST = 3
NAL_REF_IDC_PRIORITY_HIGH = 2
NAL_REF_IDC_PRIORITY_LOW = 1
NAL_REF_IDC_PRIORITY_DISPOSABLE = 0

# NAL unit type codes
NAL_UNIT_TYPE_UNSPECIFIED = 0  # Unspecified
NAL_UNIT_TYPE_CODED_SLICE_NON_IDR = 1  # Coded slice of a non-IDR picture
NAL_UNIT_TYPE_CODED_SLICE_DATA_PARTITION_A = 2  # Coded slice data partition A
NAL_UNIT_TYPE_CODED_SLICE_DATA_PARTITION_B = 3  # Coded slice data partition B
NAL_UNIT_TYPE_CODED_SLICE_DATA_PARTITION_C = 4  # Coded slice data partition C
NAL_UNIT_TYPE_CODED_SLICE_IDR = 5  # Coded slice of an IDR picture
NAL_UNIT_TYPE_SEI = 6  # Supplemental enhancement information (SEI)
NAL_UNIT_TYPE_SPS = 7  # Sequence parameter set
NAL_UNIT_TYPE_PPS = 8  # Picture parameter set
NAL_UNIT_TYPE_AUD = 9  # Access unit delimiter
NAL_UNIT_TYPE_END_OF_SEQUENCE = 10  # End of sequence
NAL_UNIT_TYPE_END_OF_STREAM = 11  # End of stream
NAL_UNIT_TYPE_FILLER = 12  # Filler data
NAL_UNIT_TYPE_SPS_EXT = 13  # Sequence parameter set extension
NAL_UNIT_TYPE_PREFIX = 14   # Prefix NAL unit, for Scalable video coding
# 15..18                                          # Reserved
NAL_UNIT_TYPE_CODED_SLICE_AUX = (
    19  # Coded slice of an auxiliary coded picture without partitioning
)
# 20..23                                          # Reserved
# 24..31                                          # Unspecified

# Slice types
P_SLICE = 0
B_SLICE = 1
I_SLICE = 2
SP_SLICE = 3
SI_SLICE = 4

def get_slice_type_str(slice_type_mod_5):
    """
    Simple helper to decode slice_type into a human-readable string.
    The H.264 spec has slice_type in the range 0..9, with the value mod 5 indicating:
    0 = P-slice, 1 = B-slice, 2 = I-slice, 3 = SP-slice, 4 = SI-slice
    If slice_type >= 5, it indicates an "all Intra" or "all P/B" variant.
    """
    mapping = {0: "P", 1: "B", 2: "I", 3: "SP", 4: "SI"}
    return mapping[slice_type_mod_5]

def get_description(nal_unit_type):
    """
    Returns a clear text description of a NALU type given as an integer
    """
    return {
        NAL_UNIT_TYPE_UNSPECIFIED: "Unspecified",
        NAL_UNIT_TYPE_CODED_SLICE_NON_IDR: "Coded slice of a non-IDR picture",
        NAL_UNIT_TYPE_CODED_SLICE_DATA_PARTITION_A: "Coded slice data partition A",
        NAL_UNIT_TYPE_CODED_SLICE_DATA_PARTITION_B: "Coded slice data partition B",
        NAL_UNIT_TYPE_CODED_SLICE_DATA_PARTITION_C: "Coded slice data partition C",
        NAL_UNIT_TYPE_CODED_SLICE_IDR: "Coded slice of an IDR picture",
        NAL_UNIT_TYPE_SEI: "Supplemental enhancement information (SEI)",
        NAL_UNIT_TYPE_SPS: "Sequence parameter set",
        NAL_UNIT_TYPE_PPS: "Picture parameter set",
        NAL_UNIT_TYPE_AUD: "Access unit delimiter",
        NAL_UNIT_TYPE_END_OF_SEQUENCE: "End of sequence",
        NAL_UNIT_TYPE_END_OF_STREAM: "End of stream",
        NAL_UNIT_TYPE_FILLER: "Filler data",
        NAL_UNIT_TYPE_SPS_EXT: "Sequence parameter set extension",
        NAL_UNIT_TYPE_PREFIX: "Prefix NAL unit, for Scalable video coding",
        NAL_UNIT_TYPE_CODED_SLICE_AUX: "Coded slice of an auxiliary coded picture without partitioning",
    }.get(nal_unit_type, "unknown")

def parse_scaling_list(bitreader, sizeOfScalingList):
    """
    Parse a scaling list of size 'sizeOfScalingList' (16 for 4x4, 64 for 8x8)
    according to H.264/AVC spec (7.3.2.1.1).

    :param bitreader: An object with a .read("se") method for reading signed Exp-Golomb.
    :param sizeOfScalingList: 16 (4x4) or 64 (8x8).
    :return: (scaling_list, use_default_scaling_matrix_flag)
    """

    scaling_list = []
    last_scale = 8
    next_scale = 8
    use_default_scaling_matrix_flag = 0

    for i in range(sizeOfScalingList):
        if next_scale != 0:
            delta_scale = bitreader.read("se")
            # ( +256 ) ensures we don't get a negative number modulo 256
            next_scale = (last_scale + delta_scale + 256) % 256

        # If nextScale becomes 0 at the very first element,
        # useDefaultScalingMatrixFlag = 1 (fall back to default matrix).
        if i == 0 and next_scale == 0:
            use_default_scaling_matrix_flag = 1
            break

        if next_scale == 0:
            scaling_list.append(last_scale)
        else:
            scaling_list.append(next_scale)
            last_scale = next_scale

    return scaling_list, use_default_scaling_matrix_flag

class NALU(object):
    """
    Class representing a NAL unit, to be initialized with its payload only.
    The type must be inferred from the NALU header, before initializing the NALU by its subclass.
    :param rbsp_bytes: Raw Byte Sequence Payload of the NALU (already de-emulated).
    :param order: Optional list of field names to print in a certain order in print_verbose().
    """

    def __init__(self, rbsp_bytes: BitStream, order=None):
        self.s = rbsp_bytes
        self.order = order

    def print_verbose(self):
        print(
            self.__class__.__name__
            + " (payload size: "
            + str(len(self.s) / 8)
            + " Bytes)"
        )
        to_print = []
        if self.order is not None:
            for key in self.order:
                if key in vars(self):
                    value = vars(self)[key]
                    to_print.append([key, value])
        for key, value in sorted(vars(self).items()):
            if key == "s" or key == "order":
                continue
            if self.order and key in self.order:
                continue
            to_print.append([key, value])
        print(tabulate(to_print, headers=["field", "value"], tablefmt="grid"))


class AUD(NALU):
    """
    Access Unit Delimiter
    """

    def __init__(self, rbsp_bytes):
        super(AUD, self).__init__(rbsp_bytes)

        self.primary_pic_type = self.s.read("uint:3")

class CodedSlice(NALU):
    """
    A unified coded slice parser for IDR and non-IDR pictures.
    Parses the slice header fully so we can accurately measure
    the slice header size and payload size.

    References:
      • ISO/IEC 14496-10, Section 7.3.3 (slice_header())
      • Additional references for scaling / reference list reordering, etc.
    """

    def __init__(self, rbsp_bytes, sps, pps, nal_unit_type):
        """
        :param rbsp_bytes: Raw Byte Sequence Payload of the slice (already de-emulated).
        :param sps:        Parsed SPS object (with relevant fields).
        :param pps:        Parsed PPS object (with relevant fields).
        :param nal_unit_type: The type of NAL (5 = IDR, 1 = non-IDR, etc.).
        """

        order = [
            "first_mb_in_slice", "slice_type", "slice_type_str",
            "pic_parameter_set_id", "colour_plane_id",
            "frame_num", "field_pic_flag", "bottom_field_flag",
            "idr_pic_id", "pic_order_cnt_lsb", "delta_pic_order_cnt_bottom",
            "delta_pic_order_cnt", "redundant_pic_cnt",
            "direct_spatial_mv_pred_flag", "num_ref_idx_active_override_flag",
            "num_ref_idx_l0_active_minus1", "num_ref_idx_l1_active_minus1",
            "slice_qp_delta", "disable_deblocking_filter_idc",
            "slice_alpha_c0_offset_div2", "slice_beta_offset_div2",
        ]
        super(CodedSlice, self).__init__(rbsp_bytes, order)

        # Detect if this is an IDR slice
        self.is_idr = (nal_unit_type == 5)

        # Track the start bit for slice header size
        start_bits = self.s.pos

        # 1) first_mb_in_slice, slice_type, pic_parameter_set_id
        self.first_mb_in_slice = self.s.read("ue")
        self.slice_type = self.s.read("ue")
        slice_type_mod_5 = self.slice_type % 5
        self.slice_type_str = get_slice_type_str(slice_type_mod_5)
        self.pic_parameter_set_id = self.s.read("ue")

        # 2) colour_plane_id (only if separate_colour_plane_flag == 1)
        self.colour_plane_id = None
        if getattr(sps, "separate_colour_plane_flag", 0) == 1:
            self.colour_plane_id = self.s.read("uint:2")

        # 3) frame_num (width = log2_max_frame_num_minus4 + 4)
        frame_num_bits = sps.log2_max_frame_num_minus4 + 4
        self.frame_num = self.s.read(f"uint:{frame_num_bits}")

        # 4) field_pic_flag / bottom_field_flag (if frame_mbs_only_flag == 0)
        self.field_pic_flag = None
        self.bottom_field_flag = None
        if not getattr(sps, "frame_mbs_only_flag", 1):
            self.field_pic_flag = self.s.read("uint:1")
            if self.field_pic_flag:
                self.bottom_field_flag = self.s.read("uint:1")

        # 5) idr_pic_id (only if IDR slice)
        self.idr_pic_id = None
        if self.is_idr:
            self.idr_pic_id = self.s.read("ue")

        # 6) pic_order_cnt
        self.pic_order_cnt_lsb = None
        self.delta_pic_order_cnt_bottom = None
        self.delta_pic_order_cnt = [None, None]

        if sps.pic_order_cnt_type == 0:
            # pic_order_cnt_lsb (width = log2_max_pic_order_cnt_lsb_minus4 + 4)
            poc_lsb_bits = sps.log2_max_pic_order_cnt_lsb_minus4 + 4
            self.pic_order_cnt_lsb = self.s.read(f"uint:{poc_lsb_bits}")

            # delta_pic_order_cnt_bottom if pps.pic_order_present_flag == 1
            if pps.pic_order_present_flag and not (self.field_pic_flag and self.bottom_field_flag):
                self.delta_pic_order_cnt_bottom = self.s.read("se")

        elif sps.pic_order_cnt_type == 1 and not getattr(sps, "delta_pic_order_always_zero_flag", 0):
            self.delta_pic_order_cnt[0] = self.s.read("se")
            if pps.pic_order_present_flag and not (self.field_pic_flag and self.bottom_field_flag):
                self.delta_pic_order_cnt[1] = self.s.read("se")

        # 7) redundant_pic_cnt (if pps.redundant_pic_cnt_present_flag)
        self.redundant_pic_cnt = None
        if getattr(pps, "redundant_pic_cnt_present_flag", 0) == 1:
            self.redundant_pic_cnt = self.s.read("ue")

        # 8) direct_spatial_mv_pred_flag (if slice_type is B-slice)
        self.direct_spatial_mv_pred_flag = None
        if slice_type_mod_5 == B_SLICE:
            self.direct_spatial_mv_pred_flag = self.s.read("uint:1")

        # 9) num_ref_idx_active_override_flag
        self.num_ref_idx_active_override_flag = None
        self.num_ref_idx_l0_active_minus1 = pps.num_ref_idx_l0_active_minus1
        self.num_ref_idx_l1_active_minus1 = pps.num_ref_idx_l1_active_minus1

        if slice_type_mod_5 in (P_SLICE, SP_SLICE, B_SLICE):
            self.num_ref_idx_active_override_flag = self.s.read("uint:1")
            if self.num_ref_idx_active_override_flag:
                self.num_ref_idx_l0_active_minus1 = self.s.read("ue")
                if slice_type_mod_5 == B_SLICE:
                    self.num_ref_idx_l1_active_minus1 = self.s.read("ue")

        # 10) ref_pic_list_modification (except I/ SI slices)
        if slice_type_mod_5 not in (I_SLICE, SI_SLICE):  # not I or SI
            self._parse_ref_pic_list_modification(slice_type_mod_5)

        # 11) pred_weight_table (if relevant)
        if ((slice_type_mod_5 in (P_SLICE, SP_SLICE) and pps.weighted_pred_flag) or
            (slice_type_mod_5 == B_SLICE and pps.weighted_bipred_idc == 1)):
            self._parse_pred_weight_table(sps, pps)

        # 12) dec_ref_pic_marking
        # If IDR => no_current_pic... else => adaptive_ref_pic_marking
        if nal_unit_type == 5:
            # IDR
            self.long_term_reference_flag = None
            self.no_output_of_prior_pics_flag = self.s.read("uint:1")
            self.long_term_reference_flag = self.s.read("uint:1")
        else:
            # Non-IDR
            self._parse_dec_ref_pic_marking()

        # 13) cabac_init_idc (if pps.entropy_coding_mode_flag == 1 and slice_type != I/ SI)
        if pps.entropy_coding_mode_flag == 1 and slice_type_mod_5 not in (I_SLICE, SI_SLICE):
            self.cabac_init_idc = self.s.read("ue")
        else:
            self.cabac_init_idc = None

        # 14) slice_qp_delta
        self.slice_qp_delta = self.s.read("se")

        # 15) if slice_type == SP or SI => parse slice_qs_delta
        if slice_type_mod_5 in (SP_SLICE, SI_SLICE):
            if slice_type_mod_5 == SP_SLICE:
                self.sp_for_switch_flag = self.s.read("uint:1")
            self.slice_qs_delta = self.s.read("se")  # For SP/SI slices
        else:
            self.slice_qs_delta = None

        # 16) deblocking_filter_control
        # If pps.deblocking_filter_control_present_flag, parse disable_deblocking_filter_idc, etc.
        if pps.deblocking_filter_control_present_flag:
            self.disable_deblocking_filter_idc = self.s.read("ue")
            if self.disable_deblocking_filter_idc != 1:
                self.slice_alpha_c0_offset_div2 = self.s.read("se")
                self.slice_beta_offset_div2 = self.s.read("se")
            else:
                self.slice_alpha_c0_offset_div2 = 0
                self.slice_beta_offset_div2 = 0
        else:
            # no fields
            self.disable_deblocking_filter_idc = 0
            self.slice_alpha_c0_offset_div2 = 0
            self.slice_beta_offset_div2 = 0

        # 17) slice_group_change_cycle
        if pps.num_slice_groups_minus1 > 0 and pps.slice_group_map_type in [3,4,5]:
            # We need to compute PicSizeInMapUnits from the SPS because it's not in the PPS when slice_group_map_type is 3,4,5
            pic_size_in_map_units = (sps.pic_width_in_mbs_minus_1 + 1) * (sps.pic_height_in_map_units_minus_1 + 1)
            if (not sps.frame_mbs_only_flag):
                pic_size_in_map_units *= 2

            max_value = pic_size_in_map_units // (pps.slice_group_change_rate_minus1 + 1)
            bits_for_slice_group_change_cycle = math.ceil(math.log2(max_value + 1))
            self.slice_group_change_cycle = self.s.read(f"uint:{bits_for_slice_group_change_cycle}")

        # End bit position of slice header
        end_bits = self.s.pos
        self._slice_header_size_bits = end_bits - start_bits

    def _parse_ref_pic_list_modification(self, slice_type_mod_5):
        self.ref_pic_list_modification_flag_l0 = self.s.read("uint:1")
        if self.ref_pic_list_modification_flag_l0:
            # should never loop more than num_ref_idx_l0_active_minus1 + 1 times
            index = 0
            for _ in range(self.num_ref_idx_l0_active_minus1 + 1):
                modification_of_pic_nums_idc = self.s.read("ue")
                if modification_of_pic_nums_idc == 3:
                    break
                self.s.read("ue")
                index += 1

        if slice_type_mod_5 == B_SLICE:
            self.ref_pic_list_modification_flag_l1 = self.s.read("uint:1")
            if self.ref_pic_list_modification_flag_l1:
                # should never loop more than num_ref_idx_l1_active_minus1 + 1 times
                index = 0
                for _ in range(self.num_ref_idx_l1_active_minus1 + 1):
                    modification_of_pic_nums_idc = self.s.read("ue")
                    if modification_of_pic_nums_idc == 3:
                        break
                    self.s.read("ue")
                    index += 1

    def _parse_pred_weight_table(self, sps, pps):
        """
        Minimal pred_weight_table parser, typically used if weighted_pred_flag or
        weighted_bipred_idc conditions are met.
        """
        self.luma_log2_weight_denom = self.s.read("ue")
        self.chroma_log2_weight_denom = None
        if sps.chroma_format_idc != 0:  # 0 => Monochrome
            self.chroma_log2_weight_denom = self.s.read("ue")

        # read luma/chroma weights for L0
        for _ in range(self.num_ref_idx_l0_active_minus1 + 1):
            luma_weight_l0_flag = self.s.read("uint:1")
            if luma_weight_l0_flag:
                _luma_weight = self.s.read("se")
                _luma_offset = self.s.read("se")
            if sps.chroma_format_idc != 0:
                chroma_weight_l0_flag = self.s.read("uint:1")
                if chroma_weight_l0_flag:
                    _chroma_weight_cb = self.s.read("se")
                    _chroma_offset_cb = self.s.read("se")
                    _chroma_weight_cr = self.s.read("se")
                    _chroma_offset_cr = self.s.read("se")

        # If B-slice, parse L1 weights
        if self.slice_type % 5 == 1:
            for _ in range(self.num_ref_idx_l1_active_minus1 + 1):
                luma_weight_l1_flag = self.s.read("uint:1")
                if luma_weight_l1_flag:
                    _luma_weight = self.s.read("se")
                    _luma_offset = self.s.read("se")
                if sps.chroma_format_idc != 0:
                    chroma_weight_l1_flag = self.s.read("uint:1")
                    if chroma_weight_l1_flag:
                        _chroma_weight_cb = self.s.read("se")
                        _chroma_offset_cb = self.s.read("se")
                        _chroma_weight_cr = self.s.read("se")
                        _chroma_offset_cr = self.s.read("se")

    def _parse_dec_ref_pic_marking(self):
        """
        dec_ref_pic_marking() for non-IDR slices (short-term / long-term references).
        """
        self.adaptive_ref_pic_marking_mode_flag = self.s.read("uint:1")
        if self.adaptive_ref_pic_marking_mode_flag:
            while self.s.pos < len(self.s):
                memory_management_control_operation = self.s.read("ue")
                if memory_management_control_operation == 0:
                    break
                if memory_management_control_operation in [1,3]:
                    _difference_of_pic_nums_minus1 = self.s.read("ue")
                if memory_management_control_operation == 2:
                    _long_term_pic_num = self.s.read("ue")
                if memory_management_control_operation in [3,6]:
                    _long_term_frame_idx = self.s.read("ue")
                if memory_management_control_operation == 4:
                    _max_long_term_frame_idx_plus1 = self.s.read("ue")

    def get_slice_header_size(self):
        """
        Returns the slice header size in **bytes**, rounded up from bits.
        """
        return (self._slice_header_size_bits + 7) // 8

    def get_slice_payload_size(self):
        """
        Returns the slice payload size in **bytes**, rounded up from bits.
        """
        return (len(self.s) - self._slice_header_size_bits) // 8

class SPS(NALU):
    """
    Sequence Parameter Set class
    """

    def __init__(self, rbsp_bytes):
        order = [
            "profile_idc",
            "constraint_set0_flag",
            "constraint_set1_flag",
            "constraint_set2_flag",
            "constraint_set3_flag",
            "constraint_set4_flag",
            "constraint_set5_flag",
            "reserved_zero_2bits",
            "level_idc",
            "seq_parameter_set_id",
            "chroma_format_idc",
            "separate_colour_plane_flag",
            "bit_depth_luma_minus8",
            "bit_depth_chroma_minus8",
            "qpprime_y_zero_transform_bypass_flag",
            "seq_scaling_matrix_present_flag",
            "log2_max_frame_num_minus4",
            "pic_order_cnt_type",
            "log2_max_pic_order_cnt_lsb_minus4",
            "delta_pic_order_always_zero_flag",
            "offset_for_non_ref_pic",
            "offset_for_top_to_bottom_filed",
            "num_ref_frames_in_pic_order_cnt_cycle",
            "offset_for_ref_frame",
            "num_ref_frames",
            "gaps_in_frame_num_value_allowed_flag",
            "pic_width_in_mbs_minus_1",
            "pic_height_in_map_units_minus_1",
            "frame_mbs_only_flag",
            "mb_adaptive_frame_field_flag",
            "direct_8x8_inference_flag",
            "frame_cropping_flag",
            "frame_crop_left_offset",
            "frame_crop_right_offset",
            "frame_crop_top_offset",
            "frame_crop_bottom_offset",
            "vui_parameters_present_flag",
        ]
        super(SPS, self).__init__(rbsp_bytes, order)

        # Initializers
        self.offset_for_ref_frame = []
        self.seq_scaling_matrix_present_flag = []
        self.scaling_lists = []

        self.profile_idc = self.s.read("uint:8")
        self.constraint_set0_flag = self.s.read("uint:1")
        self.constraint_set1_flag = self.s.read("uint:1")
        self.constraint_set2_flag = self.s.read("uint:1")
        self.constraint_set3_flag = self.s.read("uint:1")
        self.constraint_set4_flag = self.s.read("uint:1")
        self.constraint_set5_flag = self.s.read("uint:1")
        self.reserved_zero_2bits = self.s.read("uint:2")
        self.level_idc = self.s.read("uint:8")
        self.seq_parameter_set_id = self.s.read("ue")

        if self.profile_idc in [
            100, 110, 122, 244, 44, 83, 86, 118, 128, 138, 139, 134, 135
        ]:
            self.chroma_format_idc = self.s.read("ue")
            if self.chroma_format_idc == 3:
                self.separate_colour_plane_flag = self.s.read("uint:1")

            self.bit_depth_luma_minus8 = self.s.read("ue")
            self.bit_depth_chroma_minus8 = self.s.read("ue")
            self.qpprime_y_zero_transform_bypass_flag = self.s.read("uint:1")
            self.seq_scaling_matrix_present_flag = self.s.read("uint:1")

            if self.seq_scaling_matrix_present_flag:
                self.parse_scaling_matrix()

        self.log2_max_frame_num_minus4 = self.s.read("ue")
        self.pic_order_cnt_type = self.s.read("ue")

        if self.pic_order_cnt_type == 0:
            self.log2_max_pic_order_cnt_lsb_minus4 = self.s.read("ue")
        elif self.pic_order_cnt_type == 1:
            self.delta_pic_order_always_zero_flag = self.s.read("uint:1")
            self.offset_for_non_ref_pic = self.s.read("se")
            self.offset_for_top_to_bottom_filed = self.s.read("se")
            self.num_ref_frames_in_pic_order_cnt_cycle = self.s.read("ue")
            for _ in range(self.num_ref_frames_in_pic_order_cnt_cycle):
                self.offset_for_ref_frame.append(self.s.read("se"))

        self.num_ref_frames = self.s.read("ue")
        self.gaps_in_frame_num_value_allowed_flag = self.s.read("uint:1")
        self.pic_width_in_mbs_minus_1 = self.s.read("ue")
        self.pic_height_in_map_units_minus_1 = self.s.read("ue")
        self.frame_mbs_only_flag = self.s.read("uint:1")
        if not self.frame_mbs_only_flag:
            self.mb_adaptive_frame_field_flag = self.s.read("uint:1")
        self.direct_8x8_inference_flag = self.s.read("uint:1")
        self.frame_cropping_flag = self.s.read("uint:1")
        if self.frame_cropping_flag:
            self.frame_crop_left_offset = self.s.read("ue")
            self.frame_crop_right_offset = self.s.read("ue")
            self.frame_crop_top_offset = self.s.read("ue")
            self.frame_crop_bottom_offset = self.s.read("ue")

        self.vui_parameters_present_flag = self.s.read("uint:1")
        if self.vui_parameters_present_flag:
            self.parse_vui_parameters()

    def parse_scaling_matrix(self):
        """
        Parses the scaling matrix for SPS.
        """
        num_scaling_lists = 8 if self.chroma_format_idc == 3 else 6

        for i in range(num_scaling_lists):
            scaling_list_present = self.s.read("uint:1")
            if scaling_list_present:
                size_of_list = 16 if i < 6 else 64  # First 6 are 4x4, last 2 are 8x8
                scaling_list, _ = parse_scaling_list(self.s, size_of_list)
                self.scaling_lists.append(scaling_list)
            else:
                self.scaling_lists.append(None)  # Use default matrix

    def parse_vui_parameters(self):
        """
        Parses VUI parameters.
        """
        self.aspect_ratio_info_present_flag = self.s.read("uint:1")
        if self.aspect_ratio_info_present_flag:
            self.aspect_ratio_idc = self.s.read("uint:8")
            if self.aspect_ratio_idc == 255:  # Extended_SAR
                self.sar_width = self.s.read("uint:16")
                self.sar_height = self.s.read("uint:16")

        self.overscan_info_present_flag = self.s.read('uint:1')
        if self.overscan_info_present_flag:
            self.overscan_appropriate_flag = self.s.read('uint:1')
        self.video_signal_type_present_flag = self.s.read('uint:1')
        if self.video_signal_type_present_flag:
            self.video_format = self.s.read('uint:3')
            self.video_full_range_flag = self.s.read('uint:1')
            self.colour_description_present_flag = self.s.read('uint:1')
            if self.colour_description_present_flag:
                self.colour_primaries = self.s.read('uint:8')
                self.transfer_characteristics = self.s.read('uint:8')
                self.matrix_coefficients = self.s.read('uint:8')
        self.chroma_loc_info_present_flag = self.s.read('uint:1')
        if self.chroma_loc_info_present_flag:
            self.chroma_sample_loc_type_top_field = self.s.read('ue')
            self.chroma_sample_loc_type_bottom_field = self.s.read('ue')
        self.timing_info_present_flag = self.s.read("uint:1")
        if self.timing_info_present_flag:
            self.num_units_in_tick = self.s.read("uint:32")
            self.time_scale = self.s.read("uint:32")
            self.fixed_frame_rate_flag = self.s.read("uint:1")

        self.nal_hrd_parameters_present_flag = self.s.read("uint:1")
        if self.nal_hrd_parameters_present_flag:
            self.parse_hrd_parameters()

        self.vcl_hrd_parameters_present_flag = self.s.read('uint:1')
        if self.vcl_hrd_parameters_present_flag:
            self.parse_hrd_parameters()

        if self.nal_hrd_parameters_present_flag or self.vcl_hrd_parameters_present_flag:
            self.low_delay_hrd_flag = self.s.read('uint:1')
        self.pic_struct_present_flag = self.s.read('uint:1')
        self.bitstream_restriction_flag = self.s.read('uint:1')
        if self.bitstream_restriction_flag:
            self.motion_vectors_over_pic_boundaries_flag = self.s.read('uint:1')
            self.max_bytes_per_pic_denom = self.s.read('ue')
            self.max_bits_per_mb_denom = self.s.read('ue')
            self.log2_max_mv_length_horizontal = self.s.read('ue')
            self.log2_max_mv_length_vertical = self.s.read('ue')
            self.max_num_reorder_frames = self.s.read('ue')
            self.max_dec_frame_buffering = self.s.read('ue')

    def parse_hrd_parameters(self):
        """
        Parses HRD parameters.
        """
        self.cpb_cnt_minus1 = self.s.read("ue")
        self.bit_rate_scale = self.s.read("uint:4")
        self.cpb_size_scale = self.s.read("uint:4")

        self.bit_rate_value_minus1 = []
        self.cpb_size_value_minus1 = []
        self.cbr_flag = []

        for _ in range(self.cpb_cnt_minus1 + 1):
            self.bit_rate_value_minus1.append(self.s.read("ue"))
            self.cpb_size_value_minus1.append(self.s.read("ue"))
            self.cbr_flag.append(self.s.read("uint:1"))

        self.initial_cpb_removal_delay_length_minus1 = self.s.read("uint:5")
        self.cpb_removal_delay_length_minus1 = self.s.read("uint:5")
        self.dpb_output_delay_length_minus1 = self.s.read("uint:5")
        self.time_offset_length = self.s.read("uint:5")

class PPS(NALU):
    def __init__(self, rbsp_bytes):
        order = [
            "pic_parameter_set_id",
            "seq_parameter_set_id",
            "entropy_coding_mode_flag",
            "pic_order_present_flag",
            "num_slice_groups_minus1",
            "slice_group_map_type",
            "run_length_minus1",
            "top_left",
            "bottom_right",
            "slice_group_change_direction_flag",
            "slice_group_change_rate_minus1",
            "pic_size_in_map_units_minus1",
            "slice_group_id",
            "num_ref_idx_l0_active_minus1",
            "num_ref_idx_l1_active_minus1",
            "weighted_pred_flag",
            "weighted_bipred_idc",
            "pic_init_qp_minus26",
            "pic_init_qs_minus26",
            "chroma_qp_index_offset",
            "deblocking_filter_control_present_flag",
            "constrained_intra_pred_flag",
            "redundant_pic_cnt_present_flag",
            "transform_8x8_mode_flag",
            "pic_scaling_matrix_present_flag",
            "pic_scaling_list_present_flag",
            "second_chroma_qp_index_offset",
        ]
        super(PPS, self).__init__(rbsp_bytes, order)

        # --- Mandatory fields ---
        self.pic_parameter_set_id = self.s.read("ue")
        self.seq_parameter_set_id = self.s.read("ue")
        self.entropy_coding_mode_flag = self.s.read("uint:1")
        self.pic_order_present_flag = self.s.read("uint:1")

        self.num_slice_groups_minus1 = self.s.read("ue")
        if self.num_slice_groups_minus1 > 0:
            self.slice_group_map_type = self.s.read("ue")

            if self.slice_group_map_type == 0:
                self.run_length_minus1 = []
                for i_group in range(self.num_slice_groups_minus1 + 1):
                    self.run_length_minus1.append(self.s.read("ue"))

            elif self.slice_group_map_type == 2:
                self.top_left = []
                self.bottom_right = []
                for i_group in range(self.num_slice_groups_minus1):
                    self.top_left.append(self.s.read("ue"))
                    self.bottom_right.append(self.s.read("ue"))

            elif self.slice_group_map_type in [3, 4, 5]:
                self.slice_group_change_direction_flag = self.s.read("uint:1")
                self.slice_group_change_rate_minus1 = self.s.read("ue")

            elif self.slice_group_map_type == 6:
                self.pic_size_in_map_units_minus1 = self.s.read("ue")
                # slice_group_id uses ceil(log2(num_slice_groups_minus1 + 1)) bits per entry
                bits_for_slice_group_id = int(math.ceil(math.log2(self.num_slice_groups_minus1 + 1)))
                self.slice_group_id = []
                for _ in range(self.pic_size_in_map_units_minus1 + 1):
                    self.slice_group_id.append(
                        self.s.read(f"uint:{bits_for_slice_group_id}")
                    )
        else:
            # If num_slice_groups_minus1 == 0, there's only one slice group
            self.slice_group_map_type = 0
            self.run_length_minus1 = []
            self.top_left = []
            self.bottom_right = []
            self.slice_group_id = []

        self.num_ref_idx_l0_active_minus1 = self.s.read("ue")
        self.num_ref_idx_l1_active_minus1 = self.s.read("ue")
        self.weighted_pred_flag = self.s.read("uint:1")
        self.weighted_bipred_idc = self.s.read("uint:2")

        self.pic_init_qp_minus26 = self.s.read("se")
        self.pic_init_qs_minus26 = self.s.read("se")
        self.chroma_qp_index_offset = self.s.read("se")

        self.deblocking_filter_control_present_flag = self.s.read("uint:1")
        self.constrained_intra_pred_flag = self.s.read("uint:1")
        self.redundant_pic_cnt_present_flag = self.s.read("uint:1")

        # --- Optional fields (High Profile, etc.): parse if there's more data ---
        self.transform_8x8_mode_flag = None
        self.pic_scaling_matrix_present_flag = None
        self.pic_scaling_list_present_flag = []
        self.second_chroma_qp_index_offset = None

        # The specification says: if(more_rbsp_data()) { ... }
        # (i.e., additional bits in PPS for High Profile / extended features)
        if self.s.pos <= len(self.s) - 8:
            self.transform_8x8_mode_flag = self.s.read("uint:1")
            self.pic_scaling_matrix_present_flag = self.s.read("uint:1")

            # If scaling matrices are present, parse them
            if self.pic_scaling_matrix_present_flag:
                # According to the standard:
                # Number of scaling lists = 6 + 2*transform_8x8_mode_flag
                num_scaling_lists = 6 + (2 if self.transform_8x8_mode_flag == 1 else 0)

                for i_list in range(num_scaling_lists):
                    present = self.s.read("uint:1")
                    self.pic_scaling_list_present_flag.append(present)
                    if present:
                        parse_scaling_list(self.s, 16 if i_list < 6 else 64)
                        pass

            # After parsing (optionally) the scaling matrices,
            # read the second_chroma_qp_index_offset
            self.second_chroma_qp_index_offset = self.s.read("se")

        # Optionally handle rbsp_trailing_bits() if your parser requires it
        # e.g. self.s.rbsp_trailing_bits()

class Prefix(NALU):
    """
    Prefix NAL unit, for Scalable video coding.
    """

    def __init__(self, rbsp_bytes):
        order = [
            "svc_extension_flag",
            "idr_flag",
            "priority_id",
            "no_inter_layer_pred_flag",
            "dependency_id",
            "quality_id",
            "temporal_id",
            "use_ref_base_pic_flag",
            "discardable_flag",
            "output_flag",
            "reserved_three_2bits",
        ]
        super(Prefix, self).__init__(rbsp_bytes, order)

        self.svc_extension_flag = self.s.read("uint:1")
        if self.svc_extension_flag:
            self.idr_flag = self.s.read("uint:1")
            self.priority_id = self.s.read("uint:6")
            self.no_inter_layer_pred_flag = self.s.read("uint:1")   # shall be equal to 1 in prefix NAL units
            self.dependency_id = self.s.read("uint:3")              # shall be equal to 0 in prefix NAL units
            self.quality_id = self.s.read("uint:4")                 # shall be equal to 0 in prefix NAL units
            self.temporal_id = self.s.read("uint:3")
            self.use_ref_base_pic_flag = self.s.read("uint:1")
            self.discardable_flag = self.s.read("uint:1")
            self.output_flag = self.s.read("uint:1")
            self.reserved_three_2bits = self.s.read("uint:2")       # shall be equal to 3
