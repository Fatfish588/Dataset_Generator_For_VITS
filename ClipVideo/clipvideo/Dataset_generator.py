from videoclipper import VideoClipper
import os
from tqdm import tqdm
import subprocess
from modelscope.pipelines import pipeline
from modelscope.utils.constant import Tasks
current_directory = os.path.dirname(os.path.abspath(__file__))
inference_pipeline = pipeline(
    task=Tasks.auto_speech_recognition,
    model='damo/speech_paraformer-large-vad-punc_asr_nat-zh-cn-16k-common-vocab8404-pytorch',
    vad_model='damo/speech_fsmn_vad_zh-cn-16k-common-pytorch',
    punc_model='damo/punc_ct-transformer_zh-cn-common-vocab272727-pytorch',
)
video_tools = VideoClipper(inference_pipeline)
STAGE_RECOGNIZE = 1
STAGE_CLIP = 2

# 开始偏移量
START_OST = 0
# 结束偏移量
END_OST = 0

FONT_SIZE = 32
FONT_COLOR = 'white'
ADD_SUB = False
OUTPUT_SRT_FILE = f"{current_directory}/output/srt"
OUTPUT_MP4_FILE = f"{current_directory}/output/mp4/"
OUTPUT_WAV_FILE = f"{current_directory}/output/wav"
INPUT_FILE_PATH = f"{current_directory}/video_files/"

# 获取所有文件
def get_all_files_in_directory(directory):
    print("from : " + str(current_directory))
    file_paths_list = []
    for root, dirs, files in os.walk(directory):
        for file in files:
            file_path = os.path.join(root, file)
            file_paths_list.append(file_path)
    return file_paths_list

# 获取所有的字幕和字幕文件路径
def vidio_recognizing_to_get_srt_list():
    video_list = get_all_files_in_directory(INPUT_FILE_PATH)
    srt_list = []
    srt_file_list = []
    for video_path in tqdm(video_list):
        try:
            res_text, res_srt, state = video_tools.video_recog(video_path)
        except Exception as e:
            print(f"Error processing video {video_path}: {e}")
            continue
        srt_file_name = os.path.splitext(os.path.basename(video_path))[0] + '.srt'
        srt_save_path = os.path.join(OUTPUT_SRT_FILE, srt_file_name)
        srt_list.append(res_srt)
        try:
            with open(srt_save_path, "w") as f:
                f.write(res_srt)
                srt_file_list.append(srt_save_path)
                print(str(srt_save_path) + "写入")
        except Exception as e:
            print(f"Error writing SRT file {srt_save_path}: {e}")
    return srt_list, srt_file_list, state

# 获取所有文字大列表
def extract_subtitle_text_list_from_srt():
    srt_list, srt_file_path_list, state = vidio_recognizing_to_get_srt_list()
    all_srt_text_json = {}
    for srt_file_path in srt_file_path_list:
        single_subtitle_text_list = []
        with open(srt_file_path, "r") as srt_file:
            lines = srt_file.readlines()
            for i in range(2, len(lines), 3):
                subtitle_text = lines[i].strip()
                single_subtitle_text_list.append(subtitle_text)
        mp4_file_path = INPUT_FILE_PATH + os.path.splitext(os.path.basename(srt_file_path))[0] + '.mp4'
        all_srt_text_json.update({str(mp4_file_path): single_subtitle_text_list})
    return all_srt_text_json,state

# 通过文字去剪裁音频并保存
def clip_audio_from_srt():
    all_srt_text_json, state = extract_subtitle_text_list_from_srt()
    for mp4_file_path in all_srt_text_json:
        for one_line_text in all_srt_text_json[mp4_file_path]:
            state["clip_video_file"] = OUTPUT_MP4_FILE + str(one_line_text) + '_clip.mp4'
            video_tools.video_clip(dest_text=str(one_line_text), start_ost=START_OST, end_ost=END_OST, state=state)

# 转换为音频
def mp4_to_wav():
    mp4_files = [f for f in os.listdir(OUTPUT_MP4_FILE) if f.endswith(".mp4")]
    for mp4_file in mp4_files:
        input_path = os.path.join(OUTPUT_MP4_FILE, mp4_file)
        output_file_name = os.path.splitext(mp4_file)[0] + ".wav"
        output_path = os.path.join(OUTPUT_WAV_FILE, output_file_name)
        subprocess.run([
            "ffmpeg", "-i", input_path, "-acodec", "pcm_s16le", "-ar", "16000", output_path
        ])
        print(f"转换完成: {mp4_file} -> {output_file_name}")

    print("批量转换完成！")


# 面函数
if __name__ == '__main__':
    clip_audio_from_srt()
    mp4_to_wav()
