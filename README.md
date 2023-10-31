# Dataset_Generator_For_VITS
基于达摩院视频切割技术的视频转换为短音频的vits数据集生成工具   
A VITS Dataset Generation Tool for Converting Video to Short Audio Based on Damo Academy Video Cutting Technology  

# 介绍
1、本项目基于阿里达摩院FunASR-APP的ClipVideo简单修改制作，其原理是使用ClipVideo通过文字去一个视频中裁剪出对应的那句话的音视频（美妙的技术），并且可以指定音频的开始和结尾偏移量，在中文方面比whisper效果更好，不会出现尾音最后一个音只有一半的情况。  
2、本项目的输出都在根目录下ClipVideo/output/中，包含了切割后的音视频和每个视频对应的字幕文件，需要的话可以使用。  
3、本项目比较简单，所以从输入视频到输出音频数据集是连续的，如果有参数和自己想要的不一样可以自行修改，例如要修改第一条中的偏移量，可在Dataset_generator.py的前半部分修改，默认是不偏移直接截取。  
  
下图是效果展示，使用GPU加速的情况下2两分钟生成600句短音频.  
![7月10日](https://github.com/Fatfish588/Dataset_Generator_For_VITS/assets/59791439/00f57562-798a-4368-921c-6a6886f65d13)

# 更新日志
2023/10/12  
1、现在可以把音频(.wav)和视频(.mp4)一起混合放进video_files中直接运行了！生成器会安排好所有事！  
2、增加了demucs人声分离，现在可以接受浅bgm的视频与音频进行处理，哦对，不可以用在唱中文的背景音乐视频，因为歌词也会被识别并切片。  
3、增加了初始化输目录的功能，生成器会先把除了video_files以外的目录清空再运行，你只需要开始运行就好了，一切交给生成器！  

# 教程
1、克隆此仓库(python版本3.10，3.8往后应该都行)

```bash
git clone https://github.com/Fatfish588/Dataset_Denerator_For_VITS.git
```

创建所需要的目录,windows直接新建文件夹就好了
```bash
mkdir ClipVideo/font
mkdir ClipVideo/clipvideo/video_files
mkdir ClipVideo/clipvideo/output
mkdir ClipVideo/clipvideo/input
mkdir ClipVideo/clipvideo/input/mdx_extra
mkdir ClipVideo/clipvideo/org_wav
mkdir ClipVideo/clipvideo/output/mp4
mkdir ClipVideo/clipvideo/output/srt
mkdir ClipVideo/clipvideo/output/wav
```
此时，这部分结构应该如下图，以下操作都处于Dataset_Generator_For_VITS根目录下   
![image](https://github.com/Fatfish588/Dataset_Generator_For_VITS/assets/59791439/2c6ba932-4a9a-4c7f-902a-26cdfaa50c6b)
  


2、安装环境依赖
```bash
# install modelscope
pip install "modelscope[audio_asr]" -f https://modelscope.oss-cn-beijing.aliyuncs.com/releases/repo.html  
# python environments  
pip install -r ClipVideo/requirments.txt
pip install torchaudio 
pip install demucs~=4.0.0
pip install umap
pip install hdbscan  
# 下载字体（给webUI的字幕镶嵌用的）  
wget https://isv-data.oss-cn-hangzhou.aliyuncs.com/ics/MaaS/ClipVideo/STHeitiMedium.ttc -O ClipVideo/font/STHeitiMedium.ttc  
```    
如果想用GPU加速（尤其是降噪）需要对应的torch和cuda，因为大家的显卡各不相同，这里只提供一个我的作为参考：RTX 4090 + cuda11.7  
```bash
pip install torch==2.0.1+cu117 torchaudio==2.0.2+cu117 torchvision==0.15.2+cu117  --extra-index-url https://download.pytorch.org/whl/cu117
```
3、启动一次webUI，这一步是为了让FunASR-APP自动下载视频转文字的相关模型，此步骤下载模型比较耗时，进度条卡住不动是正常情况，稍等就好，模型来自阿里的服务器，可能需要关掉魔法。  

```bash
python ClipVideo/clipvideo/gradio_service.py
```  
成功打开webUI则说明FunASR-APP的依赖准备完成了  

4、将要处理的音频或视频全部放入video_files目录下，支持多个视频音频混合处理，只要确保都是一个人的声音就好。    
![image](https://github.com/Fatfish588/Dataset_Denerator_For_VITS/assets/59791439/a85784e4-b390-4c5c-b02d-c5cdf50d7e1c)

5、开始运行  

```bash
python ClipVideo/clipvideo/Dataset_generator.py 
```  
6、运行完成后，结果保存在ClipVideo/clipvideo/output/wav目录下  
![image](https://github.com/Fatfish588/Dataset_Generator_For_VITS/assets/59791439/ae24892e-7ab2-43ac-9485-46caf28b9df6)  


# 后续计划
1、添加降噪模型，将支持带背景音乐的视频输入。(已完成)  
2、一键恢复初始化状态，免得每次都要手动清空。（已完成）  
3、优化代码，目前是步骤太多太繁杂了。  
4、从视频一键生成到音频数据集和标注训练集（大概率鸽了）  
# 碎碎念
1、本项目目前只支持中文的，背景音乐不大或者是纯音乐的音频与视频，例如有声书、教程类的视频、科普类视频、虚拟主播的聊天回（天呐她们能和弹幕聊整整6个小时）等等。   
2、本项目只是将长视频生成几秒钟的短音频数据集，减少了手动切片的时间，并不带标注、重采样、生成训练集的功能。    
3、本项目生成的文件名字是Paraformer模型听写出来的，只是用作区分文件而已，并不是百分百准确，不推荐直接拿文件名去当训练集。    
4、请确保ClipVideo/clipvideo/目录下的video_files、output/mp4、output/srt、output/wav这4个目录存在，生成器现在会在每次点击运行时去清空它们，但是需要在第一次运行前先创建好它们，在这之后就不用管它们了。    
5、代码超简单的，每个方法都有备注，有些功能不需要比如降噪部分可以自己修改。    
6、关注永雏塔菲喵，关注永雏塔菲谢谢喵。    
# 相关链接：
[Paraformer视频自动切片与字幕（创空间）———阿里达摩院](https://modelscope.cn/studios/damo/funasr_app_clipvideo/summary)  
[FunASR-APP（GitHub）](https://github.com/alibaba-damo-academy/FunASR-APP)
