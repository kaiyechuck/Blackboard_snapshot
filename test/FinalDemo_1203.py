import os
import urllib
import urllib2
import json
import numpy as np
from scipy import misc
from scipy import signal
# import cv2
import base64
from PIL import Image
import time
import datetime
from shutil import copyfile
import sys, getopt
import upload

ts = 0
temp_basebaorddiff = 100
if_erasing = 100
size = 1280, 720
# 0.25 is 25% percent content, 0.03 is experiental pixel ratio
newBoardRatio = 0.99*0.25 # for real, use0.03*0.25
changeRatioThre = 0.0004 # experience value, no change at all"0.000111"
# 0=newboard(not mature) 1=mature
canNew = 0
isWhiteBoard = 0
is_local_test = 1
using_base = 0 # using base to segment instead of baidu cloud
# using local macbook to process will take 8 seconds greater than cloud process (5s)
transform = True

# content needs to exceed 25%(newBoardRatio) to create a newboard
current_board = 0
resolution = 720
board_path = "images/"+str(current_board)+"/"
es3_path = "images/cse521/"+str(current_board)+".jpg"
time_stamp = datetime.datetime.now()
last_capture_time = datetime.datetime.now()
path_dictionary = {
    "new": "N/A",
    "old": "N/A",
    "base": "N/A",
    "thumb": "N/A",
    "alpha_positive": "N/A",
    "dealpha": "N/A",
    "diff_coded": "N/A",
    "temp": "N/A",
    "before_erasing": "N/A"
}
"""
topics to could:
    current_board
    last time_stamp
"""


def transformImg(imgPath):

    if transform:
        from transformer import Transformer

        img = Image.open(imgPath)

        tf = Transformer()
        tf.set_dimention(width=size[0], height=size[1])
        print("debug:", size[0], size[1])
        # TODO [Preset]: change the coef before using
        tf.set_coeffs([(0, 0), (size[0], 0), (size[0], size[1]), (0, size[1])],
                     [(64, 0), (size[0], 0), (size[0], size[1]), (318, 309)])
        img = tf.trans(img)
        img.save(imgPath)

    return True

def capture(ts):
    newpath = path_dictionary['new']
    oldpath = path_dictionary['old']
    basepath = path_dictionary['base']
    thumbpath = path_dictionary['thumb']
    if is_local_test:
        import cv2
        if ts == 0:

            cap = cv2.VideoCapture(0) # video capture source camera (Here webcam of laptop)
            time.sleep(0.1) #wait for camera to fully start up
            ret,frame = cap.read() # return a single frame in variable `frame`
            cv2.imwrite(path_dictionary['old'],frame)
            transformImg(path_dictionary['old'])
            # cv2.imwrite('images/0/old.jpg',frame)
            copyfile(oldpath, basepath)

            return 1

        elif ts == 1:

            cap = cv2.VideoCapture(0) # video capture source camera (Here webcam of laptop)
            time.sleep(0.1) #wait for camera to fully start up
            ret,frame = cap.read() # return a single frame in variable `frame`
            cv2.imwrite(newpath,frame)

            im = Image.open(newpath)
            im.thumbnail((200,200))
            im.save(thumbpath, "JPEG")

            transformImg(newpath)

            return 2

        else:

            copyfile(newpath, oldpath)

            cap = cv2.VideoCapture(0) # video capture source camera (Here webcam of laptop)
            time.sleep(0.1) #wait for camera to fully start up
            ret,frame = cap.read() # return a single frame in variable `frame`

            cv2.imwrite(newpath,frame)
            # transformImg(newpath)

            im = Image.open(newpath)
            im.thumbnail((200,200))
            im.save(thumbpath, "JPEG")

            return 2

    else:
        if resolution == 1080:
            res_str = '1920x1080'
        elif resolution == 1440:
            res_str = '2560x1440'
        else:
            res_str = '1280x720'
        if ts == 0:
            myCmd = 'fswebcam -r '+res_str+' '+oldpath
            os.system(myCmd)

            if transform:
                transformImg(oldpath)

            copyfile(oldpath, basepath)

            return 1

        elif ts == 1:
            myCmd = 'fswebcam -r '+res_str+' '+newpath
            os.system(myCmd)

            if transform:
                transformImg(newpath)

            im = Image.open(newpath)
            im.thumbnail((200,200))
            im.save(thumbpath, "JPEG")

            return 2

        else:
            myCmd = 'cp '+newpath+' '+oldpath
            os.system(myCmd)

            myCmd = 'fswebcam -r '+res_str+' '+newpath
            os.system(myCmd)

            # if transform:
            #     transformImg(newpath)

            im = Image.open(newpath)
            im.thumbnail((200,200))
            im.save(thumbpath, "JPEG")

            return 2

    return ts


def getAlpha (content):
    alpha_postive_path = path_dictionary['alpha_positive']
    y = json.loads(content)
    pic = y["scoremap"]
    # print(len(pic))
    decoded = base64.decodestring(pic)
    filename = alpha_postive_path
    with open(filename, 'wb') as handler:
        handler.write(decoded)
        # print("alpha saved")

    # resize to original
    im = Image.open(alpha_postive_path)
    im_resized = im.resize(size, Image.ANTIALIAS)
    im_resized.save(alpha_postive_path, "JPEG")

    return filename


def configBaiduAip (filename, token):
    request_url = "https://aip.baidubce.com/rest/2.0/image-classify/v1/body_seg"
    f = open(filename, 'rb')
    img = base64.b64encode(f.read())

    params = {"image":img, "type":"scoremap"}
    params = urllib.urlencode(params)

    access_token = token
    request_url = request_url + "?access_token=" + access_token
    request = urllib2.Request(url=request_url, data=params)
    request.add_header('Content-Type', 'application/x-www-form-urlencoded')
    response = urllib2.urlopen(request)
    content = response.read()

    return content


def gettoken ():
    host = 'https://aip.baidubce.com/oauth/2.0/token?grant_type=client_credentials&client_id=UWx8MkEyOCwXjpoYfIAQYj3v&client_secret=jZxUnjOVY9GgIyA9jxjvhFiz1EqoP7Ib'
    request = urllib2.Request(host)
    request.add_header('Content-Type', 'application/json; charset=UTF-8')
    response = urllib2.urlopen(request)
    content = response.read()
    if (content):
        # print("BaiduAip newtoken",content)
        y = json.loads(content)
        token = y["access_token"]
        return token
    else:
        print("token error!!!")
        return
    # print(token)

def alpha_conflate (alphaImage, flatSize):
    # note new method do not take flatsize anymore

    t = np.linspace(-30, 30, 90)
    bump = np.exp(-0.1*t**2)
    bump /= np.trapz(bump) # normalize the integral to 1

    # make a 2-D kernel out of it
    kernel = bump[:, np.newaxis] * bump[np.newaxis, :]
    # print("kernel:", kernel)

    img3 = signal.fftconvolve(alphaImage, kernel, mode='same')
    img3 = np.clip(img3, 0, 0.01)*100 #0-1

    return img3


# def newboard(board_no):
#     return 0

def getpath(image_path):
    return board_path+image_path

# def getes3path(image_path):
#     return es3_path+".jpg"

def initpathdic():

    newpath = getpath("new.jpg")
    oldpath = getpath("old.jpg")
    basepath = getpath("base.jpg")
    thumbpath = getpath("thumb.jpg")
    alpha_postive_path = getpath('alpha_positive.jpg')
    dealpha_path = getpath("dealpha.png")
    temp_path = getpath("temp.png")
    diff_coded_path = getpath("diff_coded.jpg")
    before_path = getpath("before_erasing.jpg")
    dic = {
        "new": newpath,
        "old": oldpath,
        "base": basepath,
        "thumb": thumbpath,
        "alpha_positive": alpha_postive_path,
        "dealpha": dealpha_path,
        "diff_coded": diff_coded_path,
        "temp": temp_path,
        "before_erasing":before_path
    }
    print("dic path inited:", dic)
    return dic


def detectIfNew(base_ratio):

    # following logic deals with whether is erasing to create a newboard
    if base_ratio < newBoardRatio:
        if canNew:
            print("[LOG]: Erasing to less than 25% content detected! Creating Newboard")
            # return 1 means "please init a newboard, and reset canew to 0"
            return 1
        else:
            print("[LOG]: this board is not mature")
            # return 2 means "please update canNew to 1"
            return 2

    print("[LOG]: Content exceed 25%, this board is mature")
    # "this board is mature"
    return 0

def getbackraio(new, old, base):
    """
    # 0.25 is newboard_ratio, means:
    #   1. board has to be written more than 25% to start a new board
    #   2. new board will be created when content is lower than 25% again
    # failed to set board boarders will cause fail to get 25% content

    when t=0, take base.jpg
    cannew = 0
    when t>2, compare new and base
    def detectIfNew:
        get new_base pixels: from new to base
        if new_base > 0.25 and cannew == 0:
            cannew = 1
        get old_base pixels: from old to base
        eraseRatio = (new_base-old_base)/all_pixels*-1
        if new_base < 0.25 and cannew == 1:
            # nearly a blank board, waiting for the end of erasing
            if eraseRatio <= 0.01
            # continue check for 3s and 3 times
                if eraseRatio > 0.01
                    reset timer and continue
                if 3s
                    createNewboard()
                    cannew = 0
    """
    new_base = np.subtract(new.astype(int),base.astype(int))
    # old_base = np.subtract(old.astype(int),base.astype(int))

    """
    consider
    new = [1,1,0,0,1,0]
    base = [0,0,0,0,0,0]
    """

    lowerThre = 50
    if isWhiteBoard:
        # for whiteboard
        new_base = new_base*-1

    # erasing content of base pic counts as the same
    np.clip(new_base,0,255)
    new_base_diff = new_base/lowerThre

    new_base_diff = np.clip(new_base_diff, 0, 1)
    # 0-1, 1 for higher than threshold
    # the test result for whole black board is 0.0325(for thre=50 match the pic best)-0.044(for thre=40)
    # little changed part is 0.00137
    back_base_ratio = new_base_diff.mean()

    return back_base_ratio


def detectUpdate(new, old):

    new_old = np.subtract(new.astype(int),old.astype(int))
    lowerThre = 50

    # erasing content of base pic counts as the same
    np.clip(abs(new_old),0,255)
    new_old_diff = new_old/lowerThre

    new_old_diff = np.clip(new_old_diff, 0, 1)
    # 0-1, 1 for higher than threshold
    # the test result for whole black board is 0.0325(for thre=50 match the pic best)-0.044(for thre=40)
    # little changed part is 0.00137
    new_old_ratio = new_old_diff.mean()
    # print("Debuging new_old_ratio:", new_old_ratio)
    if new_old_ratio > changeRatioThre:
        print("Content changing, going to update timestamp")
        return 1

    return 0


#main function starts here
if using_base==0:
    thetoken = gettoken()
else:
    thetoken = "N/A"

n = 10

argv = sys.argv[1:]
try:
    opts, args = getopt.getopt(argv,"hr:",["resolution="])
except getopt.GetoptError:
    print 'GetoptError'
    sys.exit(2)
for opt, arg in opts:
    if opt == '-h':
        print '-r | --resolution 720 or 1080 or 1440'
        sys.exit()
    elif opt in ("-r", "--resolution"):
        resolution = int(arg)

if resolution == 1080:
    size = 1920, 1080
elif resolution == 1440:
    size = 2560, 1440
else:
    size = 1280, 720

# needs to re-sync the current board number from cloud
# FIXME

# Main Function From Here
while n:
    if ts == 0:
        path_dictionary = initpathdic()
        temp_basebaorddiff = 0
        if_erasing = 0
    n = n-1
    ts = capture(ts)
    # print("debug: ", if_erasing, temp_basebaorddiff)

    # clean the human and merge with the oldone
    # getAlpha of human

    if ts == 2:
        # print("debugging, current n = ", n)
        newpic = misc.imread(path_dictionary['new'])
        oldpic = misc.imread(path_dictionary['old'])
        basepic = misc.imread(path_dictionary['base'])
        if detectUpdate(newpic, oldpic):
            time_stamp = datetime.datetime.now()
            # print("time_stamp updated:",time_stamp)

        if using_base & is_local_test:
            import cv2
            import local_process
            print("[LOG]: base processing")
            img = cv2.imread(path_dictionary['thumb'])
            # print("size:", img.shape)
            (H, W) = img.shape[0:2]
            rst = local_process.process_human(img, H, W)
            # print("size rst:", rst.shape)
            # print("test case:", rst[200,:])
            filename = path_dictionary['alpha_positive']
            cv2.imwrite(filename, rst)
            im = Image.open(filename)
            im_resized = im.resize(size, Image.ANTIALIAS)
            im_resized.save(filename, "JPEG")
            print("[LOG]: process completed")

        else:
            thecontent = configBaiduAip(path_dictionary['thumb'], thetoken)
            filename = ''
            if thecontent:
                # print thecontent
                filename = getAlpha(thecontent) #get and save

        alphaImage = misc.imread(filename)
        alphaImage = alpha_conflate(alphaImage, 7)
        # alphaImage = 255-alphaImage
        alphaImage = (1-alphaImage)*255
        misc.imsave(path_dictionary['dealpha'], alphaImage)

        # merge newone(witout human) with oldone
        img1 = Image.open(path_dictionary['new'])
        img2 = Image.open(path_dictionary['dealpha']) #filename for alpha
        img3 = Image.open(path_dictionary['old'])
        img4 = Image.open(path_dictionary['base'])

        mergepic = Image.composite(img1, img3, img2)
        misc.imsave(path_dictionary['temp'], img1)
        misc.imsave(path_dictionary['new'], mergepic)

        if transform:
            transformImg(path_dictionary['temp'])
            transformImg(path_dictionary['new'])

        # diff it with the oldone
        # mergepic = misc.imread('merge.png')
        diff = mergepic - oldpic
        threshold = 20

        diff[abs(diff) < threshold] = 0
        diff[255-abs(diff) < threshold] = 0

        # diff from -255~255, need to compress, mind the way of coding
        diff_coded = (diff+255)/2

        misc.imsave(path_dictionary['diff_coded'], diff_coded)

        if_new_rst = 2

        # handle new baord
        back_ratio = getbackraio(newpic,oldpic,basepic)
        if back_ratio > temp_basebaorddiff*1.01:
        # adding contents and end of the erasing
            temp_basebaorddiff = back_ratio
            if_erasing = 0

        elif back_ratio < temp_basebaorddiff:
            if if_erasing == 0:
            # just erasing return 3 to save current image as temp
                if_erasing = 1
                print("[LOG]: just erasing", back_ratio)
                misc.imsave(path_dictionary['before_erasing'], img3)
                # if_new_rst = 3

        if_new_rst = detectIfNew(back_ratio)


        if if_new_rst == 1:
            # retrive the before erasing picture and upload as final
            # upload.upload_file(path_dictionary['before_erasing'], "boardsnapshot",object_name=es3_path)
            # upload.upload_file(path_dictionary['old'], "boardsnapshot",object_name=es3_path+"test.jpg") # this is uploaded only for testing
            # upload.upload_file(path_dictionary['old'], "boardsnapshot",object_name="test.jpg") # this is uploaded only for testing

            # need to add new board function
            current_board = (current_board+1)%6
            board_path = "images/"+str(current_board)+"/"
            es3_path = "images/cse521/"+str(current_board)+".jpg"
            canNew = 0
            ts = 0

            print("creating new board")

        else:
            # need to handle the upload
            # upload.upload_file(path_dictionary['new'], "boardsnapshot",object_name=es3_path)

            if if_new_rst == 2:
                # not mature, waiting to write enough content
                1
            elif if_new_rst == 0:
                # board is mature
                canNew = 1

            # elif if_new_rst == 3:
            #     # just erasing, save and update
            #     misc.imsave(path_dictionary['before_erasing'], img3)

    time.sleep(0.5)
    current_time = datetime.datetime.now()
    time_span = current_time-last_capture_time
    last_capture_time = current_time
    # print("Image Updated",last_capture_time)
    print("Overall logging:\n" + "  time_stamp:" + str(time_stamp) + "\n  Current_Board:" + str(current_board) + "\n  Time Interval:"+ str(time_span))
    print("----------------")







