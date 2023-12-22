import cv2
import numpy as np
from datetime import timedelta
import ffmpeg


def get_face_cascade():
    return cv2.CascadeClassifier('xml/haarcascade_frontalface_default.xml')

def check_img_face(img_path, face_cascade):
    img = img_path
    if isinstance(img_path, str):
        # 读取图片
        img = cv2.imread(img_path)

    if face_cascade is None:
        face_cascade = get_face_cascade()

    # 转换为灰度图像
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

    # 进行人脸检测
    faces = face_cascade.detectMultiScale(gray, 1.3, 5)

    # print('人脸个数：', len(faces))

    # 在图像上画出每一个人脸的矩形
    for (x, y, w, h) in faces:
        cv2.rectangle(img, (x, y), (x + w, y + h), (255, 0, 0), 2)

    return len(faces)
# last_flag的作用 如果上一次的flag是true 说明正在pk中 此时不需要检测人脸 只要直线符合就认定还是true
# 防止人脸误判
def cv_test_ispk(img_path, min_line, last_flag):
    img = img_path
    if isinstance(img_path, str):
        # 读取图片
        img = cv2.imread(img_path)

    face_cascade = get_face_cascade()

    # 使用Canny边缘检测
    edges = cv2.Canny(img, 10, 200, apertureSize=3)

    # 使用阈值化处理，将灰度边缘图像转换为黑白二值图像
    _, binary_edges = cv2.threshold(edges, 127, 255, cv2.THRESH_BINARY)



    lines = cv2.HoughLines(binary_edges, 1, np.pi / 180, min_line)
    # print('lines:', lines)

    spline_num = 0
    czline_num = 0
    if lines is not None:
        # 遍历每一条检测到的直线
        for line in lines:
            for rho, theta in line:
                # print('rho:', rho)
                # print('theta', theta)
                # 将极坐标转换为笛卡尔坐标
                a = np.cos(theta)
                b = np.sin(theta)
                x0 = a * rho
                y0 = b * rho
                x1 = int(x0 + 1000 * (-b))
                y1 = int(y0 + 1000 * (a))
                x2 = int(x0 - 1000 * (-b))
                y2 = int(y0 - 1000 * (a))
                # print('直线坐标:', x1,y1,'   ',x2,y2)
                if abs(y2-y1) < 10:
                    spline_num += 1
                if abs(x2-x1) < 10:
                    czline_num += 1
                # print('img shape', img.shape)
                cv2.line(img, (x1, y1), (x2, y2), (0, 0, 255), 3)

    # 显示边缘图像
    if spline_num >= 2 and czline_num >= 1:  # 水平方向直线大于等于2 垂直线等于1 再检测人脸数 如果人脸数>1 说明是pk
        # cv2.imshow('img', img)
        # cv2.waitKey(0)
        # cv2.destroyAllWindows()
        # print('ispk!')
        if not last_flag:
            face_num = check_img_face(img, face_cascade)
            if face_num > 1:
                return True, spline_num
        else:
            return True, spline_num
    # print('notpk!')
    return False, spline_num

def get_video_info(video_path):
    cap = cv2.VideoCapture(video_path)
    # 获取FPS
    fps = cap.get(cv2.CAP_PROP_FPS)
    print('FPS:', fps)
    # 获取帧数
    frame_count = cap.get(cv2.CAP_PROP_FRAME_COUNT)
    print('FrameCount:', frame_count)
    # 获取宽度
    width = cap.get(cv2.CAP_PROP_FRAME_WIDTH)
    print('Width:', width)
    # 获取高度
    height = cap.get(cv2.CAP_PROP_FRAME_HEIGHT)
    print('Height:', height)
    # 释放资源
    cap.release()
    return fps, frame_count, width, height

# 返回pk or notpk timeline
# video_path 视频地址
# timedis 间隔多少s检测一下 默认是5s
def test_video(video_path, timedis=5):
    fps, frame_count, width, height = get_video_info(video_path)
    min_line = int(width / 4)
    print('video info:', fps, frame_count, width, height)
    cap = cv2.VideoCapture(video_path)

    last_flag = False  # 上一次检测的结果
    current_time = 0
    last_frame_index = 0 # 上一次检测的帧序号
    next_frame_index = 0
    # 记录video是否是pk信息的数据结构
    # [[False, 0, 0], [True, 30, 1]]
    # 是否是pk 第几帧开始 第几秒开始
    video_pk_info = []

    while True:
        # out_file_path = 'out/' + str(next_frame_index) + '.png'
        cap.set(cv2.CAP_PROP_POS_FRAMES, next_frame_index)
        ret, frame = cap.read()
        if ret:
            flag, spline_num = cv_test_ispk(frame, min_line, last_flag)
            # 第一次检测一定会记录下来
            if next_frame_index == 0:
                video_pk_info.append([flag, 0, 0])
                print('首帧判定：', [flag, 0, 0])
                cv2.imwrite('out/' +str(flag)+'_'+str(spline_num)+'_'+ str(next_frame_index)+'_'+str(current_time) + '.png', frame)
                last_flag = flag
            else:
                if flag != last_flag:
                    video_pk_info.append([flag, next_frame_index, current_time])
                    print('切换判定：', [flag, next_frame_index, current_time])
                    cv2.imwrite('out/' +str(flag)+'_'+str(spline_num)+'_'+ str(next_frame_index)+'_'+str(current_time) + '.png', frame)
                    last_flag = flag

        last_frame_index = next_frame_index
        if last_frame_index == frame_count-1:
            break
        next_frame_index = last_frame_index + timedis * fps
        current_time += timedis
        if next_frame_index >= frame_count:
            next_frame_index = frame_count-1


    return video_pk_info


def transform_time(sec):
    seconds = sec
    # 转换为时分秒的格式
    time_format = str(timedelta(seconds=seconds))
    return time_format

def split_video(video_path, start_time, end_time, out_path):
    ffmpeg.input(video_path).output(out_path, ss=start_time, to=end_time, c='copy').run()

def split_video_by_video_pk_info(video_pk_info, video_path, out_path_pre):
    start_time = -1
    end_time = 0
    for pk_info in video_pk_info:
        [is_pk, frame_index, current_time] = pk_info
        if not is_pk:
            start_time = current_time
        else:
            end_time = current_time
            if end_time > start_time and start_time != -1:
                split_video(video_path, transform_time(start_time), transform_time(end_time), out_path_pre+str(start_time)+'_'+str(end_time)+'.mp4')
                start_time = -1

if __name__ == '__main__':
    # cv_test_ispk('./3.jpg')
    video_path = './1.flv'
    video_pk_info = test_video(video_path, 60)
    print('video_pk_info:', video_pk_info)
    split_video_by_video_pk_info(video_pk_info, video_path, 'out/')

