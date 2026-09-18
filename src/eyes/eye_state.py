LEFT_EYE = [33, 160, 158, 133, 153, 144]
RIGHT_EYE = [362, 385, 387, 263, 373, 380]


def get_eye_landmarks(face_landmarks):
    left_eye = [face_landmarks[i] for i in LEFT_EYE]
    right_eye = [face_landmarks[i] for i in RIGHT_EYE]

    return left_eye, right_eye