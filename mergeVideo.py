import os.path
import subprocess
def merge_video(oldVideo, aiVideo, outVideo):
    try:
        # 尝试执行的代码
        command = [
            'ffmpeg',
            '-i', oldVideo,
            '-i', aiVideo,
            '-c:v', 'copy',
            '-c:a', 'aac',
            '-strict', 'experimental',
            '-map', '0:a',
            '-map', '1:v',
            outVideo
        ]
        # 调用subprocess运行ffmpeg命令
        subprocess.run(command)
    except Exception as e:
        # 发生异常时执行的代码
        print(e)


def main():
    video_path = '/Users/wangzidong/my_work/share_ffmpeg/merge'
    out_video_path = '/Users/wangzidong/my_work/share_ffmpeg/merge'
    for i in range(1):
        old_video = os.path.join(video_path, str(i)+'.mp4')
        ai_video = os.path.join(video_path, str(i)+'_.mp4')
        out_video = os.path.join(out_video_path, str(i)+'__.mp4')
        print(old_video, ai_video, out_video)
        merge_video(old_video, ai_video, out_video)

if __name__ == '__main__':
    main()