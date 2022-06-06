from moviepy.editor import *
from pydub import AudioSegment
from pydub.utils import make_chunks
from os import listdir
from os.path import isfile, join

"""
This example demonstrates how to use `CNN` model from
`speechemotionrecognition` package
"""
from keras.utils import np_utils

from examples.common import extract_data
from speechemotionrecognition.dnn import CNN
from speechemotionrecognition.utilities import get_feature_vector_from_mfcc


def cnn_example():
    audioclip = AudioFileClip(
        "/Users/vahkksh/Documents/thivvyan/Sentiment-Analysis-On-Voice-Data/speechemotionrecognition/testvideo_fer.mp4")
    audioclip.write_audiofile(
        "/Users/vahkksh/Documents/thivvyan/Sentiment-Analysis-On-Voice-Data/speechemotionrecognition/testvideo_fer.wav")
    sound = AudioSegment.from_wav(
        "/Users/vahkksh/Documents/thivvyan/Sentiment-Analysis-On-Voice-Data/speechemotionrecognition/testvideo_fer.wav")
    sound = sound.set_channels(1)
    sound = sound.set_frame_rate(16000)

    chunk_length_ms = 2000  # pydub calculates in millisec
    chunks = make_chunks(sound, chunk_length_ms)  # Make chunks of one sec
    for i, chunk in enumerate(chunks):
        chunk_name = "output/{0}.wav".format(i)
        print("exporting", chunk_name)
        chunk.export(chunk_name, format="wav")

    sound.export("123.wav", format="wav")

    onlyfiles = [f for f in listdir("output") if isfile(join("output", f))]
    print(onlyfiles)

    to_flatten = False
    x_train, x_test, y_train, y_test, num_labels = extract_data(
        flatten=to_flatten)
    y_train = np_utils.to_categorical(y_train)
    y_test_train = np_utils.to_categorical(y_test)
    in_shape = x_train[0].shape
    # x_train = x_train.reshape(x_train.shape[0], in_shape[0], in_shape[1], 1)
    # x_test = x_test.reshape(x_test.shape[0], in_shape[0], in_shape[1], 1)
    print("shaoe; ", x_train[0].shape)
    print("labels; ", num_labels)

    model = CNN(input_shape=x_train[0].shape,
                num_classes=num_labels)
    model.load_model(
        to_load="/Users/vahkksh/Documents/thivvyan/Sentiment-Analysis-On-Voice-Data/models/best_model_CNN.h5")
    # model.train(x_train, y_train, x_test, y_test_train)
    model.evaluate(x_test, y_test)
    filename = '/Users/vahkksh/Documents/thivvyan/Sentiment-Analysis-On-Voice-Data/speechemotionrecognition/123.wav'
    # filename='/Users/vahkksh/Documents/thivvyan/Sentiment-Analysis-On-Voice-Data/dataset/Neutral/03a01Nc.wav'
    for file in onlyfiles:
        print('prediction', model.predict_one(
            get_feature_vector_from_mfcc("output/{}".format(file), flatten=to_flatten)),
              'This is the file prediction')
    print('prediction', model.predict_one(
        get_feature_vector_from_mfcc(filename, flatten=to_flatten)),
          'Actual 3')
    print('CNN Done')


if __name__ == "__main__":
    cnn_example()
