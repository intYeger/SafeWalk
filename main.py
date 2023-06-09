import firebase_admin
from firebase_admin import credentials
from firebase_admin import db

import cv2
import serial
import time
import argparse
import numpy as np
import torch
import copy

from numpy import random

from main_utils.make_box import convert_coor
from main_utils.find_sign import traffic_light_recognition
# from main_utils.tracker import tracking

from yolov7.detect import detect
from yolov7.utils.general import check_img_size, check_requirements, non_max_suppression, scale_coords
from yolov7.utils.datasets import letterbox
from yolov7.models.experimental import attempt_load
from yolov7.utils.torch_utils import select_device, time_synchronized


# SOURCE = 'C:/Users/J/Desktop/skku/skku_2023-1/SafeWalk/dataset/PTL_Dataset_876x657/heon_IMG_0575.JPG'
# SOURCE = 'C:/Users/J/Desktop/skku/skku_2023-1/SafeWalk/dataset/PTL_Dataset_876x657/heon_IMG_0521.JPG'
# WEIGHTS_CROSSWALK = 'C:/Users/J/Desktop/skku/skku_2023-1/SafeWalk/epoch_029.pt' 
<<<<<<< HEAD
SOURCE = "http://192.168.107.64:81/stream"
# SOURCE = 'C:/Users/J/Desktop/skku/skku_2023-1/SafeWalk/crosswalk_vid.mp4'
WEIGHTS_CROSSWALK = 'C:/Users/baeju/Desktop/final/SafeWalk/yolov7/epoch_029.pt'
=======
SOURCE = 'http://192.168.107.64:81/stream'
# SOURCE = 'C:/Users/J/Desktop/skku/skku_2023-1/SafeWalk/crosswalk_vid.mp4'

WEIGHTS_CROSSWALK = 'C:/Users/J/Desktop/skku/skku_2023-1/SafeWalk/epoch_029.pt'
>>>>>>> 60384ad14cb946591ff507e2cfa60d25f1923418
# WEIGHTS_SIGN_CAR = 'C:/Users/J/Desktop/skku/skku_2023-1/SafeWalk/yolov7/yolov7x.pt'
# WEIGHTS_SIGN_CAR = 'C:/Users/J/Desktop/skku/skku_2023-1/SafeWalk/yolov7/yolov7x.pt'
WEIGHTS_SIGN_CAR = 'C:/Users/baeju/Desktop/final/SafeWalk/yolov7/yolov7x.pt'


IMG_SIZE = 640
DEVICE = ''   # cuda???
AUGMENT = False
CONF_THRES = 0.25
IOU_THRES = 0.45
CLASSES = None
AGNOSTIC_NMS = False

<<<<<<< HEAD
#Firebase Realtime database access
cred = credentials.Certificate('xxxxxxxxxxxxxxxxxxxxx')
firebase_admin.initialize_app(cred,{
    'databaseURL' : 'https://safe-walk-server-default-rtdb.firebaseio.com/',
    'storageBucket' : "safe-walk-server.appspot.com"
})
=======
# #Firebase Realtime database access
# <<<<<<< JYS
# cred = credentials.Certificate('C:/Users/J/Desktop/skku/skku_2023-1/SafeWalk/safe-walk-server-firebase-adminsdk-7ymx1-f530c53769.json')
# =======
# cred = credentials.Certificate('safe-walk-server-firebase-adminsdk-7ymx1-34616ba0e4.json')
# >>>>>>> master
# firebase_admin.initialize_app(cred,{
#     'databaseURL' : 'https://safe-walk-server-default-rtdb.firebaseio.com/',
#     'storageBucket' : "safe-walk-server.appspot.com"
# })  
>>>>>>> 60384ad14cb946591ff507e2cfa60d25f1923418
dir = db.reference()
dir.update({'Red':0})
dir.update({'Green':0})
dir.update({'No Detection':1})


print("****************************************************************")
print('YOLOv7 INITIALIZING...')
print()

# Initialize
device = select_device(DEVICE)
half = device.type != 'cpu'  # half precision only supported on CUDA

# Load model
model_crosswalk = attempt_load(WEIGHTS_CROSSWALK, map_location=device)  # load FP32 model
model_sign_car = attempt_load(WEIGHTS_SIGN_CAR, map_location=device)    # load FP32 model
stride = int(model_crosswalk.stride.max())  # model stride
imgsz = check_img_size(IMG_SIZE, s=stride)  # check img_size

if half:
    model_crosswalk.half()  # to FP16
    model_sign_car.half()  # to FP16

# Get names and colors
names_crosswalk = model_crosswalk.module.names if hasattr(model_crosswalk, 'module') else model_crosswalk.names
names_sign_car = model_crosswalk.module.names if hasattr(model_crosswalk, 'module') else model_sign_car.names
colors_crosswalk = [[random.randint(0, 255) for _ in range(3)] for _ in names_crosswalk]
colors_sign_car = [[random.randint(0, 255) for _ in range(3)] for _ in names_sign_car]

# Run inference
if device.type != 'cpu':
    model_crosswalk(torch.zeros(1, 3, imgsz, imgsz).to(device).type_as(next(model_crosswalk.parameters())))  # run once
    model_sign_car(torch.zeros(1, 3, imgsz, imgsz).to(device).type_as(next(model_sign_car.parameters())))  # run once

print()
print('Yolo Ready!!!')
print("****************************************************************")
print()

cur_frame = 0
has_crosswalk = 0
now_red = 0
now_green = 0

if __name__ == '__main__':

    vids = cv2.VideoCapture(SOURCE)

    if not vids.isOpened():

        print("****************************************************************")
        print("Server not connected!!")
        print("****************************************************************")
        exit()

    while True:

        cur_frame += 1

        has_crosswalk = 0
        now_red = 0
        now_green = 0

        result, img0 = vids.read()
        img0 = cv2.rotate(img0, cv2.ROTATE_90_COUNTERCLOCKWISE)

        if result == False: break

        # img0 = cv2.imread(SOURCE)  # BGR
        img = letterbox(img0, imgsz, stride=stride)[0]
        img = img[:, :, ::-1].transpose(2, 0, 1)  # BGR to RGB, to 3x416x416
        img = np.ascontiguousarray(img)
        img = torch.from_numpy(img).to(device)
        img = img.half() if half else img.float()  # uint8 to fp16/32
        img /= 255.0  # 0 - 255 to 0.0 - 1.0
        if img.ndimension() == 3:
            img = img.unsqueeze(0)

        with torch.no_grad():
            pred_crosswalk = model_crosswalk(img, augment=False)[0]
            pred_sign_car = model_sign_car(img, augment=False)[0]

        pred_crosswalk = non_max_suppression(pred_crosswalk, conf_thres=0.10)
        pred_sign_car = non_max_suppression(pred_sign_car, conf_thres=0.10, classes=[2, 3, 5, 7, 9])
        #[0].cpu().numpy()

        if len(pred_crosswalk[0]) != 0:

            pred_crosswalk = convert_coor(img.shape[2:], pred_crosswalk, img0.shape)
            has_crosswalk = 1

        if len(pred_sign_car[0]) != 0:

            pred_sign_car = convert_coor(img.shape[2:], pred_sign_car, img0.shape)

        img2 = img0
        for idx in range(len(pred_crosswalk[0])):

            img2 = cv2.rectangle(img0, (int(pred_crosswalk[0][idx][0]), int(pred_crosswalk[0][idx][1])), (int(pred_crosswalk[0][idx][2]), int(pred_crosswalk[0][idx][3])), (0, 200, 0), 2)

        for idx in range(len(pred_sign_car[0])):
            
            if pred_sign_car[0][idx][5] == 9:

                traffic_flag = traffic_light_recognition(img0, int(pred_sign_car[0][idx][0]), int(pred_sign_car[0][idx][1]), int(pred_sign_car[0][idx][2]), int(pred_sign_car[0][idx][3]))
                
                if traffic_flag != -1:
                    img2 = cv2.rectangle(img0, (int(pred_sign_car[0][idx][0]), int(pred_sign_car[0][idx][1])), (int(pred_sign_car[0][idx][2]), int(pred_sign_car[0][idx][3])), (0, 0, 200), 2)

                if now_red != 1 and traffic_flag == 0:
                    now_green = 0
                    now_red = 1
                
                elif now_red != 1 and traffic_flag == 1:
                    now_green = 1
                    now_red = 0

            else:
                img2 = cv2.rectangle(img0, (int(pred_sign_car[0][idx][0]), int(pred_sign_car[0][idx][1])), (int(pred_sign_car[0][idx][2]), int(pred_sign_car[0][idx][3])), (200, 0, 0), 2)
 

        if has_crosswalk == 1:
            if now_red == 1:
                dir.update({'No Detection':0})
                dir.update({'Red':1}) # 건너지 마라
                dir.update({'Green':0})
            elif now_green == 1:
                dir.update({'No Detection':0})
                dir.update({'Red':0}) # 건너라는 신호
                dir.update({'Green':1})
            elif now_red == 1 and now_green == 1:
                dir.update({'No Detection':1}) # 차에 따라서 건너라

        print('cross walk', has_crosswalk)
        print(now_red, now_green)

        cv2.imshow('frame', img2)

        if cv2.waitKey(100) == 27: break
        # cv2.destroyAllWindows()

    print('\n')
    print("Exit Program...")
    
    vids.release()
    cv2.destroyAllWindows()