import librosa
import soundfile as sf
from videoclipper import VideoClipper
import os
from tqdm import tqdm
import subprocess
from modelscope.pipelines import pipeline
from modelscope.utils.constant import Tasks
from shutil import copyfile, rmtree

current_directory = os.path.dirname(os.path.abspath(__file__))
inference_pipeline = pipeline(
    task=Tasks.auto_speech_recognition,
    model='damo/speech_paraformer-large-vad-punc_asr_nat-zh-cn-16k-common-vocab8404-pytorch',
    vad_model='damo/speech_fsmn_vad_zh-cn-16k-common-pytorch',
    punc_model='damo/punc_ct-transformer_zh-cn-common-vocab272727-pytorch',
)
video_tools = VideoClipper(inference_pipeline)
audio_clipper = VideoClipper(None)
STAGE_RECOGNIZE = 1
STAGE_CLIP = 2

# 开始偏移量
START_OST = 0
# 结束偏移量
END_OST = 0

FONT_SIZE = 32
FONT_COLOR = 'white'
ADD_SUB = False
OUTPUT_SRT_FILE = f"{current_directory}/output/srt/"
OUTPUT_MP4_FILE = f"{current_directory}/output/mp4/"
OUTPUT_WAV_FILE = f"{current_directory}/output/wav/"
INPUT_FILE_PATH = f"{current_directory}/video_files/"
READY_INPUT_WAV_PATH = f"{current_directory}/input/mdx_extra/"
DEMUCS_TARGET_INPUT_PATH = f"{current_directory}/input/"
ORG_INPUT_WAV_PATH = f"{current_directory}/org_wav/"


# 获取所有文件
def get_all_files_in_directory(directory):
    print(f"from :{current_directory}{directory} ")
    file_paths_list = []
    for root, dirs, files in os.walk(directory):
        for file in files:
            file_path = os.path.join(root, file)
            file_paths_list.append(file_path)
    return file_paths_list


# 获取所有的字幕和字幕文件路径
def vidio_recognizing_to_get_srt_list():
    video_list = get_all_files_in_directory(READY_INPUT_WAV_PATH)
    srt_list = []
    srt_file_list = []
    state_json = {}
    for video_path in tqdm(video_list):
        try:
            wav = librosa.load(video_path, sr=16000)[0]
            res_text, res_srt, state = video_tools.recog((16000, wav))
            state_json.update({str(video_path): state})
        except Exception as e:
            print(f"音频转译错误 {video_path}: {e}")
            continue
        srt_file_name = os.path.splitext(os.path.basename(video_path))[0] + '.srt'
        srt_save_path = os.path.join(OUTPUT_SRT_FILE, srt_file_name)
        srt_list.append(res_srt)
        try:
            with open(srt_save_path, "w", encoding="utf-8") as f:
                f.write(res_srt)
                srt_file_list.append(srt_save_path)
                print(str(srt_save_path) + "写入")
        except Exception as e:
            print(f"Error writing SRT file {srt_save_path}: {e}")
    return srt_list, srt_file_list, state_json


# 视频转音频
def mp4_to_wav(input_path):
    output_file_name = os.path.splitext(os.path.basename(input_path))[0] + '.wav'
    output_path = os.path.join(ORG_INPUT_WAV_PATH, output_file_name)
    subprocess.run([
        "ffmpeg", "-i", input_path, "-acodec", "pcm_s16le", "-ar", "16000", output_path
    ])
    print(f"转换完成: {input_path} -> {output_path}")


# 获取所有文字大列表
def extract_subtitle_text_list_from_srt():
    srt_list, srt_file_path_list, state_json = vidio_recognizing_to_get_srt_list()
    all_srt_text_json = {}
    index = 0
    for srt_file_path in srt_file_path_list:
        single_subtitle_text_list = []
        with open(srt_file_path, "r", encoding="utf-8") as srt_file:
            lines = srt_file.readlines()
            for i in range(2, len(lines), 3):
                subtitle_text = lines[i].strip()
                single_subtitle_text_list.append(subtitle_text)
                index = index + 1
        wav_file_path = READY_INPUT_WAV_PATH + os.path.splitext(os.path.basename(srt_file_path))[0] + '.wav'
        all_srt_text_json.update({str(wav_file_path): single_subtitle_text_list})
    print(f"总文字数量：{index}")
    return all_srt_text_json, state_json


# 通过文字去剪裁音频并保存
def clip_audio_from_srt():
    all_srt_text_json, state_json = extract_subtitle_text_list_from_srt()
    print(str(state_json))
    for wav_file_path in all_srt_text_json:
        for one_line_text in all_srt_text_json[wav_file_path]:
            state = state_json[str(wav_file_path)]
            wav_file_name = OUTPUT_WAV_FILE + str(one_line_text) + '_clip.wav'
            (sr, audio), message, srt_clip = video_tools.clip(dest_text=str(one_line_text), start_ost=START_OST,
                                                              end_ost=END_OST,
                                                              state=state)
            if "No period found in the speech" not in message:
                print(f"{one_line_text} in {wav_file_path}")
                sf.write(wav_file_name, audio, 16000)


# 清空生成物，初始化文件夹
def clean_files():
    rmtree(f"{current_directory}/input/mdx_extra/")
    os.mkdir(f"{current_directory}/input/mdx_extra/")
    rmtree(f"{current_directory}/org_wav/")
    os.mkdir(f"{current_directory}/org_wav/")
    rmtree(f"{current_directory}/output/mp4/")
    os.mkdir(f"{current_directory}/output/mp4/")
    rmtree(f"{current_directory}/output/srt/")
    os.mkdir(f"{current_directory}/output/srt/")
    rmtree(f"{current_directory}/output/wav/")
    os.mkdir(f"{current_directory}/output/wav/")
    print("初始化完成")


# 降噪
def demucs_wav():
    for org_wav_file in get_all_files_in_directory(ORG_INPUT_WAV_PATH):
        target_ready_wav_path = os.path.splitext(os.path.basename(org_wav_file))[0] + ".wav"
        os.system(
            f"demucs -n mdx_extra -o {DEMUCS_TARGET_INPUT_PATH} --filename {target_ready_wav_path} {org_wav_file}")


# 预备……
def ready_all_to_wav():
    files_list = get_all_files_in_directory(INPUT_FILE_PATH)
    for file in files_list:
        audio_suffixs = ['wav']
        video_suffixs = ['mp4']
        if file[-3:] in audio_suffixs:
            target_wav_path = os.path.join(ORG_INPUT_WAV_PATH, os.path.basename(file))
            copyfile(file, target_wav_path)
        elif file[-3:] in video_suffixs:
            mp4_to_wav(file)
        else:
            print(f"只支持.wav和.mp4！Only supports .wav and .mp4")


# 润！
def run():
    clean_files()
    ready_all_to_wav()
    demucs_wav()
    clip_audio_from_srt()


# 面函数
if __name__ == '__main__':
    run()
