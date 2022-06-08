import os
import cv2
from datetime import datetime
import uuid
import time


def video_capt(img, out):

    if out == None:
        filename = os.path.join('..', 'data', 'videos', f'video_{datetime.now()}.mp4')
        frames_per_second = 30
        height, width, _ = img.shape
        video_codec = cv2.VideoWriter_fourcc(*'mp4v')
    
        out = cv2.VideoWriter(filename, video_codec, frames_per_second, (width, height))

    out.write(img)

    return out 

def image_capt(img, img_num, dir_path):
    """
    Function to automaticall collect images with the drone.
    """
    print(f'Collecting image {img_num}')
    if img_num == 1:
        dir_path = os.path.join('..', 'data', 'face_detection', 'new', 'not_allocated', f'image_batch_{time.time()}')
        os.mkdir(dir_path)
    img_name = os.path.join(dir_path, f'{str(uuid.uuid1())}.jpg')
    
    cv2.imwrite(img_name, img)
    cv2.circle(img, (180, 120), 10, (0, 255, 0), cv2.FILLED)
    
    img_num += 1
    last_time = time.time()

    return img, img_num, dir_path, last_time
    