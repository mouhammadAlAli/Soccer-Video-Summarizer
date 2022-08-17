import pytesseract
import cv2
import numpy as np
import json
import PIL
import re
import os

from moviepy.editor import *
from moviepy.video.io.ffmpeg_tools import ffmpeg_extract_subclip

pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'


class Train:

    def __init__(self, filename):
        self.cap = cv2.VideoCapture(filename)
        _, self.initial_frame = self.cap.read()
        self.filename = filename

        self.height, self.width, self.channels = self.initial_frame.shape

        # parameters for filtering
        self.green_thresh = 80
        self.diff_thresh = 60
        self.perc = 0.075

    # returns the "distance" between two pixels
    def dist(self, dest, src):
        val = abs(dest[0] - src[0]) + abs(dest[1] - src[1]) + abs(dest[2] - src[2])
        return val

    # returns the max rgb values of a frame
    def max_rgb(self, frame):
        max_r, max_g, max_b = 0, 0, 0
        for x in range(self.width):
            for y in range(self.height):
                curr = frame[y, x]
                max_r = max(curr[0], max_r)
                max_g = max(curr[1], max_g)
                max_b = max(curr[2], max_b)
        return max_r, max_g, max_b

    # preprocessing step: filters out the grass on the soccer field and returns a filtered frame
    def preprocess(self, frame):
        filtered_frame = frame.copy()
        max_r, max_g, max_b = self.max_rgb(frame)
        for x in range(self.width):
            for y in range(self.height):
                curr = frame[y, x]
                if curr[1] > self.green_thresh and curr[0] > max_r * self.perc and curr[1] > max_g * self.perc and curr[2] > max_b * self.perc:
                    filtered_frame[y, x] = [0, 0, 0]
                else:
                    filtered_frame[y, x] = [255, 255, 255]
        filtered_frame = cv2.cvtColor(filtered_frame, cv2.COLOR_BGR2GRAY)
        return filtered_frame

    # performs a morphology expansion on the image
    def morphology_expansion(self, y, x, filtered_frame, pre_morph):
        if pre_morph[y, x] != 255:
            return filtered_frame
        for i in range(-1, 2):
            for j in range(-1, 2):
                in_height = y + i > 0 and y + i <= self.height - 1
                in_width = x + j >= 0 and x + j <= self.width - 1
                if in_height and in_width:
                    filtered_frame[y + i][x + j] = 255
                if in_height and not in_width:
                    filtered_frame[y + i][x] = 255
                if in_width and not in_height:
                    filtered_frame[y][x + j] = 255
        return filtered_frame

    # find the rectangle given the processsed binary image
    def find_rect(self, frame):
        contours, bbb = cv2.findContours(frame, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)

        contour = contours[0]
        max_area = 0
        for c in contours:
            if cv2.contourArea(c) > max_area:
                contour = c
                max_area = cv2.contourArea(c)

        rect = cv2.boundingRect(contour)
        return rect

    def num_white_pixels(self, frame):
        rv = 0
        for x in range(self.width):
            for y in range(self.height):
                if frame[y, x] == 255:
                    rv += 1
        return rv

    def train(self, output_filename, display_image=False):
        print("Preprocessing...")
        filtered_frame = self.preprocess(self.initial_frame)
        print("Done reprocessing...")

        print("Running main filter...")
        # main processing
        prev_frame = None
        rv = True
        while rv:
            rv, frame = self.cap.read()
            if not rv:
                break
            num_pix = self.num_white_pixels(filtered_frame)
            if num_pix < 1000:
                break
            if prev_frame is None:
                prev_frame = frame
                continue
            for x in range(self.width):
                for y in range(self.height):
                    curr = frame[y, x]

                    if self.dist(curr.tolist(), prev_frame[y, x].tolist()) < self.diff_thresh and filtered_frame[y, x] == 255:
                        filtered_frame[y, x] = 255
                    else:
                        filtered_frame[y, x] = 0
            prev_frame = frame
        print("Done running main filer...")

        print("Postprocessing...")
        pre_morph_frame = filtered_frame.copy()
        for i in range(self.width):
            for j in range(self.height):
                filtered_frame = self.morphology_expansion(j, i, filtered_frame, pre_morph_frame)
        print(type(filtered_frame))
        print("Done postprocessing")

        print("Finding box")
        rect = self.find_rect(filtered_frame)
        print(rect)
        x, y, w, h = rect
        y += 1
        h -= 2
        cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 0), 2)
        print("Done finding box")

        data = {}
        data["video_filename"] = self.filename
        data["x"] = x
        data["y"] = y
        data["w"] = w
        data["h"] = h

        self.trained_data = data

        with open(output_filename, "w") as outfile:
            json.dump(data, outfile)
            outfile.write("\n")
        outfile.close()
        print("Saved data to file")


class Detect:
    goals = []

    def replace_chars(self, text):
        list_of_numbers = re.findall(r'\d+', text)
        result_number = ''.join(list_of_numbers)
        return result_number

    def get_frame_time(self, frame_num):
        if (frame_num <= 30):
            return 1
        if (frame_num % 30 > 0):
            return int(frame_num / 30 + 1)
        else:
            return int(frame_num / 30)

    def __init__(self, data_file):
        self.data_file = data_file
        try:
            with open(data_file) as json_data:
                d = json.load(json_data)
                self.x = d["x"]
                self.y = d["y"]
                self.w = d["w"]
                self.h = d["h"]
                self.video_filename = d["video_filename"]
        except IOError:
            print("There was an error opening your data file!")
            return

    def validateString(self, input):
        blacklist = {'O'}
        stringList = input.split(" ")
        if (len(stringList) >= 4 and (len(stringList[0]) < 2 or len(stringList[3]) < 2)) or len(
                stringList[0].strip()) < 3:
            return ""
        if len(stringList) >= 2:
            if 'O' in stringList[1]:
                stringList[1] = 0
        if len(stringList) >= 3:
            if 'O' in stringList[2]:
                stringList[2] = 0
        if len(stringList[0]) >= 1:  # we already know they length will be greater than 0
            stringList[0] = stringList[0][1:4]
        if len(stringList) >= 4 and len(stringList[3]) >= 4:
            stringList[3] = stringList[3][0:3]
        answer = ""
        for string in stringList:
            answer += str(string) + " "
        # remove the space at the end
        answer.rstrip()
        if len(answer) < 11:
            return ""
        return answer

    def detect(self, video_file):
        cap = cv2.VideoCapture(video_file)
        prev_cropped_frame = None
        frame_num = 0
        h1, h2 = 0, 0
        goals = []
        while cap.isOpened():
            cap.set(1, frame_num)
            rv, frame = cap.read()
            if not rv:
                break
            cropped_frame = frame[self.y:self.y + self.h, self.x:self.x + self.w]
            resized = cv2.resize(cropped_frame, (int(100 / self.h * self.w), 100))
            hsv = cv2.cvtColor(resized, cv2.COLOR_BGR2HSV)
            low = np.array([0, 0, 140])
            high = np.array([360, 150, 255])
            mask = cv2.inRange(hsv, low, high)
            prev_cropped_frame = cropped_frame
            cv2.rectangle(frame, (self.x, self.y), (self.x + self.w, self.y + self.h), (0, 255, 0), 1)
            x = self.validateString(pytesseract.image_to_string(PIL.Image.fromarray(mask)))
            x = self.replace_chars(x)
            if len(x) == 2:
                score_1 = int(x[0])
                score_2 = int(x[1])
                if (score_1 != h1 or score_2 != h2):
                    h1 = score_1
                    h2 = score_2
                    goals.append(self.get_frame_time(frame_num))
                    print('Goal')
                    print(h1, h2)
            frame_num += 30
        return goals
# trainer = Train("goal_detect_module/Input")
# trainer.train("goal_detect_module/Input/Orig.txt", True)
# detector = Detect("goal_detect_module/Input/Orig.txt")
# goals = detector.detect("goal_detect_module/Input/video.mp4")

def extract_goals(path, goals):
    if (len(goals) > 0):
        goal_num = 1
        for goal in goals:
            ffmpeg_extract_subclip(path, goal - 14, goal, targetname='Output/'+ 'Goal_' + str(goal_num) + '.mp4')
            goal_num += 1


def summarize_of_goals():
    L = []
    for root, dirs, files in os.walk("Output/"):

        for file in files:
            if os.path.splitext(file)[1] == '.mp4':
                filePath = os.path.join(root, file)
                video = VideoFileClip(filePath)
                L.append(video)

    final_clip = concatenate_videoclips(L)
    final_clip.to_videofile("Output/Goal_summary.mp4", fps=30, remove_temp=False)