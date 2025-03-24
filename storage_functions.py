from google.cloud import storage


class BucketMngr:

    def __init__(self, project_id, bucket_name):
        storage_client = storage.Client(project=project_id)
        self.bucket = storage_client.bucket(bucket_name)

    def upload_blob(self, source_file_name, destination_blob_name):
        blob = self.bucket.blob(destination_blob_name)
        blob.upload_from_filename(source_file_name)

