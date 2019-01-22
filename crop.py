
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
import  numpy as np

def get_Imgfiles(rootdir):
    vfs = []
    for fpathe,dirs,fs in os.walk(rootdir):
      for f in fs:
        if os.path.splitext(f)[1]=='.png':
            vfs.append (os.path.join(fpathe,f))
    return vfs

def crop_img(pic,size=(50,50,50,50)):
    im = Image.open(pic)
    img_size = im.size
    print(img_size)
    (x,y,w,h) = (10,10,60,60)
    region = im.crop((x,y,w,h))
    basename = os.path.basename(pic).split('.')[0]
    region.save("%s/%s_%s"%(os.path.dirname(pic),basename,"_crop_.png"))                
    
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
def compute_image_similar(work_dir):
    ads_sample =  "./ads_sample.png"
    a=getImgHash(ads_sample) # standrod base image
    video_dir = work_dir 
    similar_values = []
    extract_imgs = get_Imgfiles(video_dir)
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

def main():
    i_rgb = []
    i_r = []
    ads_sample =  "./ads_sample.png"
    ads_rgb = []
    ads_r = []
    #crop_img(ads_sample)    #第一次运行需要制作 Tile样本小图
    video_dir = "./test" #  input("work directory : ")
    ads_rgb,ads_r=get_ImageRGB(ads_sample)
    ads_v_mn = np.mean(ads_rgb)  #axis 不设置值，对 m*n 个数求均值，返回一个实数
    ads_v_1n = np.mean(ads_rgb,0)#axis = 0：压缩行，对各列求均值，返回 1* n 矩阵
    ads_v_m1 = np.mean(ads_rgb,1)#axis =1 ：压缩列，对各行求均值，返回 m *1 矩阵
    ads_v_median = np.median(ads_v_m1) #中位数
    ads_v_variance_mn = np.var(ads_rgb)  #方差
    ads_v_variance_R = np.var(ads_r) #仅查看R的波动情况       
##    print("%5.2f %s  %.2f  %.2f  %.2f"%(ads_v_mn,ads_v_1n,ads_v_median,\
##                        ads_v_variance_mn,ads_v_variance_R))
    
    extract_imgs = get_Imgfiles(video_dir)
    for target_img in extract_imgs:       
    #crop_img(target_img)
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
        if (v1>90 and v3>90 and v4>90):
            print("%s 是[垃圾广告]截图"% basename(target_img))
        else:
            print("%s 内无插入广告视频"%basename(target_img))
        print("_______________________________________________________")
        #compute_image_similar(video_dir)
              
if __name__ == "__main__":
    main()
