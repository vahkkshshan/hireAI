from fer import FER
from fer import Video
import cv2

# img = cv2.imread("pic/rami.jpg")
# detector = FER(mtcnn=True)
# results=detector.detect_emotions(img)
# print(results)

video_filename = "pic/test3.mp4"
video = Video(video_filename)

# Analyze video, displaying the output
detector = FER(mtcnn=True)
raw_data = video.analyze(detector, display=False)
df = video.to_pandas(raw_data)
print(df)