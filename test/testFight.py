from transformer import Transformer
import time
import numpy as np

tf = Transformer()
usingCV2 = False #True
resizeScale = 1
points = 0
refPt = []
srcPoints = []
res_str = '1280x720'

# ('points: ', array([[  442.,   570.],
#        [  748.,   570.],
#        [  822.,  1014.],
#        [  326.,  1030.]], dtype=float32))


def start_gather(img):

    global image

    width = int(img.shape[1]*resizeScale)
    heighth = int(img.shape[0]*resizeScale)
    print("img size 0:", img.shape)
    img = cv2.resize(img, (width, heighth))
    print("img size 1:", img.shape)
    image = img
    cv2.namedWindow("testFlight")
    cv2.setMouseCallback("testFlight", click_and_transform)
    cv2.putText(image, "Click Four points to start transform: tl-tr-br-bl", (50,50),cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 0), 2, cv2.LINE_AA)
    cv2.imshow('testFlight',image)
    cv2.waitKey(0)


def click_and_transform(event, x, y, flags, param):

    global points, srcPoints, refPt

    if event == cv2.EVENT_LBUTTONDOWN and points < 6:
        print("x,y:", x, y)
        refPt.append((x, y))
        points += 1

    if len(refPt) > 1 and points < 6:
        cv2.line(image, refPt[-2], refPt[-1], (255, 0, 0), 2)
        cv2.imshow("testFlight", image)

    if event == cv2.EVENT_LBUTTONDOWN and points > 4:
        srcPoints = np.float32(refPt[0:4])*(1/resizeScale)
        cv2.putText(image, "Press ESC to exit, points are in log", (50,200),cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2, cv2.LINE_AA)
        print("points: ", srcPoints*resizeScale)

if usingCV2:
    import cv2
    cap = cv2.VideoCapture(0) # video capture source camera (Here webcam of laptop)
    time.sleep(0.1) #wait for camera to fully start up
    ret,frame = cap.read() # return a single frame in variable `frame`
    # cv2.imwrite(path_dictionary['old'],frame)
    start_gather(frame)
    cap.release()

else:
    import os
    from scipy import misc
    import cv2
    myCmd = 'fswebcam -r 1280x720 testFlight.jpg'
    os.system(myCmd)
    alphaImage = misc.imread('testFlight.jpg')
    img = cv2.imread('testFlight.jpg')
    start_gather(img)

