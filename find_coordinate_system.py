# Copyright (c) 2022 Juha Toivola
# Licensed under the terms of the MIT License

import arcpy
from datetime import datetime
import os
import re


class FindCoordinateSystemException(Exception):
    error_msg = ""

    def __init__(self, error_msg, *args):
        super().__init__(args)
        self.error_msg = error_msg

    def __str__(self):
        return 'Exception: ' + self.error_msg


if __name__ == '__main__':
    fc = arcpy.GetParameterAsText(0)
    is_geographic = arcpy.GetParameter(1)
    is_projected = arcpy.GetParameter(2)
    wc = arcpy.GetParameterAsText(3)

    if not is_geographic and not is_projected:
        err_msg = "Error - no coordinate system reference type selected - select geographic or projected or both"
        arcpy.AddError(err_msg)
        raise FindCoordinateSystemException(err_msg)

    sr_type = "ALL"

    if is_geographic and not is_projected:
        sr_type = "GCS"
    if not is_geographic and is_projected:
        sr_type = "PCS"

    if wc != "":
        srs = arcpy.ListSpatialReferences(wild_card=wc, spatial_reference_type=sr_type)
    else:
        srs = arcpy.ListSpatialReferences(spatial_reference_type=sr_type)

    aprx = arcpy.mp.ArcGISProject('CURRENT')

    active_map = aprx.activeMap

    add_to_map = False
    if active_map:
        add_to_map = True

    active_map_name = active_map.name

    aprx_map = aprx.listMaps(active_map_name)[0]

    desc = arcpy.Describe(fc)
    fc_name = re.sub(r'\W+', '_', desc.baseName)[0:10]

    now = datetime.now()

    out_gdb = fc_name + "_" + now.strftime("%d%b%Y_%H%M%S").lower() + ".gdb"

    project_dir = os.path.dirname(os.path.realpath(__file__))

    arcpy.management.CreateFileGDB(project_dir, out_gdb)

    for sr_full_name in srs:
        def_proj_sr = arcpy.SpatialReference(sr_full_name)
        def_proj_sr_name = re.sub(r'\W+', '_', def_proj_sr.name)
        out_fc = project_dir + "/" + out_gdb + "/" + fc_name + "_" + def_proj_sr_name
        arcpy.management.CopyFeatures(fc, out_fc)
        out_fc_def_proj = arcpy.management.DefineProjection(out_fc, def_proj_sr)
        if add_to_map:
            try:
                aprx_map.addDataFromPath(out_fc_def_proj)
            except:
                pass
