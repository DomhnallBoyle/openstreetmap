import fiona
import json
import os
import shutil
from collections import Counter
from rtree.index import Index
from shapely.geometry import asShape, Polygon


from Node import Node
from Rect import Rect


class LQTree:

    DIR_NAMES = ['nw', 'sw', 'ne', 'se']

    def __init__(self, x1, y1, x2, y2, path):
        self.root = Node(x1, y1, x2, y2, path)
        self.count = 1

    def add_to_node(self, _node, bounding_box, current_way):
        current_node = _node
        result, i = current_node.in_child_nodes(bounding_box)
        if result:
            child_node = current_node.nodes[i]
            if child_node is None:
                child_node = Node(*current_node.r.get_inner_rect(i), path=current_node.path + '/' + self.DIR_NAMES[i])
                if child_node.create_directory():
                    current_node.nodes[i] = child_node
                    self.count += 1
                else:
                    current_node.add_to_osm(current_way)
            self.add_to_node(child_node, bounding_box, current_way)
        else:
            current_node.add_to_osm(current_way)

    def remove_directory(self, path):
        shutil.rmtree(path)

    def clear(self):
        self.remove_directory(self.root.path)
        self.root = None
        self.count = 0


if __name__ == '__main__':
    xml = 'ireland-and-northern-ireland-latest.osm'
    # xml = 'ni_buildings_test.osm'
    ni_bb = [55.297884, -8.184814, 54.001312, -5.383301]
    tree = LQTree(*ni_bb, path='root')
    tree.root.create_directory()

    # 54.91, -7.25, 54.44, -6.23

    # first pass - nodes
    node_with_attrib = False
    node = []
    all_nodes = {}
    with open(xml, 'r') as f:
        for line in f:
            line = line.strip()
            if node_with_attrib:
                if line.startswith('</node>'):
                    node_with_attrib = False
                node.append(line)
            elif len(node) > 0:
                _node = '\n'.join(node)
                _id = _node.split('"')[1]
                all_nodes[_id] = _node
                node = []

            if line.startswith('<node'):
                if line.endswith('">'):
                    node_with_attrib = True
                node.append(line)

    # second pass - ways
    count = 50
    way = []
    nodes = []
    found_way = False
    with open(xml, 'r') as f:
        for line in f:
            line = line.strip()
            if found_way:
                if line.startswith('<nd'):
                    ref = line.split('"')[1]
                    node = all_nodes[ref]
                    nodes.append(node)
                    way.append(node)
                elif line.startswith('</way>'):
                    way.append('</way>')
                    if len(nodes) > 2:
                        polygon = Polygon(
                            [
                                [float(node.split('"')[3]), float(node.split('"')[5])] for node in nodes
                            ]
                        )
                        bb = polygon.bounds
                        if bb[0] <= ni_bb[0] and bb[1] >= ni_bb[1] and bb[2] >= ni_bb[2] and bb[3] <= ni_bb[3]:
                            tree.add_to_node(tree.root, bb, '\n'.join(way))
                            # if count == 0:
                            #     break
                            # else:
                            #     count -= 1

                    nodes = []
                    way = []
                    found_way = False
                else:
                    way.append(line)
            elif line.startswith('<way'):
                found_way = True
                way.append(line)

    print tree.count

    # get all polygons from shape files - need to find OAC classification etc
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
    polygons = []
    shapefile_records = []
    for shape_file in shape_files:
        print 'Getting polygons from: {}'.format(shape_file)
        with fiona.open('shape files/' + shape_file) as collection:
            for shapefile_record in collection:
                shape = asShape(shapefile_record['geometry'])
                y1, x1, y2, x2 = shape.bounds
                shapefile_record['properties']['bounds'] = str((x1, y1, x2, y2))
                shapefile_records.append(shapefile_record)
                polygons.append(shape)

    index = Index()
    count = 0
    for polygon in polygons:
        index.insert(count, polygon.bounds)
        count += 1

    # recursively loop over every directory
    for root, directories, filenames in os.walk('root'):
        for filename in filenames:
            obj = None
            with open(os.path.join(root, filename), 'r') as f:
                bb = f.readline()
                tpl = eval(bb)
                r = Rect(*tpl)
                # point = Point(*r.centre_point)
                records = []
                # for j in index.nearest(r.rtree_bb(), 1):
                for j in index.intersection(r.rtree_bb()):
                    shapefile = shapefile_records[j]
                    records.append(shapefile)

                if len(records) == 1:
                    super_group = records[0]['properties']['SPRGRP']
                    group = records[0]['properties']['GRP']
                    sub_group = records[0]['properties']['SUBGRP']
                    region = records[0]['properties']['SUB_REGION']
                elif len(records) > 1:
                    # mode
                    super_groups, groups, sub_groups, regions = [], [], [], []
                    for record in records:
                        super_groups.append(record['properties']['SPRGRP'])
                        groups.append(record['properties']['GRP'])
                        sub_groups.append(record['properties']['SUBGRP'])
                        regions.append(record['properties']['SUB_REGION'])

                    super_group = Counter(super_groups).most_common(1)[0][0]
                    group = Counter(groups).most_common(1)[0][0]
                    sub_group = Counter(sub_groups).most_common(1)[0][0]
                    region = Counter(regions).most_common(1)[0][0]
                else:
                    super_group = 'ROI'
                    group = 'ROI'
                    sub_group = 'ROI'
                    region = 'ROI'

                # print '{} - {}, {}, {}, {}'.format(r.bb(), super_group, group, sub_group, region)
                obj = json.load(f)
                obj['regional_info'] = {
                    'super_group': super_group,
                    'group': group,
                    'sub_group': sub_group,
                    'region': region
                }

            with open(os.path.join(root, 'segment_info.json'), 'w') as f:
                json.dumps(obj, f)
