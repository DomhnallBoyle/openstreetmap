import os
import json

from Rect import Rect


class Node:

    MAX_PATH_LENGTH = 260
    OSM_NAME = 'segment.osm'

    def __init__(self, x1, y1, x2, y2, path):
        self.r = Rect(x1, y1, x2, y2)
        self.nodes = [None, None, None, None]
        self.path = path
        self.osm_path = self.path + '/' + self.OSM_NAME

    def create_directory(self):
        print 'Creating directory: {}'.format(self.path)
        if len(self.path) <= self.MAX_PATH_LENGTH - len(self.OSM_NAME):
            try:
                if not os.path.exists(self.path):
                    os.makedirs(self.path)

                with open(self.osm_path, 'w') as f:
                    f.write(str(self.r.bb()) + '\n')

                return True
            except OSError:
                return False
        else:
            return False

    def add_to_osm(self, current_way):
        with open(self.osm_path, 'a') as f:
            f.write(current_way + '\n')

    def set_path(self, path):
        self.path = path

    def in_child_nodes(self, bounding_box):
        # TODO: Looser bounds
        # If the bb size < cell size and the bb centre is inside the cell, we can guarantee the object is in the
        # loose bounds
        r = Rect(*bounding_box)
        for i in range(0, 4):
            segment = self.r.get_loose_rect(i)
            segment = Rect(*segment)
            if (abs(r.width) <= abs(segment.width) and abs(r.height) <= abs(segment.height)) and segment.in_rect(
                    point=r.centre_point):
                return True, i
            # if segment.in_rect(point=r.get_top_left()) and segment.in_rect(point=r.get_bottom_right()):
            #     return True, i

        return False, None
