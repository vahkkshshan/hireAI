from fer import FER
from fer import Video


def predict(filename):
    video_filename = filename
    video = Video(video_filename)

    # Analyze video, displaying the output
    detector = FER(mtcnn=True)
    raw_data = video.analyze(detector, display=False)
    df = video.to_pandas(raw_data)
    df = df.iloc[:, 1:8]
    df = df * 100
    df_mean = df.mean(axis=0).round(0).astype('int')
    df_positive=((df['happy']+df['surprise']+df['neutral'])/3).round(0)
    df_negative=((df['fear']+df['sad']+df['disgust'])/3).round(0)

    df_pos_neg=((df_positive-df_negative)/df_positive)*100


    return df_mean['angry'], df_mean['disgust'], df_mean['fear'], df_mean['happy'], df_mean['sad'], df_mean['surprise'], df_mean['neutral'],df_pos_neg
