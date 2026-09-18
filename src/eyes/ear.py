import math


def distance(p1, p2):
    return math.sqrt(
        (p1.x - p2.x) ** 2 +
        (p1.y - p2.y) ** 2
    )


def calculate_ear(eye):
    vertical_1 = distance(eye[1], eye[5])
    vertical_2 = distance(eye[2], eye[4])

    horizontal = distance(eye[0], eye[3])

    ear = (vertical_1 + vertical_2) / (2.0 * horizontal)

    return ear