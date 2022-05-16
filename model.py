from fer import FER
from fer import Video
import cv2


# img = cv2.imread("pic/rami.jpg")
# detector = FER(mtcnn=True)
# results=detector.detect_emotions(img)
# print(results)
#
# video_filename = "pic/test3.mp4"
# video = Video(video_filename)
#
# # Analyze video, displaying the output
# detector = FER(mtcnn=True)
# raw_data = video.analyze(detector, display=False)
# df = video.to_pandas(raw_data)
# print(df)

def predict(filename):
    video_filename = filename
    video = Video(video_filename)

    # Analyze video, displaying the output
    detector = FER(mtcnn=True)
    raw_data = video.analyze(detector, display=True)
    df = video.to_pandas(raw_data)
    df_mean = df.iloc[:, 1:7].mean(axis=0)
    print(df)
    return df_mean['angry'], df_mean['disgust'], df_mean['fear'], df_mean['happy'], df_mean['sad'], df_mean['surprise'], df_mean['neutral']


