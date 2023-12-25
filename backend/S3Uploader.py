import boto3
from botocore.exceptions import NoCredentialsError

class S3Uploader:
    def __init__(self):
        self.bucket_name = "fitme-gag-arsham"
        self.s3_client = boto3.client('s3')

    def upload_file(self, file_path, s3_file_key):
        """
        Uploads a file to an S3 bucket.

        :param file_path: Path to the file to upload.
        :param s3_file_key: S3 object key (path in the bucket).
        :return: URL of the uploaded file, or None if upload failed.
        """
        try:
            self.s3_client.upload_file(file_path, self.bucket_name, s3_file_key)
            presigned_url = self.generate_presigned_url(s3_file_key)
            if presigned_url:
                print(f"Presigned URL: {presigned_url}")
            return presigned_url
        except FileNotFoundError:
            print("The file was not found")
            return None
        except NoCredentialsError:
            print("Credentials not available")
            return None
        
    def generate_presigned_url(self, object_name, expiration=3600):
        """
        Generate a presigned URL to share an S3 object

        :param bucket_name: string
        :param object_name: string
        :param expiration: Time in seconds for the presigned URL to remain valid
        :return: Presigned URL as string. None if error.
        """
        try:
            s3_client = boto3.client('s3')
            response = s3_client.generate_presigned_url('get_object',
                                                        Params={'Bucket': self.bucket_name,
                                                                'Key': object_name},
                                                        ExpiresIn=expiration)
            return response
        except NoCredentialsError:
            print("Credentials not available")
            return None

