import cv2
import imutils
from imutils.video import WebcamVideoStream as wvs

hmin = 0
hmax = 360
smin = 0
smax = 255
vmin = 0
vmax = 255

def set_hmin(x):
    global hmin
    hmin = x

def set_hmax(x):
    global hmax
    hmax = x

def set_smin(x):
    global smin
    smin = x

def set_smax(x):
    global smax
    smax = x

def set_vmin(x):
    global vmin
    vmin = x

def set_vmax(x):
    global vmax
    vmax = x

def main():
    cv2.namedWindow("res")

    cv2.createTrackbar("H min", "res", hmin, 360, set_hmin)
    cv2.createTrackbar("H max", "res", hmax, 360, set_hmax)
    cv2.createTrackbar("S min", "res", smin, 255, set_smin)
    cv2.createTrackbar("S max", "res", smax, 255, set_smax)
    cv2.createTrackbar("V min", "res", vmin, 255, set_vmin)
    cv2.createTrackbar("V max", "res", vmax, 255, set_vmax)
    v = wvs(src=0).start()
    while True:
        frame = v.read()
        if frame is None:
            break

        frame = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
        mask = cv2.inRange(frame, (hmin, smin, vmin), (hmax, vmax, smax))
        frame = cv2.bitwise_or(frame, frame, mask=mask)
        frame = cv2.cvtColor(frame, cv2.COLOR_HSV2BGR)
        cv2.imshow("res", frame)

        if cv2.waitKey(1) & 0xFF == ord("q"):
            break
    #v.release()
    cv2.destroyAllWindows()

if __name__ == "__main__":
    main()