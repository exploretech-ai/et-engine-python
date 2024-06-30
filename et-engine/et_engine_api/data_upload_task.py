import boto3
import os


def upload(s3_bucket, s3_key):    

    destination_path = '/mnt/efs/' + s3_key

    s3_client = boto3.client('s3')

    print('Dowloading...')
    s3_client.download_file(s3_bucket, s3_key, destination_path)
    print(f"success")

    

if __name__ == "__main__":

    s3_bucket = os.environ["s3_bucket"]
    s3_key = os.environ["s3_key"]

    print("UPLOAD REQUESTED TO", s3_bucket)
    print('bucket: ', s3_bucket)
    print('key: ', s3_key)

    upload_result = upload(s3_bucket, s3_key)

