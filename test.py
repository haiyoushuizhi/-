#coding:utf-8
import cv2
import os
import numpy as np
import re
import argparse
import subprocess
from PIL import Image,ImageFont,ImageDraw
from multiprocessing import Pool



ASCII_CHAR=list("$@B%8&WM#*oahkbdpqwmZO0QLCJUYXzcvunxrjft/\|()1{}[]?-_+~<>i!lI;:,\"^`'. ")
char_len=len(ASCII_CHAR)

def video_to_img(video_name):
    '''视频一帧截一张图片'''
    # 判断是否打开
    c=0
    vc = cv2.VideoCapture(video_name)
    if vc.isOpened():
        rval, frame = vc.read()
    else:
        rval=False
    while rval:
        rval,frame=vc.read()
        cv2.imwrite('%05d.jpg'%c,frame)
        c += 1
        if c % 100 == 0:print('已截取'+str(c)+'帧图片')
    print('处理完毕')



def image_to_img(name,SIZE):
    '''图片转为字符串,将字符串写入新建图片'''
    im=Image.open(name)
    width,height=SIZE
    # 图片压缩为原有1/4,减少时间(像素点为原有1/4),Image.NEAREST按最高质量压缩
    w=width//2
    h=height//2
    im=im.resize((w,h),Image.NEAREST)
    
    # 使用numpy库提高效率
    data_color=np.array(im,'f')
    #  gray=int(0.2126 * r + 0.7152 * g + 0.0722 * b)
    a = np.array([0.2126, 0.7152, 0.0722])
    data = (data_color * a).sum(axis=2)
    
    # 新建图片,大小为SIZE
    new_img = Image.new('RGB', size=SIZE, color=(255, 255, 255))
    draw = ImageDraw.Draw(new_img)
    # 设定字符大小,3,4 灰 5 黑
    font = ImageFont.truetype('simsun.ttc', 4)
    
    # 字符只有原有图片像素的1/4,xy设定2个像素大小.与w,h于SIZE的比值对应
    x=y=0
    for i in range(h):
        for j in range(w):
            txt = ASCII_CHAR[int(data[i][j]/256*char_len)]
            if txt:
                draw.text((y, x), txt,'black', font=font)
            y += 2
        x += 2
        y = 0
                
    new_img.save('change_'+ name)


def jpg_to_video(input_name,change_name,FPS,SIZE):
    '''字符图片转为视频'''
    fourcc=cv2.VideoWriter_fourcc(*'MJPG')

    vw=cv2.VideoWriter(change_name,fourcc,FPS,SIZE)
    i=0
    for image in os.listdir(input_name+'_cache'):
        if image.startswith('change'):
            frame=cv2.imread(input_name+'_cache/'+image)
            vw.write(frame)
            if not i%100:print(image+' finish')
            i += 1
    vw.release()

#调用ffmpeg获取mp3音频文件
def video2mp3(video_name,mp3_name):
    subprocess.call('ffmpeg -i '+video_name+' -f mp3 '+mp3_name,shell = True)
#合成音频和视频文件
def video_add_mp3(change_name,mp3_file,output_name):
    subprocess.call('ffmpeg -i '+change_name+' -i '+mp3_file+' -strict -2 -f mp4 '+output_name,shell = True)


def main(video_name,FPS,SIZE):
    input_name=video_name.split('.')[0]
    output_name=input_name+'_output.mp4'
    change_name=input_name+'_change.mp4'
    mp3_name=input_name+'.mp3'
    if not os.path.isfile(output_name):
        if os.path.isfile(change_name) and os.path.isfile(mp3_name):
            video_add_mp3(change_name,mp3_name,output_name)
        else:
            if not os.path.isfile(change_name):
                if not os.path.isfile(input_name + r'_cache\change_02699.jpg'):
                    if not os.path.isfile(input_name + r'_cache\00000.jpg'):
                        if not os.path.isdir(input_name + '_cache'):os.mkdir(input_name + '_cache')
                        os.chdir(input_name + '_cache')
                        video_to_img(video_name)
                        os.chdir('..')
                    os.chdir(input_name + '_cache')
                    i = 0
                    pool=Pool(4)
                    for pic_name in os.listdir():
                        if re.match(r'\d+\.jpg',pic_name) and (not os.path.isfile('change_'+pic_name)):
                            pool.apply_async(func=image_to_img,args=(pic_name,SIZE))
                            i += 1
                            if i % 100 == 0: print('已处理' + str(i) + '张图片')
                    pool.close()
                    pool.join()
                    os.chdir('..')
                jpg_to_video(input_name,change_name, FPS, SIZE)
            if not os.path.isfile(mp3_name):
                video2mp3(video_name,mp3_name)
            video_add_mp3(change_name, mp3_name, output_name)

if __name__ == '__main__':

    '''
    # argparse是Python内置的一个用于命令项选项与参数解析的模块,
    # 命令行启动时,python test.py bad_apple.mp4 -F 29 -W 512 -H 384
    # 输入视频名称,帧数,宽,高.
    # windows中路径中反斜杠与文件名形成转义,
    # 出现以下报错
        warning: Error opening file (/build/opencv/modules/videoio/src/cap_ffmpeg_impl.hpp
        warning: bad_apple.mp4 (/build/opencv/modules/videoio/src/cap_ffmpeg_impl.hpp:809)
    请输入绝对路径,在转义的字符前多加一个反斜杠
    
    # parser=argparse.ArgumentParser()
    # parser.add_argument('file',help='Video file or charvideo file')
    # parser.add_argument('-F','--fps',help='Video file FPS',type=float)
    # parser.add_argument('-W','--width',help='Video file SIZE WIDTH',type=int)
    # parser.add_argument('-H','--height',help='Video file SIZE HEIGHT',type=int)

    # args=parser.parse_args()
    # video_name=args.file
    # FPS=args.fps
    # width=args.width
    # height=args.height
    # SIZE=(width,height)
    '''
    
    '''
    不知道视频帧率,宽高,可以删除注释
    vc=cv2.VideoCapture(video_name)
    FPS=vc.get(cv2.CAP_PROP_FPS)
    SIZE=(int(vc.get(cv2.CAP_PROP_FRAME_WIDTH)),int(vc.get(cv2.CAP_PROP_FRAME_HEIGHT)))
    '''
    
    # 手动查看视频详情,右键
    FPS=29  #实际帧率29.97002997002997,显示的帧数比实际的小,会使转换的视频延长
    SIZE=(512,384)  
    
    print(FPS,SIZE)

    main(video_name,FPS,SIZE)

