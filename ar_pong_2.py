import cv2
import gd_twoen
import math
import mediapipe as mp
import multiprocessing
import numpy as np
import particles
import random
import time
import twoen
import urllib.request as ur


def cummulative_avg(s, n, prev_avg):
    return (prev_avg + (s - prev_avg) / (n + 1), n + 1)


def get_frame(ip_address, stream_output):
    ip_address = "10.0.23.208"
    stream = ur.urlopen(
        ur.Request(
            "http://"
            + ip_address
            + "/api/camera/snapshot?width=1280&height=960&quality=60&source=internal&fps=15",
            headers={"Cache-Control": "no-cache"}
        )
    )

    bts = bytes()
    stime = time.time()
    n = 0
    prev_avg = 0
    while True:
        bts += stream.read(4096)
        a = bts.find(b'\xff\xd8')
        b = bts.find(b'\xff\xd9')
        if a != -1 and b != -1:
            if b > a:
                jpg = bts[a:b+2]
                bts = bts[b+2:]
                img = cv2.imdecode(
                    np.frombuffer(jpg, dtype=np.uint8),
                    cv2.IMREAD_COLOR
                )
                stream_output.put(img)
                prev_avg, n = cummulative_avg(time.time() - stime, n, prev_avg)
                if n % 100 == 0:
                    print("stream", prev_avg)
                stime = time.time()
            else:
                bts = bts[a:]


def detect_hands(stream_output, processed_output):
    hands = mp.solutions.hands.Hands()
    n = 0
    prev_avg = 0
    while True:
        stime = time.time()
        objects = []
        if stream_output.empty():
            continue

        while not stream_output.empty():
            img = stream_output.get()
        imgRGB = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        results = hands.process(imgRGB)
        if results.multi_hand_landmarks:
            for hand_landmarks, hand_handiness in zip(
                results.multi_hand_landmarks[:2],
                results.multi_handedness[:2]
            ):
                objects.append(
                    gd_twoen.Hand(hand_landmarks.landmark, hand_handiness)
                )
        processed_output.put((img, objects))
        prev_avg, n = cummulative_avg(time.time() - stime, n, prev_avg)
        if n % 100 == 0:
            print("hands", prev_avg)


def prepare_image(processed_output, final_image):

    ball_x_default = int(0.5*1707)
    ball_y_default = int(0.5*1280)
    ball_x = ball_x_default
    ball_y = ball_y_default
    ball_speed_x = random.randrange(-30, 30)
    ball_speed_y = -30
    if random.randrange(10) % 2 == 0:
        ball_speed_y = 30
    active = True
    score = [0, 0]
    temp = processed_output.get()
    img = temp[0]
    objects = temp[1]
    n = 0
    prev_avg = 0

    while True:
        stime = time.time()
        paddles = [False, False]
        players = [None, None]
        objects = []

        if processed_output.empty():
            continue

        bearing = math.atan2(ball_speed_y, ball_speed_x)

        while not processed_output.empty():
            temp = processed_output.get()
            img = temp[0]
            objects = temp[1]
        img = cv2.resize(img, (1707, 1280))
        h, w, c = img.shape

        if not active:
            if len(objects) == 2:
                if objects[0].gesture_raised_fist() and objects[1].gesture_raised_fist():
                    score[0] = 0
                    score[1] = 0
                    ball_speed_x = random.randrange(-20, 20)
                    ball_speed_y = -30
                    if random.randrange(10) % 2 == 0:
                        ball_speed_y = 30
                    active = True

        if len(objects) > 1:
            if objects[0].max_y < objects[1].min_y:
                players = ["upper", "lower"]
            else:
                players = ["lower", "upper"]
        elif len(objects) == 1:
            if objects[0].max_y <= 0.5:
                players = ["upper", None]
            elif objects[0].min_y >= 0.5:
                players = ["lower", None]
            else:
                None

        for idx, hand in enumerate(objects):
            # PADDLES COLLISION
            paddles[idx] = True
            bounding_box_color = (128, 128, 128)

            if len(objects) > 1:
                if players[idx] == "upper":
                    bounding_box_color = (0, 255, 0)
                else:
                    bounding_box_color = (0, 0, 255)

            if (
                (hand.sizex > 0.2 or hand.sizey > 0.2) or
                (players[idx] == "lower" and hand.min_y < 0.7) or
                (players[idx] == "upper" and hand.max_y > 0.3)
            ):
                bounding_box_color = (128, 128, 128)
                paddles[idx] = False

            if paddles[idx]:
                if players[idx] == "lower":
                    if abs(ball_y - hand.min_y*h) < 31 and ball_x > hand.min_x*w and ball_x < hand.max_x*w:
                        modifier = -math.cos(2*abs(math.radians(hand.orientation)))
                        old_speed = ball_speed_x
                        ball_speed_x += int((ball_speed_x/abs(ball_speed_x)) * (int(5*modifier) + int(abs(ball_speed_x)*modifier)))
                        if abs(ball_speed_x) > 49:
                            ball_speed_x = old_speed
                        ball_speed_y = int(math.sqrt(50**2 - ball_speed_x**2))
                        if ball_speed_x == 0:
                            ball_speed_x = 1
                        if ball_speed_y > 0:
                            ball_speed_y = -ball_speed_y
                else:
                    if abs(ball_y - hand.max_y*h) < 31 and ball_x > hand.min_x*w and ball_x < hand.max_x*w:
                        modifier = -math.cos(2*abs(math.radians(hand.orientation)))
                        old_speed = ball_speed_x
                        ball_speed_x += int((ball_speed_x/abs(ball_speed_x)) * (int(5*modifier) + int(abs(ball_speed_x)*modifier)))
                        if abs(ball_speed_x) > 49:
                            ball_speed_x = old_speed
                        ball_speed_y = int(math.sqrt(50**2 - ball_speed_x**2))
                        if ball_speed_x == 0:
                            ball_speed_x = 1
                        if ball_speed_y < 0:
                            ball_speed_y = -ball_speed_y

            # DRAW PADDLES
            if True:
                for point in hand.bounding_box:
                    cv2.circle(
                        img,
                        (int(point[0]*w), int(point[1]*h)),
                        5,
                        (0, 255, 0),
                        cv2.FILLED
                    )

                for p1, p2 in zip(
                    hand.bounding_box,
                    hand.bounding_box[1:] + (hand.bounding_box[0],)
                ):
                    cv2.line(
                        img,
                        (int(p1[0]*w), int(p1[1]*h)),
                        (int(p2[0]*w), int(p2[1]*h)),
                        bounding_box_color,
                        3
                    )

                for landmark in hand.landmarks_list:
                    h, w, c = img.shape
                    cx, cy = int(landmark.x * w), int(landmark.y * h)
                    cv2.circle(
                        img,
                        (cx, cy),
                        5,
                        (
                            128 + 1270*landmark.z,
                            128 + 1270*landmark.z,
                            128 + 1270*landmark.z
                        ),
                        cv2.FILLED
                    )
                    cv2.circle(
                        img,
                        (cx, cy),
                        2,
                        (
                            0,
                            0,
                            255
                        ),
                        cv2.FILLED
                    )

                for points in [
                    (hand.landmarks_list[0], hand.landmarks_list[1]),
                    (hand.landmarks_list[0], hand.landmarks_list[5]),
                    (hand.landmarks_list[0], hand.landmarks_list[17]),
                    (hand.landmarks_list[1], hand.landmarks_list[2]),
                    (hand.landmarks_list[2], hand.landmarks_list[3]),
                    (hand.landmarks_list[3], hand.landmarks_list[4]),
                    (hand.landmarks_list[5], hand.landmarks_list[6]),
                    (hand.landmarks_list[6], hand.landmarks_list[7]),
                    (hand.landmarks_list[7], hand.landmarks_list[8]),
                    (hand.landmarks_list[5], hand.landmarks_list[9]),
                    (hand.landmarks_list[9], hand.landmarks_list[10]),
                    (hand.landmarks_list[10], hand.landmarks_list[11]),
                    (hand.landmarks_list[11], hand.landmarks_list[12]),
                    (hand.landmarks_list[9], hand.landmarks_list[13]),
                    (hand.landmarks_list[13], hand.landmarks_list[14]),
                    (hand.landmarks_list[14], hand.landmarks_list[15]),
                    (hand.landmarks_list[15], hand.landmarks_list[16]),
                    (hand.landmarks_list[13], hand.landmarks_list[17]),
                    (hand.landmarks_list[17], hand.landmarks_list[18]),
                    (hand.landmarks_list[18], hand.landmarks_list[19]),
                    (hand.landmarks_list[19], hand.landmarks_list[20]),
                ]:
                    cv2.line(
                        img,
                        (int(points[0].x*w), int(points[0].y*h)),
                        (int(points[1].x*w), int(points[1].y*h)),
                        (200, 128, 128),
                        1
                    )

        if True:
            # DRAW BALL AND PLAYGROUND
            for particle in particles.generate(ball_x, ball_y, bearing):
                try:
                    cv2.circle(
                        img,
                        (particle[0], particle[1]),
                        2,
                        particle[2],
                        cv2.FILLED
                    )
                except IndexError:
                    pass

        if True:
            # ball_color1 = (random.randrange(50, 150), random.randrange(50, 150), random.randrange(200, 256))
            # ball_color2 = (255-ball_color1[0], 255-ball_color1[1], 255-ball_color1[2])
            ball_color1 = (0, 0, 255)
            ball_color2 = (0, 255, 255)
            cv2.circle(
                img,
                (ball_x, ball_y),
                30,
                ball_color1,
                cv2.FILLED
            )
            cv2.circle(
                img,
                (ball_x, ball_y),
                15,
                ball_color2,
                cv2.FILLED
            )

            cv2.line(
                img,
                (0, int(0.7*h)),
                (1707, int(0.7*h)),
                (255, 255, 255),
                3
            )

            cv2.line(
                img,
                (0, int(0.3*h)),
                (1707, int(0.3*h)),
                (255, 255, 255),
                3
            )

            cv2.line(
                img,
                (0, int(0.7*h)-3),
                (1707, int(0.7*h)-3),
                (0, 0, 0),
                3
            )

            cv2.line(
                img,
                (0, int(0.3*h)+3),
                (1707, int(0.3*h)+3),
                (0, 0, 0),
                3
            )

        if ball_x <= 478 or ball_x >= 1228:
            ball_speed_x = -ball_speed_x

        ball_x += ball_speed_x
        ball_y += ball_speed_y

        if ball_y < 0:
            ball_x = ball_x_default
            ball_y = ball_y_default
            score[1] += 1
        elif ball_y > 1280:
            ball_x = ball_x_default
            ball_y = ball_y_default
            score[0] += 1

        img = cv2.putText(
            img,
            str(score[0]),
            (1150, int(0.3*h+90)),
            cv2.FONT_HERSHEY_SIMPLEX,
            3,
            (0, 255, 0),
            5
        )

        img = cv2.putText(
            img,
            str(score[1]),
            (1150, int(0.7*h-30)),
            cv2.FONT_HERSHEY_SIMPLEX,
            3,
            (0, 0, 255),
            5
        )

        if score[0] > 4:
            img = cv2.putText(
                img,
                "GREEN WINS",
                (600, 600),
                cv2.FONT_HERSHEY_SIMPLEX,
                3,
                (0, 255, 0),
                5
            )
            ball_speed_x = 0
            ball_speed_y = 0
            active = False

        if score[1] > 4:
            img = cv2.putText(
                img,
                "RED WINS",
                (600, 600),
                cv2.FONT_HERSHEY_SIMPLEX,
                3,
                (0, 0, 255),
                5
            )
            ball_speed_x = 0
            ball_speed_y = 0
            active = False

        img = img[0:1280, 453:1253]
        image_bytes = cv2.imencode(
            ".jpeg",
            img,
            [cv2.IMWRITE_JPEG_QUALITY, 20]
        )[1].tobytes()
        final_image.put(image_bytes)
        prev_avg, n = cummulative_avg(time.time() - stime, n, prev_avg)
        if n % 100 == 0:
            print("image", prev_avg)


def upload_image(final_image, ip_address, password):
    device = twoen.Device(ip_address, "admin", password)
    device.login()
    image_bytes = final_image.get()
    n = 0
    prev_avg = 0
    while True:
        stime = time.time()
        while not final_image.empty():
            image_bytes = final_image.get()
        device.upload_image(image_bytes)
        prev_avg, n = cummulative_avg(time.time() - stime, n, prev_avg)
        if n % 100 == 0:
            print("upload", prev_avg)


if __name__ == "__main__":
    ip_address = input("IP ADDRESS: ")
    password = input("PASSWORD: ")

    stream_output = multiprocessing.Manager().Queue()
    processed_output = multiprocessing.Manager().Queue()
    final_image = multiprocessing.Manager().Queue()

    p_stream = multiprocessing.Process(
        target=get_frame,
        args=(ip_address, stream_output)
    )
    p_stream.start()

    p_process = multiprocessing.Process(
        target=detect_hands,
        args=(stream_output, processed_output)
    )
    p_process.start()

    p_image = multiprocessing.Process(
        target=prepare_image,
        args=(processed_output, final_image)
    )
    p_image.start()

    p_upload = multiprocessing.Process(
        target=upload_image,
        args=(final_image, ip_address, password)
    )
    p_upload.start()

    while True:
        time.sleep(1)
