# -*- coding: utf-8 -*-
"""
General saving / loading utilities
"""
import json
import datetime

DATE_FORMAT = "%Y%m%d %H:%M:%S"

def save_rois(rois, fh):
    output_dict = {}
    output_dict["Content"] = "ROI-Definitions for PyLocator"
    _add_current_date(output_dict)
    output_dict["Data"] = rois
    _save_structure_as_json(output_dict, fh)

def load_rois(fh):
    def check_sanity(rois):
        assert rois["Content"] == "ROI-Definitions for PyLocator"
        _assert_date_is_valid(rois)
        for roi in rois["Data"]:
            assert len(roi["color"]) == 3
            assert all([0 <= color_part <= 1 for color_part in roi["color"]])
            assert 0 <= roi["opacity"] <= 1
        
    rois = _load_json(fh)
    check_sanity(rois)
    return rois


# Helper methods ############################

def _save_structure_as_json(rois, fh):
    fh = _make_open_file(fh, "w")
    json.dump(rois, fh, indent=4)

def _load_json(fh):
    fh = _make_open_file(fh,"r")
    return json.load(fh)

def _make_open_file(fh, mode):
    if type(fh)==str:
        fh = open(fh,mode)
    return fh

def _add_current_date(dict_):
    dict_["Date"] = datetime.datetime.now().strftime(DATE_FORMAT)

def _assert_date_is_valid(rois):
    datetime_saved = datetime.datetime.strptime(rois["Date"], DATE_FORMAT)
    assert datetime_saved is not None