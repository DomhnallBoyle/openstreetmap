

class Rect:

    def __init__(self, x1, y1, x2, y2):
        self.x1 = x1
        self.y1 = y1
        self.x2 = x2
        self.y2 = y2
        self.width = x2 - x1
        self.height = y2 - y1
        self.half_width = self.width / 2
        self.half_height = self.height / 2
        self.quarter_width = self.width / 4
        self.quarter_height = self.height / 4
        self.centre_point = (x1 + self.half_width, y1 + self.half_height)
        self.inner_rects = [
            [x1, y1, x1 + self.half_width, y1 + self.half_height],
            [x1 + self.half_width, y1, x2, y1 + self.half_height],
            [x1, y1 + self.half_height, x1 + self.half_width, y2],
            [x1 + self.half_width, y1 + self.half_height, x2, y2]
        ]
        self.loose_rects = [
            [ir[0] - self.quarter_width, ir[1] - self.quarter_height, ir[2] + self.quarter_width,
             ir[3] + self.quarter_height] for ir in self.inner_rects
        ]

    def bb(self):
        return (self.x1, self.y1, self.x2, self.y2)

    def rtree_bb(self):
        return (self.y2 - self.height, self.x2, self.y1 + self.height, self.x1)

    def get_top_left(self):
        return (self.x1, self.y1)

    def get_bottom_right(self):
        return (self.x2, self.y2)

    def get_inner_rect(self, i):
        return self.inner_rects[i]

    def get_loose_rect(self, i):
        return self.loose_rects[i]

    def in_rect(self, point):
        x, y = point
        if (self.x2 <= x <= self.x1) and (self.y1 <= y <= self.y2):
            return True

        return False
