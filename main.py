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

def get_Imgfiles_and_NotNeedVidoes(rootdir):
    vfs = []
    tmp_f = []
    for fpathe,dirs,fs in os.walk(rootdir):
      for f in fs:
        if os.path.splitext(f)[1]=='.png':
           if os.path.splitext(f)[0] != "ads_sample":                
                vfs.append (os.path.join(fpathe,f))
                tmp_f.append(f)
        elif os.path.splitext(f)[1]=='.mp4':
            target = os.path.basename(f)
            if target.find("_.mp4")>0:
                vfs.append (os.path.join(fpathe,f))
                tmp_f.append(f)
    print(tmp_f)
    return vfs

def clear_curdir_Files(file_path): #清空图片视频
   wait_del_files = get_Imgfiles_and_NotNeedVidoes(file_path)
   for target in wait_del_files:
       os.unlink(target)
       print("Deleted %s"%target)


def main(): 
    curdir = input("Need to clear images and noneed vidoes at directory : ")
    clear_curdir_Files(curdir)
 

if __name__ == "__main__":
    main()
