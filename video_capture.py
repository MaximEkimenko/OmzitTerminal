import cv2


def face_and_qr_reader():
    """
    Определение лица в видеопотоке и считывание QR.
    :return:
    """
    qr_detector = cv2.QRCodeDetector()  # декодер
    cap = cv2.VideoCapture(0)  # видеопоток
    while True:
        ret, frame = cap.read()
        if ret:  # если не было ошибок при чтении кадра
            try:
                ret_qr, decoded_info, points, _ = qr_detector.detectAndDecodeMulti(frame)  # декодирование QR
            except Exception as e:
                ret_qr, decoded_info, points, _ = qr_detector.detectAndDecodeMulti(frame)
                print(e)
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)  # перевод в серый цвет
            if ret_qr:
                for qr_text, point_vertices in zip(decoded_info, points):
                    if qr_text:
                        print(qr_text)
                        # TODO код нужного действия при определении текста
                        #  принудительный выход из цикла с сообщением об успехе в интерфейс - break
                        color = (255, 255, 255)  # подкраска белым если прочитал QR
                    else:
                        color = (0, 0, 0)  # подкраска чёрным если не прочитал
                    # обвод QR цветом
                    gray = cv2.polylines(gray, [point_vertices.astype(int)], True, color, 8)
            face_cascade = cv2.CascadeClassifier(r'haarcascade_frontalface_alt2.xml')
            faces = face_cascade.detectMultiScale(gray, 1.3, 5)
            # print(faces, type(faces))
            if faces is not None and type(faces) != tuple:
                print(faces)
            for (x, y, w, h) in faces:
                cv2.rectangle(gray, (x, y), (x + w, y + h), (255, 0, 0), 4)
            cv2.imshow(winname='Camera 0', mat=gray)  # отображение картинки

        if cv2.waitKey(1) & 0xFF == ord('q'):
            break
    cap.release()
    cv2.destroyWindow('Camera 0')


if __name__ == '__main__':
    # QR_reader()
    # face_reader()
    face_and_qr_reader()

