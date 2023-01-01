import math


class Hand:
    def __init__(self, landmarks, handidness) -> None:
        self.wrist = landmarks[0]
        self.thumb_cmc = landmarks[1]
        self.thumb_mcp = landmarks[2]
        self.thumb_ip = landmarks[3]
        self.thumb_tip = landmarks[4]
        self.index_mcp = landmarks[5]
        self.index_pip = landmarks[6]
        self.index_dip = landmarks[7]
        self.index_tip = landmarks[8]
        self.middle_mcp = landmarks[9]
        self.middle_pip = landmarks[10]
        self.middle_dip = landmarks[11]
        self.middle_tip = landmarks[12]
        self.ring_mcp = landmarks[13]
        self.ring_pip = landmarks[14]
        self.ring_dip = landmarks[15]
        self.ring_tip = landmarks[16]
        self.pinky_mcp = landmarks[17]
        self.pinky_pip = landmarks[18]
        self.pinky_dip = landmarks[19]
        self.pinky_tip = landmarks[20]

        self.landmarks_list = [landmarks[idx] for idx in range(21)]

        self.handidness = handidness.classification[0].label
        self.handidness_score = handidness.classification[0].score

        self.orientation = self.get_orientation()
        self.size, self.sizex, self.sizey, self.bounding_box = self.get_size()
        self.face = self.get_face()

    def get_orientation(self):
        x = self.middle_mcp.x - self.wrist.x
        y = self.middle_mcp.y - self.wrist.y

        if (
            self.middle_mcp.x <= self.wrist.x and
            self.middle_mcp.y <= self.wrist.y
        ):
            q = 0
        elif (
            self.middle_mcp.x <= self.wrist.x and
            self.middle_mcp.y >= self.wrist.y
        ):
            q = 180
        elif (
            self.middle_mcp.x >= self.wrist.x and
            self.middle_mcp.y >= self.wrist.y
        ):
            q = -180
        elif (
            self.middle_mcp.x >= self.wrist.x and
            self.middle_mcp.y <= self.wrist.y
        ):
            q = 0

        return(q + math.degrees(math.atan(x/y)))

    def get_size(self):
        self.max_x = 0
        self.max_y = 0
        self.min_x = 1
        self.min_y = 1
        for landmark in self.landmarks_list:
            self.max_x = max(landmark.x, self.max_x)
            self.max_y = max(landmark.y, self.max_y)
            self.min_x = min(landmark.x, self.min_x)
            self.min_y = min(landmark.y, self.min_y)
        size = math.sqrt(
            (self.max_x - self.min_x)**2 + (self.max_y - self.min_y)**2
        )
        sizex = self.max_x - self.min_x
        sizey = self.max_y - self.min_y
        return(
            size,
            sizex,
            sizey,
            (
                (self.min_x, self.min_y),
                (self.max_x, self.min_y),
                (self.max_x, self.max_y),
                (self.min_x, self.max_y)
            )
        )

    def get_face(self):
        if abs(self.orientation) < 30:
            if self.handidness == "Right":
                if self.thumb_mcp.x < self.pinky_mcp.x:
                    return "forehand"
                return "backhand"
            if self.thumb_mcp.x > self.pinky_mcp.x:
                return "forehand"
            return "backhand"
        elif abs(self.orientation) > 150:
            if self.handidness == "Right":
                if self.thumb_mcp.x > self.pinky_mcp.x:
                    return "forehand"
                return "backhand"
            if self.thumb_mcp.x < self.pinky_mcp.x:
                return "forehand"
            return "backhand"
        elif self.orientation >= 30 and self.orientation <= 150:
            if self.handidness == "Right":
                if self.thumb_mcp.y > self.pinky_mcp.y:
                    return "forehand"
                return "backhand"
            if self.thumb_mcp.y < self.pinky_mcp.y:
                return "forehand"
            return "backhand"
        elif self.orientation <= -30 and self.orientation >= -150:
            if self.handidness == "Right":
                if self.thumb_mcp.y < self.pinky_mcp.y:
                    return "forehand"
                return "backhand"
            if self.thumb_mcp.y > self.pinky_mcp.y:
                return "forehand"
            return "backhand"

    def finger_up(self, finger_top, finger_btm, strict="no"):
        if strict == "strict":
            if abs(finger_top.x - finger_btm.x) > self.size/10:
                return False
        if finger_top.y < finger_btm.y:
            return True
        return False

    def thumb_up(self, strict="no"):
        return(self.finger_up(self.thumb_tip, self.thumb_mcp, strict))

    def index_up(self, strict="no"):
        return(self.finger_up(self.index_tip, self.index_pip, strict))

    def middle_up(self, strict="no"):
        return(self.finger_up(self.middle_tip, self.middle_pip, strict))

    def ring_up(self, strict="no"):
        return(self.finger_up(self.ring_tip, self.ring_pip, strict))

    def pinky_up(self, strict="no"):
        return(self.finger_up(self.pinky_tip, self.pinky_pip, strict))

    def gesture_open_palm(self):
        if (
            self.face == "forehand" and
            self.thumb_up() and
            self.index_up("strict") and
            self.middle_up("strict") and
            self.ring_up("strict") and
            self.pinky_up("strict")
        ):
            return True
        return False

    def gesture_flipping_the_bird(self):
        if (
            self.face == "backhand" and
            abs(self.orientation) < 45 and
            not self.index_up() and
            self.middle_up() and
            not self.ring_up() and
            not self.pinky_up()
        ):
            return True
        return False

    def gesture_raised_fist(self):
        if (
            self.face == "forehand" and
            abs(self.orientation) < 30 and
            self.index_tip.y > self.index_pip.y and
            self.middle_tip.y > self.middle_pip.y and
            self.ring_tip.y > self.ring_pip.y and
            self.pinky_tip.y > self.pinky_pip.y and
            (
                (
                    self.handidness == "Right" and
                    self.thumb_tip.x > self.index_mcp.x and
                    self.thumb_tip.x < self.pinky_mcp.x
                ) or
                (
                    self.handidness == "Left" and
                    self.thumb_tip.x < self.index_mcp.x and
                    self.thumb_tip.x > self.pinky_mcp.x
                )
            )
        ):
            return True
        return False
