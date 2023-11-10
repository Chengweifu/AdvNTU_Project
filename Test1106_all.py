# V4 this sample by restful api trigger and store the result to pg, modify for mic-710aix
import pandas as pd, silic
import os
from IPython.display import Image
from minio import Minio
from flask import Flask, request, jsonify
from sqlalchemy import create_engine, MetaData, Table, Column, Integer, String
from datetime import datetime
import shutil
#from google.colab import files

app = Flask(__name__)

@app.route('/silic', methods=['POST'])
def slic_browser():
    try:
        # 获取传入的文件名
        file_name = request.json['file_name']
        #file_name = request.form.get('file_name')
        file_path = file_name
        download_path = "/home/mic-710aix/samples3/"+ file_name       # 设置下载目录
        print("file_path: " +file_path)
        print("download_path: " +download_path)

        # Use local record file
        current_date = datetime.now().strftime('%Y-%m-%d')
        localfile_path = folder + current_date + '/' + file_name
        print("localfile_path: " + localfile_path)
        shutil.copy(localfile_path, download_path)
        
        # download the file from S3
        # minio_client = Minio(minio_endpoint,
        #                     access_key=access_key,
        #                     secret_key=secret_key,
        #                     secure=False)
        # minio_client.fget_object(bucket_name, file_path, download_path)

        # classed by silic
        # os.makedirs(download_path, exist_ok=True)     # 确保下载目录存在
        silic.browser(download_path, model='./exp29', step=1000, targetclasses=targetclasses_m, conf_thres=0.5, zip=False)  # zip=false表示不產生zip檔

        # 调用函数删除特定类型的文件（例如删除路径'./samples3/'下的file）
        delete_specific_files('/home/mic-710aix/samples3/', file_name)
        shutil.rmtree('/home/mic-710aix/result_silic/audio')
        shutil.rmtree('/home/mic-710aix/result_silic/linear')
        shutil.rmtree('/home/mic-710aix/result_silic/rainbow')

        # 
        upload_data_to_postgresql(csv_file_path, database_url, schema_name, table_name, if_exists='replace')

        return jsonify({"message": "Successfully processed the file and restore to pg archive."}), 200
    
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# delete the download file
def delete_specific_files(directory, file_extension):
    # 获取路径下的所有文件和目录列表
    file_list = os.listdir(directory)
    
    # 删除特定类型的文件
    for file in file_list:
        if file.endswith(file_extension):
            
            file_path = os.path.join(directory, file)
            os.remove(file_path)
            print("remove the download file success...")

# Store the result to pg
def upload_data_to_postgresql(csv_file_path, database_url, schema_name, table_name, if_exists='replace'):
    try:
        # 读取 labels.csv 文件
        df = pd.read_csv(csv_file_path)

        # 连接到 PostgreSQL 数据库
        engine = create_engine(database_url)

        # 创建一个新的Schema对象
        schema = MetaData(schema=schema_name)

        # 将数据上传至 PostgreSQL 数据库, 'replace'刪除取代現有資料, 'append'加入新的資料
        #df.to_sql(table_name, engine, schema=schema_name, if_exists=if_exists, index=False)
        df.to_sql(table_name, engine, schema=schema_name, if_exists='append', index=False)

        print('Store to PostgreSQL success!')
    except Exception as e:
        print(f"Error uploading data to PostgreSQL: {str(e)}")

if __name__ == '__main__':
    # Connect to S3 parament
    minio_endpoint = 'blobstore.education.wise-paas.com:8888'
    access_key = '836f6e5b71294a50989599f54a63f628'
    secret_key = 'xqDXwM57kYuA01ptpToWbtuj5SzSKAFzc'
    bucket_name = 'ntutony-demo'
    #file_name = 'recording_20230804_170020.mp3'    # get file name
    #file_path = file_name                          # get file path
    #download_path = "./samples3/"+file_name
    folder = '/mnt/usb/audio_record_data/'          # 於/mnt/usb/目錄下

    # restore to pg parament
    csv_file_path = '/home/mic-710aix/result_silic/label/labels.csv'
    database_url = 'postgresql://188ae346-2065-47af-8df3-a14008cb7f29:ng7t27G4ciAwShQHNN72n0Lce@60.250.255.162:5432/silic-result'
    schema_name = 'silic'
    table_name = 'silic_labels_table'
    targetclasses_m = '1, 11, 12, 28, 29, 35, 40, 41, 72, 73, 76, 77, 78, 85, 86, 103, 105, 110, 126, 187, 199, 202, 235, 290, 307, 308, 313, 315, 316, 320, 330, 332, 333, 340, 341, 342, 344, 383, 419, 420, 459, 463, 465, 468, 553, 554, 555, 563, 565, 566'

    # start the restful 
    app.run(host='0.0.0.0', port=5000)