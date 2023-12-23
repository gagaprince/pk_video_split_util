import cv2
import numpy as np
import ffmpeg
import os

def get_face_cascade():
    return cv2.CascadeClassifier('xml/haarcascade_frontalface_default.xml')

def get_body_cascade():
    return cv2.CascadeClassifier('xml/haarcascade_upperbody.xml')

def get_profile_face_cascade():
    return cv2.CascadeClassifier('xml/haarcascade_profileface.xml')



def check_img_face(img_path, face_cascade, body_cascade):
    img = img_path
    if isinstance(img_path, str):
        # 读取图片
        img = cv2.imread(img_path)

    if face_cascade is None:
        face_cascade = get_face_cascade()

    if body_cascade is None:
        body_cascade = get_body_cascade()

    profile_face_cascade = get_profile_face_cascade()

    # 转换为灰度图像
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

    # 进行人脸检测
    faces = face_cascade.detectMultiScale(gray, 1.3, 5)

    bodies = body_cascade.detectMultiScale(gray, 1.3, 5)

    profile_faces = profile_face_cascade.detectMultiScale(gray, 1.3, 5)

    print('人脸个数：', len(faces))
    print('侧脸个数：', len(profile_faces))
    print('上半身个数:', len(bodies))

    # 在图像上画出每一个人脸的矩形
    for (x, y, w, h) in faces:
        cv2.rectangle(img, (x, y), (x + w, y + h), (255, 0, 0), 2)

    for (x, y, w, h) in bodies:
        cv2.rectangle(img, (x, y), (x + w, y + h), (0, 0, 255), 2)

    # 显示图像
    cv2.imshow('img', img)
    cv2.waitKey(0)
    cv2.destroyAllWindows()

def split_video(video_path, start_time, end_time, out_path):
    ffmpeg.input(video_path).output(out_path, ss=start_time, to=end_time, c='copy').run()

def get_files_from_dir(dir):
    files = []
    for filepath,dirnames,filenames in os.walk(dir):
        for filename in filenames:
            if str.endswith(filename,'.flv'):
                files.append(os.path.join(filepath, filename))

    return files


if __name__ == '__main__':
    # img_path = './2.jpg'
    # check_img_face(img_path, get_face_cascade(), get_body_cascade())
    # video_path = './1.flv'
    # out_path = 'out/ss.flv'
    # start_time = '00:00:00'
    # end_time = '01:00:00'
    # split_video(video_path,start_time,end_time,out_path)
    files = get_files_from_dir('/Users/gagaprince/Downloads/20231008')
    print(files)
    for file in files:
        print(os.path.dirname(file))
