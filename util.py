from OCC.Core.TopoDS import TopoDS_Shape, TopoDS_Compound, TopoDS_Builder, topods
from OCC.Core.GeomProjLib import geomprojlib
from OCC.Core.BRep import BRep_Tool
from OCC.Core.BRepTools import breptools, BRepTools_WireExplorer
from OCC.Core.TopExp import TopExp_Explorer
from OCC.Core.TopAbs import TopAbs_FACE, TopAbs_WIRE, TopAbs_EDGE, TopAbs_VERTEX
from OCC.Core.gp import gp_Pln, gp_Pnt, gp_Dir
from OCC.Core.Geom import Geom_Plane
from OCC.Core.BRepBuilderAPI import BRepBuilderAPI_MakeFace, BRepBuilderAPI_MakeWire, BRepBuilderAPI_MakeEdge
from OCC.Core.ShapeFix import ShapeFix_Wire

from shapely.geometry import Polygon


def make_wire(edges):
    make_wire = BRepBuilderAPI_MakeWire()
    for e in edges:
        make_wire.Add(e)
    make_wire.Build()
    if make_wire.IsDone():
        wire = make_wire.Wire()
        return wire
    else:
        return None

    
def shape_to_polygons(shape):
    polygons = []
    exp1 = TopExp_Explorer(shape.geometry, TopAbs_FACE)
    polygon_extracted = False
    while exp1.More() and not polygon_extracted:
        face = exp1.Current()
        surface = BRep_Tool.Surface(face) 
        wire = breptools.OuterWire(face)
        fix = ShapeFix_Wire()
        fix.Load(wire)
        fix.Perform()
        #wire = fix.Wire()
        exp2 = BRepTools_WireExplorer(wire)
        points = []
        while exp2.More():
            vertex = exp2.CurrentVertex()
            pnt = BRep_Tool.Pnt(vertex)
            points.append([pnt.X(),pnt.Y()])
            exp2.Next()
        polygon = Polygon(points)
        if polygon.area > 0:# and polygon.is_valid:
            polygons.append(polygon)
            polygon_extracted = True
        exp1.Next()
    return polygons