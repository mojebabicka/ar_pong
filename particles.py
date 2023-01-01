import cv2
import math
import numpy as np
import random


def generate(ball_x, ball_y, bearing):
    plist = []
    while True:
        ball_y += int(48*math.sin(bearing))
        ball_x += int(48*math.cos(bearing))
        for y in range(ball_y-280, ball_y-20):
            for x in range(ball_x-30*abs((y-ball_y))//100, ball_x+30*abs((y-ball_y))//100):
                x2 = x - ball_x
                y2 = y - ball_y
                if x != ball_x:
                    prob_x = abs(ball_x-x)
                else:
                    prob_x = 1
                if (
                    random.randrange(-abs(int(100*(y2+300)/y2)), -1) < random.randrange(-200, -20) and
                    random.randrange(prob_x) < random.randrange(-2, 5)
                ):
                    modifier = 0
                    if 8.5*abs(ball_x-x) > 0:
                        modifier = 8.5*abs(ball_x-x)
                    if 8.5*abs(ball_x-x) > 255:
                        modifier = 255
                    color = (max(0, 100-modifier), modifier, 255)
                    r = math.sqrt(x2**2 + y2**2)
                    phi = math.atan2(y2, x2)
                    phi += bearing - math.pi/2
                    xr = int(r*math.cos(phi)) + ball_x
                    yr = int(r*math.sin(phi)) + ball_y
                    plist.append([xr, yr, color])

        return plist


if __name__ == "__main__":
    bearing = 0
    while True:
        bearing += 0.1
        blank_image = np.zeros((600, 600, 3), np.uint8)
        for points in generate(300, 300, bearing):
            cv2.circle(
                blank_image,
                (points[0], points[1]),
                2,
                points[2],
                cv2.FILLED
            )
            # blank_image[points[1], points[0]] = points[2]
        cv2.circle(
            blank_image,
            (300, 300),
            30,
            (0, 255, 255),
            cv2.FILLED
        )
        cv2.imshow("blank_image", blank_image)
        cv2.waitKey(1)
