# How to georeference an IFC file

[![Binder](https://mybinder.org/badge_logo.svg)](https://mybinder.org/v2/gh/stijngoedertier/georeference-ifc/master?labpath=how-to-georeference-ifc-file.ipynb)

# How to georeference a BIM model

IFC is an open standard for exchanging Building Information Models (BIM).
This notebook shows how IFC files can be georeferenced by providing **7 parameters** that are part of the IFC standard but are usually omitted.
These parameters make it easier to **combine BIM and geospatial data** (e.g. cadastral parcel data, 3D city models, point cloud data, or a digital elevation model) and enable use cases such as urban planning, evaluation of building permits or asset management.

## The problem
One of the impediments to the automated processing of IFC data is the fact that georeferencing information is not *explicitly* included in IFC information exchanges. Two scenarios are possible:
1. **Local reference system**: in most construction projects, the partners share a common *local* reference system, which is defined as a local origin and axis orientation. The local origin is often a conspicuous point near the construction site and the axis orientation is often chosen for convenience (e.g. along the axis of the main construction). Although the geolocation of this local reference system is known to the partners, there is usually no information about it in the IFC file.
1. **Geospatial reference system**: In other construction projects, the partners exchange IFC files in a standard projected reference system used by land surveyors or geospatial data (for example [EPSG:2169](https://epsg.io/2169) Luxembourg).  Although this information is known to the partners in the project, it is often left implicit in the IFC file thus inhibiting the possibility for automated processing.

## The solution
In both scenarios, the georeferencing information can be made explicit by using the **IfcProjectedCRS** and **IfcMapConversion** entities from the [IFC4 standard](https://standards.buildingsmart.org/IFC/RELEASE/IFC4/ADD2_TC1/HTML/schema/templates/project-global-positioning.htm). The former allows specifying a recognized, target coordinate reference system (CRS). The latter can be used to specify the coordinate transformation needed to convert coordinates from the project CRS to the specified target CRS. As depicted in the diagram below from the IFC standard, these ifc entities are directly related to the IfcProject (a subclass of IfcContext) entity.

[![BuildingSMART IFC4](https://standards.buildingsmart.org/IFC/RELEASE/IFC4/ADD2_TC1/HTML/schema/templates/diagrams/project-global-positioning.png)](https://standards.buildingsmart.org/IFC/RELEASE/IFC4/ADD2_TC1/HTML/schema/templates/project-global-positioning.htm)

[IfcProjectedCRS](https://standards.buildingsmart.org/IFC/RELEASE/IFC4/ADD2_TC1/HTML/schema/ifcrepresentationresource/lexical/ifcprojectedcrs.htm) allows specifying a target projected coordinate reference system. The most relevant attribute is the name of the reference system:
* **IfcProjectedCRS.Name**: According to the IFC4 specification, the name shall be taken from the list recognized by the European Petroleum Survey Group EPSG and should be qualified by the EPSG name space, for example as '[EPSG:2169](https://epsg.io/2169)'. In case the EPSG registry includes a vertical datum for the coordinate reference system - as is the case for our example - no other properties need to be provided.

[IfcMapConversion](https://standards.buildingsmart.org/IFC/RELEASE/IFC4/ADD2_TC1/HTML/schema/ifcrepresentationresource/lexical/ifcmapconversion.htm) provides information on how the reference system of the IFC file can be converted into the reference system indicated by IfcProjectedCRS. It contains information on the required coordinate translation, rotation, and scaling:
* **IfcMapConversion.Eastings, IfcMapConversion.Northings, IfcMapConversion.OrthogonalHeight** indicate the position of the origin of the local reference system used in the IFC file in terms of the indicated IfcProjectedCRS. Together, they define the coordinate *translation* needed to convert the *origin* of the local project CRS into the origin of the target geospatial CRS.
* **IfcMapConversion. XAxisAbscissa and IfcMapConversion.XAxisOrdinate** together define the angle of *rotation* required to convert the axis orientation of the local reference system, into the axis orientation of the indicated coordinate reference system.
* **IfcMapConversion.Scale** indicates the conversion factor to be used, to convert the units of the local, engineering coordinate system into the units of the target CRS (often expressed in metres). If omitted, the value of 1.0 is assumed.

In IFC2x3 the same information can be included by using equivalent property sets 'ePset_MapConversion' and 'ePSet_ProjectedCRS' on IfcSite as proposed by BuildingSMART Australasia in their paper '[User guide for georeferencing in IFC](https://www.buildingsmart.org/wp-content/uploads/2020/02/User-Guide-for-Geo-referencing-in-IFC-v2.0.pdf)'.

Recent versions of [Revit](https://wiki.osarch.org/index.php?title=Revit_IFC_geolocation) (with the [revit-ifc plugin](https://github.com/Autodesk/revit-ifc)) and [ArchiCAD](https://wiki.osarch.org/index.php?title=ArchiCAD_IFC_geolocation) make it possible export this IFC information. See the osarch.org wiki or the [blog post](https://thinkmoult.com/ifc-coordinate-reference-systems-and-revit.html) by Dion Moult for a detailed guide on georeferencing in Revit.

## Add georeference information with IfcOpenShell-python

[IfcOpenShell-python](https://github.com/IfcOpenShell/IfcOpenShell) is an open-source library for working with IFC files. Let's use [IfcOpenShell-python](https://github.com/IfcOpenShell/IfcOpenShell) to write or read georeferencing information from an IFC file.
For this purpose, we have taken the [Duplex Apartment](https://github.com/buildingSMART/Sample-Test-Files/tree/master/IFC%202x3/Duplex%20Apartment) IFC file by BuildingSMART International.

### Visualize the spaces in the IFC file

First, let's visualize the rooms (IfcSpace) in the IFC file using a threeJS viewer. This filter on IfcSpace objects is relevant because we usually do not need all the detail in the IFC file when combining it with GIS data. The viewer shows the XYZ axis and origin of the local reference system. Its origin is located very near the construction site.




```python
from math import atan2, degrees
import ifcopenshell
import ifcopenshell.geom
from OCC.Display.WebGl.jupyter_renderer import JupyterRenderer, format_color

settings = ifcopenshell.geom.settings()
settings.set(settings.USE_WORLD_COORDS, True)
settings.set(settings.USE_BREP_DATA, True)
settings.set(settings.USE_PYTHON_OPENCASCADE, True)

fn = './Duplex_A_20110907.ifc'
ifc_file = ifcopenshell.open(fn)

threejs_renderer = JupyterRenderer(size=(500, 500))
spaces = ifc_file.by_type("IfcSpace")

for space in spaces:
    if space.Representation is not None:
        shape = ifcopenshell.geom.create_shape(settings, inst=space)
        r,g,b,alpha = shape.styles[0]
        color = format_color(int(abs(r)*255), int(abs(g)*255), int(abs(b)*255))
        threejs_renderer.DisplayShape(shape.geometry, shape_color = color, transparency=True, opacity=alpha, render_edges=True)

threejs_renderer.Display()
```

    /opt/conda/lib/python3.9/site-packages/jupyter_client/session.py:716: UserWarning: Message serialization failed with:
    Out of range float values are not JSON compliant
    Supporting this message is deprecated in jupyter-client 7, please make sure your message is JSON-compliant
      content = self.pack(content)



    HBox(children=(VBox(children=(HBox(children=(Checkbox(value=True, description='Axes', layout=Layout(height='au…


### Write georeference parameters
Now, let's use IfcOpenShell-python to add geoloation information to the IFC file. As the [Duplex_A_20110907.ifc](./Duplex_A_20110907.ifc) file uses the IFC2x3 schema, we need to add the 'ePSet_MapConversion' and 'ePSet_ProjectedCRS' property sets to the IfcSite object. We will use the OSarch.org [IFC propertyset template](https://wiki.osarch.org/index.php?title=IFC_geolocation) provided on their website.


```python
import ifcopenshell
import ifcopenshell.api
import ifcopenshell.util.element
from ifcopenshell.util.element import get_psets

ifc = ifcopenshell.open('./IFC2X3_Geolocation.ifc')
map_conversion_template = [t for t in ifc.by_type('IfcPropertySetTemplate') if t.Name == 'EPset_MapConversion'][0]
crs_template = [t for t in ifc.by_type('IfcPropertySetTemplate') if t.Name == 'EPset_MapConversion'][0]

site = ifc_file.by_type("IfcSite")[0] # we assume that the IfcProject only has one IfcSite entity.
pset = ifcopenshell.api.run("pset.add_pset", ifc_file, product=site, name="ePSet_MapConversion")
ifcopenshell.api.run("pset.edit_pset", ifc_file, pset=pset, properties={'Eastings': 76670.0, 
                                                                        'Northings': 77179.0, 
                                                                        'OrthogonalHeight': 293.700012207031, 
                                                                        'XAxisAbscissa': 0.325568154457152, 
                                                                        'XAxisOrdinate': 0.945518575599318, 
                                                                        'Scale': 1.0}, 
                     pset_template=map_conversion_template)
pset = ifcopenshell.api.run("pset.add_pset", ifc_file, product=site, name="ePSet_ProjectedCRS")
ifcopenshell.api.run("pset.edit_pset", ifc_file, pset=pset, properties={'Name': 'EPSG:2169'}, 
                     pset_template=crs_template)
psets = get_psets(site)
print(psets)
```

    {'ePSet_MapConversion': {'Eastings': 76670.0, 'Northings': 77179.0, 'OrthogonalHeight': 293.700012207031, 'XAxisAbscissa': 0.325568154457152, 'XAxisOrdinate': 0.945518575599318, 'Scale': 1.0}, 'ePSet_ProjectedCRS': {'Name': 'EPSG:2169'}}


### Read georeference information

The below function `map_conversion_crs()` can be used to extract georeferencing information from an IFC file. From XAxisAbscissa and XAxisOrdinate we calculate the rotation.


```python
import ifcopenshell.util.pset
import ifcopenshell.util.geolocation
from ifcopenshell.util.element import get_psets
import pandas as pd
from IPython.display import display

        
def map_conversion_crs(ifc_file):
    
    class Struct:
        def __init__(self, **entries):
            self.__dict__.update(entries)
            
    map_conversion = None
    crs = None
    
    if ifc_file.schema == 'IFC4':
        project = ifc_file.by_type("IfcProject")[0]
        for c in (m for c in project.RepresentationContexts for m in c.HasCoordinateOperation):
            return c, c.TargetCRS
    if ifc_file.schema == 'IFC2X3':
        site = ifc_file.by_type("IfcSite")[0]
        psets = get_psets(site)
        if 'ePSet_MapConversion' in psets.keys() and 'ePSet_ProjectedCRS' in psets.keys():
            return Struct(**psets['ePSet_MapConversion']), Struct(**psets['ePSet_ProjectedCRS'])
    return map_conversion, crs

        
IfcMapConversion, IfcProjectedCRS = map_conversion_crs(ifc_file)

df = pd.DataFrame(list(IfcProjectedCRS.__dict__.items()) + list(IfcMapConversion.__dict__.items()), columns= ['property', 'value'])
display(df)

rotation = degrees(atan2(IfcMapConversion.XAxisOrdinate, IfcMapConversion.XAxisAbscissa))
print(f'Rotation is: {rotation:.1f}°  (degrees(atan2(map_conversion.XAxisOrdinate, map_conversion.XAxisAbscissa)) ')
```


<div>
<style scoped>
    .dataframe tbody tr th:only-of-type {
        vertical-align: middle;
    }

    .dataframe tbody tr th {
        vertical-align: top;
    }

    .dataframe thead th {
        text-align: right;
    }
</style>
<table border="1" class="dataframe">
  <thead>
    <tr style="text-align: right;">
      <th></th>
      <th>property</th>
      <th>value</th>
    </tr>
  </thead>
  <tbody>
    <tr>
      <th>0</th>
      <td>Name</td>
      <td>EPSG:2169</td>
    </tr>
    <tr>
      <th>1</th>
      <td>Eastings</td>
      <td>76670.0</td>
    </tr>
    <tr>
      <th>2</th>
      <td>Northings</td>
      <td>77179.0</td>
    </tr>
    <tr>
      <th>3</th>
      <td>OrthogonalHeight</td>
      <td>293.700012</td>
    </tr>
    <tr>
      <th>4</th>
      <td>XAxisAbscissa</td>
      <td>0.325568</td>
    </tr>
    <tr>
      <th>5</th>
      <td>XAxisOrdinate</td>
      <td>0.945519</td>
    </tr>
    <tr>
      <th>6</th>
      <td>Scale</td>
      <td>1.0</td>
    </tr>
  </tbody>
</table>
</div>


    Rotation is: 71.0°  (degrees(atan2(map_conversion.XAxisOrdinate, map_conversion.XAxisAbscissa)) 


### Convert 3D spaces into 2D polygons (footprint)

We will use a utility function `shape_to_polygons(shape)` that will convert a 3D space into a 2D polygon, by extracting the shape into faces. Only the first face that is converted into a valid polygon is taken. We then use [GeoPandas](https://geopandas.org) to convert the polygons from the project CRS into the geospatial CRS using the IfcMapConversion parameters. We will respectively apply a rotation, translation, and scaling.


```python
from util import shape_to_polygons
import geopandas as gpd
from geopandas import GeoSeries

polygons = []
names = []
for space in spaces:
    if space.Representation is not None:
        shape = ifcopenshell.geom.create_shape(settings, inst=space)
        shape_polygons = shape_to_polygons(shape)
        polygons = polygons + shape_polygons
        names = names + [space.Name for _ in shape_polygons]
        

footprint = GeoSeries(polygons,crs=IfcProjectedCRS.Name)
footprint = footprint\
    .rotate(rotation, origin=(0,0,), use_radians=False)\
    .translate(IfcMapConversion.Eastings, IfcMapConversion.Northings, 0)\
    .scale(IfcMapConversion.Scale if IfcMapConversion.Scale else 1.0)
```

### Add footprints to map
The resulting building footprint data is pure geospatial data that can be depicted on a map and combined with other geospatial data, in this example with [OpenStreetMap](https://www.openstreetmap.org) and [geoportail.lu](https://map.geoportail.lu/) data.


```python
import folium
import json
import requests

m = folium.Map(location=[49.629, 6.122], zoom_start=20, tiles='CartoDB positron', max_zoom=30)

url="https://wms.inspire.geoportail.lu/geoserver/cp/wfs?service=WFS&request=GetFeature&version=2.0.0&srsName=urn:ogc:def:crs:EPSG::3857&typeNames=cp%3ACP.CadastralParcel&bbox=681342.6715153919,6382237.960593072,681731.4043978148,6382399.0656238245,urn:ogc:def:crs:EPSG::3857&namespaces=xmlns(cp,http%3A%2F%2Fcp)&count=2000&outputFormat=json"
df_cp = gpd.read_file(requests.get(url).text, crs='EPSG:3857')
df_cp = df_cp.to_crs(epsg=4326)
folium.GeoJson(df_cp.to_json(), name="cadastral parcels").add_to(m)

df = gpd.GeoDataFrame({'name': names}, geometry=footprint)
df = df.to_crs(epsg=4326)
for _, r in df.iterrows():
    sim_geo = gpd.GeoSeries(r['geometry'])
    geo_j = sim_geo.to_json()
    geo_j = folium.GeoJson(data=geo_j,
                           style_function=lambda x: {'fillColor': 'orange'})
    folium.Popup(r['name']).add_to(geo_j)
    geo_j.add_to(m)

m
```

## Conclusion

The use of  **IfcProjectedCRS** and **IfcMapConversion** is a unitrusive and precise way of adding geolocation information to an IFC file.
* This solution does require you to change the local reference system, only to provide information about it.
* It is more accurate compared the use of IfcSite.RefLongitude and IfcSite.RefLatitude in [WGS84](https://epsg.io/4326) coordinates, as a more appropriate geospatial coordinate reference system can be used.
* BIM tools such as Revit and ArchiCAD already support it.
* If your BIM tool does not support it, you can use IfcOpenShell to postprocess your IFC prior to exchanging it with third parties.

Therefore providing this information should considered to be made mandatory when drafting BIM information exchange agreements.

## References

BuildingSMART. IFC Specifications database. https://technical.buildingsmart.org/standards/ifc/ifc-schema-specifications/

BuildingSMART Australasia (2020). User Guide for Geo-referencing in IFC, version 2.0. https://www.buildingsmart.org/wp-content/uploads/2020/02/User-Guide-for-Geo-referencing-in-IFC-v2.0.pdf

Dion Moult (2019). IFC Coordinate Reference Systems and Revit. https://thinkmoult.com/ifc-coordinate-reference-systems-and-revit.html

OSarch.org (2021). IFC2x3 geo-referencing property set template definitions. https://wiki.osarch.org/index.php?title=IFC_geolocation

Clemen, C., & Görne, H. (2019). Level of Georeferencing (LoGeoRef) using IFC for BIM. Journal of Geodesy, Cartography and Cadastre, (10). https://jgcc.geoprevi.ro/docs/2019/10/jgcc_2019_no10_3.pdf

Noardo, F., Krijnen, T., Arroyo Ohori, K., Biljecki, F., Ellul, C., Harrie, L., Eriksson, H., Polia, L., Salheb, N., Tauscher, H., van Liempt, J., Goerne, H., Hintz, D., Kaiser, T., Leoni, C., Warchol, A., Stoter, J. (2021). Reference study of IFC software support: the GeoBIM benchmark 2019 – Part I. Transactions in GIS.


## Comments
Comments are welcome via GitHub [issues](https://github.com/stijngoedertier/georeference-ifc).


## License

This work is licensed under a Creative Commons Attribution-ShareAlike 4.0 International [(CC BY 4.0)](https://creativecommons.org/licenses/by/4.0/) License.