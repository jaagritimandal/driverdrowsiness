import math


def distance(p1, p2):
    return math.sqrt(
        (p1.x - p2.x) ** 2 +
        (p1.y - p2.y) ** 2
    )


def calculate_mar(mouth):
    horizontal = distance(mouth[0], mouth[2])

    vertical_1 = distance(mouth[1], mouth[3])
    vertical_2 = distance(mouth[4], mouth[5])

    mar = (vertical_1 + vertical_2) / (2.0 * horizontal)

    return mar