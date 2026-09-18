MOUTH = [61, 13, 291, 14, 78, 308]


def get_mouth_landmarks(face_landmarks):
    return [face_landmarks[i] for i in MOUTH]