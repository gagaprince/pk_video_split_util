import ffmpeg
from datetime import timedelta
import cv2
import math
import os
import sys
import subprocess


# current_directory = os.getcwd()
executable_path = '/data/home/my_work/pk_video_split_util/cmd/cutvideo'

def get_video_length(video_path):
    cap = cv2.VideoCapture(video_path)
    frames = cap.get(cv2.CAP_PROP_FRAME_COUNT)
    fps = cap.get(cv2.CAP_PROP_FPS)
    video_length = frames / fps
    return video_length

def transform_time(sec):
    seconds = sec
    # 转换为时分秒的格式
    time_format = str(timedelta(seconds=seconds))
    return time_format

def split_video(video_path, start_time, end_time, out_path, is_copy=True):
    docker_video_path = video_path.replace('/Users/wangzidong', '/data/home')
    docker_out_path = out_path.replace('/Users/wangzidong', '/data/home')
    print("video_path", video_path)
    print("out_path", out_path)
    print("docker_video_path", docker_video_path)
    print("docker_out_path", docker_out_path)
    result = subprocess.run(['docker', 'exec', 'ffmpeg_con', executable_path, start_time, end_time, docker_video_path, docker_out_path], capture_output=True, text=True)
    # 打印C程序的标准输出
    print("标准输出:", result.stdout)
    # 打印C程序的标准错误输出
    print("错误输出:", result.stderr)
    # if is_copy:
    #     ffmpeg.input(video_path).output(out_path, ss=start_time, to=end_time, c='copy').run()
    # else:
    #     ffmpeg.input(video_path).output(out_path, ss=start_time, to=end_time).run()


# def split_lite_video(video_path, time_step, out_pre, is_copy=True):
#     os.makedirs(out_pre, exist_ok=True)
#     video_length = get_video_length(video_path)
#     num_clips = math.ceil(video_length / time_step)
#     for i in range(num_clips):
#         start_time = i * time_step
#         end_time = (i + 1) * time_step if (i + 1) * time_step < video_length else video_length
#         output_path = os.path.join(out_pre, "output_{}.mp4".format(i))
#         start_time = max(0, start_time - 1)
#         split_video(video_path, transform_time(start_time), transform_time(end_time), output_path, is_copy)

def split_lite_video(video_path, time_step, out_pre, is_copy=True):
    os.makedirs(out_pre, exist_ok=True)
    video_length = get_video_length(video_path)
    num_clips = math.ceil(video_length / time_step)
    for i in range(num_clips):
        start_time = i * time_step
        end_time = (i + 1) * time_step if (i + 1) * time_step < video_length else video_length
        output_path = os.path.join(out_pre, "output_{}.mp4".format(i))
        split_video(video_path, str(start_time), str(end_time), output_path, is_copy)


def main(video_path, time_step):
    dir_tmp = os.path.dirname(video_path)
    file_name = os.path.splitext(os.path.basename(video_path))[0]
    out_pre = os.path.join(dir_tmp, file_name, 'out_'+str(time_step))
    split_lite_video(video_path, time_step, out_pre)

if __name__ == '__main__':
    main(sys.argv[1], int(sys.argv[2]))