# V4 為新增POST API 功能, modify for mic-710aix
import os
import time
import pyaudio
import wave
import requests
from datetime import datetime
from minio import Minio
# from minio.error import ResponseError //"ResponseError" 沒有在使用了
from minio.error import InvalidResponseError

def record_audio(duration, folder):
    CHUNK = 1024
    FORMAT = pyaudio.paInt16
    CHANNELS = 1      # microphone channel
    RATE = 44100
    RECORD_SECONDS = duration

    p = pyaudio.PyAudio()

    stream = p.open(format=FORMAT,
                    channels=CHANNELS,
                    rate=RATE,
                    input=True,
                    frames_per_buffer=CHUNK)

    print("Recording audio...")

    frames = []
    for i in range(0, int(RATE / CHUNK * RECORD_SECONDS)):
        data = stream.read(CHUNK)
        frames.append(data)

    print("Finished recording.")

    stream.stop_stream()
    stream.close()
    p.terminate()

    # Create folder based on current date
    current_date = datetime.now().strftime('%Y-%m-%d')
    folder_path = os.path.join(folder, current_date)
    if not os.path.exists(folder_path):
        os.makedirs(folder_path)

    # Save audio file
    filename = 'recording_M01_' + dtime + '.wav'
    file = os.path.join(folder_path, filename)
    wf = wave.open(file, 'wb')
    wf.setnchannels(CHANNELS)
    wf.setsampwidth(p.get_sample_size(FORMAT))
    wf.setframerate(RATE)
    wf.writeframes(b''.join(frames))
    wf.close()

    # upload to minio
    upload_to_minio(file)

    # POST API
    post_byrestful(filename)

def upload_to_minio(filepath):
    minio_endpoint = 'blobstore.education.wise-paas.com:8888'
    access_key = '836f6e5b71294a50989599f54a63f628'
    secret_key = 'xqDXwM57kYuA01ptpToWbtuj5SzSKAFzc'
    bucket_name = 'ntutony-demo'

    minio_client = Minio(minio_endpoint,
                         access_key=access_key,
                         secret_key=secret_key,
                         secure=False)

    try:
        with open(filepath, 'rb') as file_data:
            file_stat = os.stat(filepath)
            minio_client.put_object(bucket_name,
                                    os.path.basename(filepath),
                                    file_data,
                                    file_stat.st_size)
        print("File uploaded successfully.")
    except InvalidResponseError as err:
        print("Minio Error: ", err)

def post_byrestful(filename):
    url = 'http://127.0.0.1:5000/silic'
    file_name = filename
    data = {"file_name":file_name}
    response = requests.post(url, json=data)

    if response.status_code == 200:
        print('POST success')
    else:
        print('An error occurred:', response.json())
        

if __name__ == '__main__':
    duration = 300                                       # 單位:秒
    dtime = datetime.now().strftime("%Y%m%d_%H%M%S")    # 加上時間命名
    # filename = 'recording_' + dtime + '.wav'
    #folder = '/home/m/audio_record_data/'                              # 於/home/mic-710aix/目錄下
    folder = '/mnt/usb/audio_record_data/'                              # 於/mnt/usb/目錄下
    
    record_audio(duration, folder)
