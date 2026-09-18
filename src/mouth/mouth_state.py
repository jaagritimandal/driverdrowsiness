MOUTH = [61, 82, 312, 291, 317, 87]

def get_mouth_landmarks(face_landmarks):
    return [face_landmarks[i] for i in MOUTH]