import json
import lxml.etree as etree
import requests
from rtree.index import Index
import fiona
from shapely.geometry import asShape, Point
import time

# TODO:
# Record the nodes for each way to plot their coords on the map


shape_files = [
    'Antrim and Newtownabbey.shp',
    'Armagh, Banbridge and Craigavon.shp',
    'Belfast.shp',
    'Causeway Coast and Glens.shp',
    'Derry and Strabane.shp',
    'Fermanagh and Omagh.shp',
    'Lisburn and Castlereagh.shp',
    'Mid and East Antrim.shp',
    'Mid Ulster.shp',
    'Newry, Mourne and Down.shp',
    'North Down and Ards.shp'
]
household_count = 0
testing = False
if testing:
    api = 'https://nominatim.openstreetmap.org/lookup?format=json&osm_ids={}&extratags=1'
else:
    api = 'http://143.117.174.209:80/nominatim/lookup?format=json&osm_ids={}&extratags=1'


def query_nominatim(_index, _polygons, _shapefile_records, _way_ids):
    osm_ids = ','.join(['W{}'.format(_way_id) for _way_id in _way_ids])

    response = requests.get(api.format(osm_ids))
    data = json.loads(response.content)

    for way_content in data:
        if way_content.get('address').get('country_code') == 'gb':
            if way_content.get('class') in ['building', 'residential', 'flats', 'house', 'apartments']:
                house_number = way_content.get('address').get('house_number')
                display_name = way_content.get('display_name')
                if house_number and display_name.split(',')[0] == house_number:
                    global household_count
                    household_count += 1
                    longitude = way_content.get('lon')
                    latitude = way_content.get('lat')
                    point = Point(float(longitude), float(latitude))

                    # technically, the point should only belong to one polygon anyway
                    for j in _index.intersection([point.x, point.y]):
                        if _polygons[j].contains(point):
                            _shapefile_record = _shapefile_records[j]
                            print '{} is in region {}'.format(display_name,
                                                              _shapefile_record['properties']['SUB_REGION'])
                            way_content['regional_info'] = {
                                'oa_sa': _shapefile_record['properties']['OA_SA'],
                                'region': _shapefile_record['properties']['SUB_REGION'],
                                'population': _shapefile_record['properties']['POPULATION'],
                                'length': _shapefile_record['properties']['Shape_Leng'],
                                'area': _shapefile_record['properties']['Shape_Area'],
                                'supergroup': _shapefile_record['properties']['SPRGRP'],
                                'group': _shapefile_record['properties']['GRP'],
                                'subgroup': _shapefile_record['properties']['SUBGRP']
                            }
                            with open('buildings/W{}.json'.format(way_content.get('osm_id')), 'w') as f:
                                json.dump(way_content, f)
                            break


start_time = time.time()

# Pre-processing
polygons = []
shapefile_records = []
for shape_file in shape_files:
    print 'Getting polygons from: {}'.format(shape_file)
    with fiona.open('shape files/' + shape_file) as collection:
        for shapefile_record in collection:
            shapefile_records.append(shapefile_record)
            shape = asShape(shapefile_record['geometry'])
            polygons.append(shape)

index = Index()
# count = 0
# for polygon in polygons:
#     index.insert(count, polygon.bounds)
#     count += 1

# Parsing ways
xml_ni = 'ni_buildings_test.osm'
way_ids = []
for event, element in etree.iterparse(xml_ni, events=('end',), tag='way'):
    way_id = element.get('id')
    if len(way_ids) < 50:
        way_ids.append(way_id)
    else:
        query_nominatim(index, polygons, shapefile_records, way_ids)
        way_ids = []

    element.clear()

    while element.getprevious() is not None:
        del element.getparent()[0]

query_nominatim(index, polygons, shapefile_records, way_ids)

print 'Extracted {} house-holds in {} seconds'.format(household_count, time.time() - start_time)
