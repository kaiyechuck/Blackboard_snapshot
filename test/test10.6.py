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


ts = 0
size = 1280, 720

def capture(ts):
    if ts == 0:
        myCmd = 'fswebcam -r 1280x720 old.jpg'
        os.system(myCmd)
        return 1

    elif ts == 1:
        myCmd = 'fswebcam -r 1280x720 new.jpg'
        os.system(myCmd)

        im = Image.open("new.jpg")
        im.thumbnail((200,200))
        im.save("thumb.jpg", "JPEG")
        return 2

    else:
        myCmd = 'cp new.jpg old.jpg'
        os.system(myCmd)

        myCmd = 'fswebcam -r 1280x720 new.jpg'
        os.system(myCmd)

        im = Image.open("new.jpg")
        im.thumbnail((200,200))
        im.save("thumb.jpg", "JPEG")
        return 2

    return ts


def getAlpha (content):
    y = json.loads(content)
    pic = y["scoremap"]
    # print(len(pic))
    decoded = base64.decodestring(pic)
    filename = 'alpha_positive.jpg'
    with open(filename, 'wb') as handler:
        handler.write(decoded)
        print("alpha saved")

    # resize to original
    im = Image.open("alpha_positive.jpg")
    im_resized = im.resize(size, Image.ANTIALIAS)
    im_resized.save("alpha_positive.jpg", "JEPG")

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
    # flatSize = 7
    kernal = np.zeros((flatSize,flatSize))
    kernal[:,:] = 0.11
    alphaImage = signal.convolve2d(alphaImage, kernal, mode = 'same')
    alphaImage = np.clip(alphaImage,0,0.01) * 100 #0-1
    # alphaImage = 1-alphaImage
    # alphaImage = alphaImage[:,:,np.newaxis]
    # nohumanPic = originPic*alphaImage
    # print("after human decrease:",nohumanPic.shape)
    return alphaImage



thetoken = gettoken()

# Main Function From Here
while True:
    ts = capture(ts)
    # clean the human and merge with the oldone
    # getAlpha of human

    if ts == 2:
        thecontent = configBaiduAip('thumb.jpg', thetoken)
        filename = ''
        if thecontent:
            # print thecontent
            filename = getAlpha(thecontent) #get and save

        alphaImage = misc.imread(filename)
        alphaImage = alpha_conflate(alphaImage, 7)
        alphaImage = 255-alphaImage
        misc.imsave('dealpha.png', alphaImage)

        # merge newone(witout human) with oldone
        img1 = Image.open('new.jpg')
        img2 = Image.open('dealpha.png') #filename for alpha
        img3 = Image.open('old.jpg')
        mergepic = Image.composite(img1, img3, img2)
        misc.imsave('temp.png', img1)
        misc.imsave('new.jpg', mergepic)

        # diff it with the oldone
        # mergepic = misc.imread('merge.png')
        oldpic = misc.imread('old.jpg')
        diff = mergepic - oldpic
        threshold = 20

        diff[abs(diff) < threshold] = 0
        diff[255-abs(diff) < threshold] = 0

        # diff from -255~255, need to compress, mind the way of coding
        diff_coded = (diff+255)/2

        misc.imsave('diff_coded.jpg', diff_coded)

        # need to handle the upload
        # FIXME

    time.sleep(0.5)
    print("Image Updated",datetime.datetime.now())







