import math
import unittest
import ifcopenshell
from georeference_ifc import get_mapconversion_crs, get_rotation, set_si_units, set_mapconversion_crs


class SimpleTest(unittest.TestCase):

    def test_ifc4(self):
        fn_input = 'ACT2BIM.ifc'
        ifc_file = ifcopenshell.open(fn_input)
        set_si_units(ifc_file)
        set_mapconversion_crs(ifc_file=ifc_file,
                              target_crs_epsg_code='EPSG:9897',
                              eastings=76670.0,
                              northings=77179.0,
                              orthogonal_height=293.7,
                              x_axis_abscissa=-0.325568154457152,
                              x_axis_ordinate=0.945518575599318,
                              scale=1.0)
        fn_output = 'ACT2BIM_georeferenced.ifc'
        ifc_file.write(fn_output)

        ifc_file = ifcopenshell.open(fn_output)
        mapconversion, crs = get_mapconversion_crs(ifc_file)
        assert math.isclose(mapconversion.Eastings, 76670.0)
        assert math.isclose(mapconversion.Northings, 77179.0)
        assert math.isclose(mapconversion.OrthogonalHeight, 293.7)
        rotation = get_rotation(mapconversion)
        assert math.isclose(rotation, 109.0)

    def test_ifc2x3(self):
        fn_input = 'Duplex_A_20110907.ifc'
        ifc_file = ifcopenshell.open(fn_input)
        set_si_units(ifc_file)
        set_mapconversion_crs(ifc_file=ifc_file,
                              target_crs_epsg_code='EPSG:2169',
                              eastings=76670.0,
                              northings=77179.0,
                              orthogonal_height=293.7,
                              x_axis_abscissa=0.325568154457152,
                              x_axis_ordinate=0.945518575599318,
                              scale=1.0)
        fn_output = 'Duplex_A_20110907_georeferenced.ifc'
        ifc_file.write(fn_output)

        ifc_file = ifcopenshell.open(fn_output)
        mapconversion, crs = get_mapconversion_crs(ifc_file)
        assert math.isclose(mapconversion.Eastings, 76670.0)
        assert math.isclose(mapconversion.Northings, 77179.0)
        assert math.isclose(mapconversion.OrthogonalHeight, 293.7)
        rotation = get_rotation(mapconversion)
        assert math.isclose(rotation, 71.0)


if __name__ == '__main__':
    unittest.main()
