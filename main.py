
import argparse
import datetime
import re
import subprocess 
from time import sleep
import os
import sys
from os import listdir
from os.path import isfile, join ,splitext , basename
from PIL import Image
import numpy as np

# 视频尾部的垃圾广告时长 需要用户自己手动设置
g_adv_length = 0.0

def extract_AdsImages(file_name,start_at,how_Long="1",extract_pics= "./tmp_pic_%03d.png"): #尝试抽取广告图片
    process = subprocess.Popen(
        ["ffmpeg", "-ss", start_at, "-i", file_name,  "-t", how_Long, "-r", "3", "-q:v", "2", "-f", "image2",  extract_pics], 
        stderr = subprocess.PIPE,
        close_fds = True
    )     # "-r" "1" 帧取1
    sleep(0.8) # 太快 当前目录未更新导致get_Imgfiles返回为空

def get_Imgfiles(rootdir):
    vfs = []
    tmp_f = []
    for fpathe,dirs,fs in os.walk(rootdir):
      for f in fs:
        if os.path.splitext(f)[1]=='.png':
            vfs.append (os.path.join(fpathe,f))
            tmp_f.append(f)
    print(tmp_f)
    return vfs

def cut_VideoAds(file_name,new_name,start_at,how_Long,debug_infor='./d.txt'): 
    process = subprocess.Popen(
        ["ffmpeg", "-ss", start_at, "-t", how_Long, "-i", file_name, "-vcodec", "copy", "-acodec", "copy", new_name], 
        stderr = subprocess.PIPE,
        close_fds = True
    ) 
    output = ""
    iterations = 0
    # ensure the output contains "Duration"
    while(not "start" in output and iterations < 100):
        buffer_read = str(process.stderr.read())
        iterations += 1
        if(buffer_read != "None"):
            output += buffer_read
        #print(iterations)
        sleep(.01)

    with open(debug_infor,"a+") as fn:
        fn.write(output[1:])
        fn.close()
        
    return output

def get_VideoDurationsByName(file_name):
    regex = r"Duration:.+(\d\d:\d\d:\d\d\.\d\d)"
    process = subprocess.Popen(
        ["ffmpeg", "-i", file_name], 
        stderr = subprocess.PIPE,
        close_fds = True
    ) 
    output = ""
    iterations = 0
    # ensure the output contains "Duration"
    while(not "start" in output and iterations < 100):
        buffer_read = str(process.stderr.read())
        iterations += 1
        if(buffer_read != "None"):
            output += buffer_read
        #print(iterations)
        sleep(.01)

    target = output[1:]
    match = re.search(regex, target)
    if match:
        duration = match.group(1)              
    else:
        duration = "00:00:00"
        
    return duration

def get_videofiles(rootdir):
    vfs = []
    for fpathe,dirs,fs in os.walk(rootdir):
      for f in fs:
        if os.path.splitext(f)[1]=='.mp4':
            vfs.append (os.path.join(fpathe,f))
    return vfs

def get_durationfromstring(target):
    durations = []
    fle = len("Duration: 00:06:37.20") 
    fi = 0
    fnext =target.find("Duration",fi)
    while ( fnext  > 0 ):
        if(fnext>0):
            durations.append(target[fnext:fnext+fle])
            fi =  fnext+fle + 1
            fnext =target.find("Duration",fi)
            
def calculate_total(durations):
    total = datetime.timedelta()
    for duration in durations:
        time = datetime.datetime.strptime(duration, "%H:%M:%S.%f")
        time_delta = datetime.timedelta(
            hours = time.hour,
            minutes = time.minute,
            seconds = time.second,
            microseconds = time.microsecond
        )
        total += time_delta
    return total

def get_seconds(duration):
    tar = duration.split(":")
    hours = float(tar[0])
    mins = float(tar[1])
    seconds = float(tar[2])
    return float(hours*3600 + mins * 60 + seconds )
 
def format_TimeStyles(total_seconds):
    minutes, seconds = divmod(total_seconds, 60)
    hours, minutes = divmod(minutes, 60)
    days, hours = divmod(hours, 24)
    tstyle = "{:.0f}:{:.0f}:{:.2f}".format( hours, minutes, seconds)
    print(tstyle)
    return tstyle

def crop_img(pic,size=(50,50,50,50)):
    im = Image.open(pic)
    img_size = im.size
    print(img_size)
    (x,y,w,h) = (10,10,60,60)
    region = im.crop((x,y,w,h))
    basename = os.path.basename(pic).split('.')[0]
    newname = "%s/%s_%s"%(os.path.dirname(pic),basename,"_crop_.png")
    print(newname)
    region.save(newname)                
    
def getGray(image_file):
    tmpls=[]
    for h in range(0, image_file.size[1]):#h
        for w in range(0, image_file.size[0]):#w
            tmpls.append( image_file.getpixel((w,h)) )
    return tmpls

def getAvg(ls):#获取平均灰度值
    return sum(ls)/len(ls)

def getMH(a,b):#比较64个字符有几个字符相同
    dist = 0
    for i in range(0,len(a)):
        if a[i]==b[i]:
            dist=dist+1
    return dist

def getImgHash(fne):
    image_file = Image.open(fne) # 打开
    image_file=image_file.resize((12, 12))#重置图片大小我12px X 12px
    image_file=image_file.convert("L")#转256灰度图
    Grayls=getGray(image_file)#灰度集合
    avg=getAvg(Grayls)#灰度平均值
    bitls=''#接收获取0或1
    #除去变宽1px遍历像素
    for h in range(1, image_file.size[1]-1):#h
        for w in range(1, image_file.size[0]-1):#w
            if image_file.getpixel((w,h))>=avg:#像素的值比较平均值 大于记为1 小于记为0
                bitls=bitls+'1'
            else:
                bitls=bitls+'0'
    return bitls
'''
 m2 = hashlib.md5() 
m2.update(bitls)
 print m2.hexdigest(),bitls
 return m2.hexdigest()
'''

def get_CropImgfiles(rootdir):
    vfs = []
    tmp_f = []
    for fpathe,dirs,fs in os.walk(rootdir):
      for f in fs:
        extension = os.path.splitext(f)[1]
        basename = os.path.basename(f)
        if extension =='.png' :
            if basename.find("_crop_.png")>0:            
                vfs.append (os.path.join(fpathe,f))
                tmp_f.append(f)
    print(tmp_f)
    return vfs


def compute_image_similar(std_sample,file_path):
    ads_sample = std_sample
    a=getImgHash(ads_sample) # standrod base image
    similar_values = []
    extract_imgs = get_CropImgfiles(file_path)
    for target_img in extract_imgs:
        b=getImgHash(target_img)
        compare=getMH(a,b)
        print("%s %s %s%%"%(target_img,u'相似度', compare ))
        similar_values.append(compare)
    similar_nums = 0
    for i in similar_values:
        if i > 60 :
            similar_nums += 1
    similar_pasent =  float(similar_nums / len(similar_values)) * 100.0
    print("similar_pasent = %s%%"%similar_pasent)
    return similar_pasent

def crop_AdsImgs(file_path):
   extract_imgs = get_Imgfiles(file_path)
   for target_img in extract_imgs:
       crop_img(target_img)
       #os.unlink(target_img) #删除
       
def clear_curdir_Images(file_path): #清空图片
   extract_imgs = get_Imgfiles(file_path)
   for target_img in extract_imgs:
       os.unlink(target_img)     

def compute_standord_simple_data(simple_pic):
    ads_rgb = []
    ads_r = []
    ads_rgb,ads_r=get_ImageRGB(simple_pic)
    ads_v_mn = np.mean(ads_rgb)  #axis 不设置值，对 m*n 个数求均值，返回一个实数
    ads_v_1n = np.mean(ads_rgb,0)#axis = 0：压缩行，对各列求均值，返回 1* n 矩阵
    ads_v_m1 = np.mean(ads_rgb,1)#axis =1 ：压缩列，对各行求均值，返回 m *1 矩阵
    ads_v_median = np.median(ads_v_m1) #中位数
    ads_v_variance_mn = np.var(ads_rgb)  #方差
    ads_v_variance_R = np.var(ads_r) #仅查看R的波动情况       
##    print("%5.2f %s  %.2f  %.2f  %.2f"%(ads_v_mn,ads_v_1n,ads_v_median,\
##                        ads_v_variance_mn,ads_v_variance_R))
    return(ads_v_mn,ads_v_1n,ads_v_median,\
                            ads_v_variance_mn,ads_v_variance_R)

def get_ImageRGB(pic):
    c_rgb=[]
    c_r = []
    im = Image.open(pic)
    pix = im.load()
    width = im.size[0]
    height = im.size[1]
    for x in range(width):  # 随机抽取 50个像素的R值判断 与标准广告50个像素的R值相比较
        for y in range(height):
            r, g, b = pix[x, y]
            c_rgb.append([r,g,b])  #[r,0,0] [r,g,b]
            c_r.append([r])
    return c_rgb,c_r
    

def compute_image_similar2(standrod_simple_data,file_path):
    i_rgb = []
    i_r = []
##    ads_rgb = []
##    ads_r = []
    (ads_v_mn,ads_v_1n,ads_v_median,ads_v_variance_mn,ads_v_variance_R) = standrod_simple_data
    #crop_img(ads_sample)    #第一次运行需要制作 Tile样本小图
    video_dir = file_path #  input("work directory : ")
    extract_imgs = get_Imgfiles(video_dir)
    for target_img in extract_imgs:       
        i_rgb,i_r = get_ImageRGB(target_img)
        look_v_mn = np.mean(i_rgb)  #axis 不设置值，对 m*n 个数求均值，返回一个实数
        look_v_1n = np.mean(i_rgb,0)#axis = 0：压缩行，对各列求均值，返回 1* n 矩阵
        look_v_m1 = np.mean(i_rgb,1)#axis =1 ：压缩列，对各行求均值，返回 m *1 矩阵
        look_v_median = np.median(look_v_m1) #中位数
        look_v_variance_mn = np.var(i_rgb)  #方差
        look_v_variance_R = np.var(i_r) #仅查看R的波动情况       
        print("对照数据 %5.2f %25s  %.2f  %.2f  %.2f"%(look_v_mn,look_v_1n,look_v_median,\
                            look_v_variance_mn,look_v_variance_R))
        print("样本数据 %5.2f %25s  %.2f  %.2f  %.2f"%(ads_v_mn,ads_v_1n,ads_v_median,\
                        ads_v_variance_mn,ads_v_variance_R))
        arr_ln = np.array(np.divide(look_v_1n,ads_v_1n)*100)
        arr_ln_percentage = [ "%.2f%%"%x for x in arr_ln]
        (v1,v2,v3,v4,v5) = ((look_v_mn/ads_v_mn)*100,arr_ln_percentage,(look_v_median/ads_v_median)*100,\
                            (look_v_variance_mn/ads_v_variance_mn)*100,(look_v_variance_R/ads_v_variance_R)*100)
        print("相似度   %.2f%% %s  %.2f%%  %.2f%%  波幅%.2f%%"%(v1,v2,v3,v4,v5))
        ret = False
        if (v1>90 and v3>90 and v4>90):
            print("%s 是[垃圾广告]截图"% basename(target_img))
            ret = True
        else:
            print("%s 内无插入广告视频"%basename(target_img))
        print("_______________________________________________________")
        return ret
    
def main():
    global g_adv_length
    included_ads_nums = 0 
    save_result = "./d.txt"
    standrod_simple =  "./ads_sample.png"  # 广告截图标准图片
    standord_v = compute_standord_simple_data(standrod_simple)
    regex = r"Duration:.+(\d\d:\d\d:\d\d\.\d\d)"
    g_adv_length = 6.5 # float(input("In vidoe at tails ,the adverisement duration times Long(ep. 5 seconds input 5 and Enter):"))
    curdir = input("Need to cut video directory : ")
    if  os.path.exists(save_result):
        os.unlink(save_result)
    videofiles = get_videofiles(curdir)
    for file_name in videofiles:
        basename = os.path.basename(file_name)
        videosize = os.path.getsize(file_name)
        ext_name = os.path.splitext(file_name)[1]
        file_path = os.path.dirname(file_name)
        new_name = "%s/%s_%s"%(file_path,basename.split(".")[0],ext_name)
        duration = get_VideoDurationsByName(file_name)        
        start_at = "00:00:00"
        total_seconds = get_seconds(duration)
        how_Long = format_TimeStyles( total_seconds - g_adv_length)
        print("duration=%s\nhow_Long=%s"%(duration,how_Long))
        print("file_name=%s file_path=%s\nbasename=%s\nnew_name=%s"%(file_name,file_path,basename,new_name))
        extract_pic_name = "%s/%s"%(file_path,"tmp_pic_%03d.png")
        #print(extract_pic_name)
        extract_at = format_TimeStyles( total_seconds - g_adv_length + 3 ) # 加3 使刚好落在广告期间
        ads_time_s = "2"
        clear_curdir_Images(file_name)#清空图片
        extract_AdsImages(file_name,extract_at,ads_time_s,extract_pic_name)  # ads_time取广告视频区间任意位置中 2秒 中images
        sleep(1)
        crop_AdsImgs(file_path) #裁剪抽取出来的样本
        similar_value = compute_image_similar2(standord_v,file_path)
        if similar_value == True : #含有广告
            output = cut_VideoAds(file_name,new_name,start_at,how_Long,save_result)
            print("从视频中剔出广告视频,生成新视频文件 [ %s ]"% new_name)
            included_ads_nums  += 1
        print("\n")
    print("\n\n____________")
    print("Total vidoes = %s"% len(videofiles))
    print("Included adversion videos have : %s"%included_ads_nums)
    

if __name__ == "__main__":
    main()







 
