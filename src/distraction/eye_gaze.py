import math


LEFT_EYE_CORNERS = (33, 133)
RIGHT_EYE_CORNERS = (362, 263)

LEFT_IRIS = [468, 469, 470, 471, 472]
RIGHT_IRIS = [473, 474, 475, 476, 477]


def distance(p1, p2):
    return math.sqrt(
        (p1.x - p2.x) ** 2 +
        (p1.y - p2.y) ** 2
    )


def average_point(points):
    x = sum(p.x for p in points) / len(points)
    y = sum(p.y for p in points) / len(points)
    return x, y


def get_eye_gaze(face_landmarks):
    left_corner = face_landmarks[LEFT_EYE_CORNERS[0]]
    left_outer = face_landmarks[LEFT_EYE_CORNERS[1]]

    right_corner = face_landmarks[RIGHT_EYE_CORNERS[0]]
    right_outer = face_landmarks[RIGHT_EYE_CORNERS[1]]

    left_iris = [
        face_landmarks[i]
        for i in LEFT_IRIS
    ]

    right_iris = [
        face_landmarks[i]
        for i in RIGHT_IRIS
    ]

    left_iris_x, _ = average_point(left_iris)
    right_iris_x, _ = average_point(right_iris)

    left_min_x = min(left_corner.x, left_outer.x)
    left_max_x = max(left_corner.x, left_outer.x)

    right_min_x = min(right_corner.x, right_outer.x)
    right_max_x = max(right_corner.x, right_outer.x)

    left_range = left_max_x - left_min_x
    right_range = right_max_x - right_min_x

    if left_range == 0 or right_range == 0:
        return {
            "gaze": "CENTER",
            "left_ratio": 0.5,
            "right_ratio": 0.5,
        }

    left_ratio = (
        left_iris_x - left_min_x
    ) / left_range

    right_ratio = (
        right_iris_x - right_min_x
    ) / right_range

    average_ratio = (
        left_ratio + right_ratio
    ) / 2

    if average_ratio < 0.40:
        gaze = "LEFT"
    elif average_ratio > 0.60:
        gaze = "RIGHT"
    else:
        gaze = "CENTER"

    return {
        "gaze": gaze,
        "left_ratio": round(left_ratio, 3),
        "right_ratio": round(right_ratio, 3),
    }