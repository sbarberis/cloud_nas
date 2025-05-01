import os
import ffmpeg

EXCLUDED_FILES = ['.DS_Store']


class MetaDataLoader:
    def __init__(self, path: str):
        self.path = path

    def get_metadata(self):
        metadata = []

        for f in os.listdir(self.path):
            if f not in EXCLUDED_FILES:
                full_path = f"{self.path}{f}"
                metadata.append(MetaDataLoader.load_metadata_from_file(full_path))

        return metadata

    @staticmethod
    def load_metadata_from_file(file_path: str) -> dict:
        metadata = None
        try:
            metadata = ffmpeg.probe(filename=f"{file_path}", cmd='/opt/homebrew/bin/ffprobe')
        except ffmpeg.Error as e:
            print(f'Error {e}')

        return metadata
