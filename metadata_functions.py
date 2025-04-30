import os
import ffmpeg

EXCLUDED_FILES = ['.DS_Store']


class MetaDataLoader:
    def __init__(self):
        pass

    @staticmethod
    def get_metadata(filepath: str):
        metadata = []

        for f in os.listdir(filepath):
            if f not in EXCLUDED_FILES:
                full_path = f"{filepath}{f}"
                metadata.append(MetaDataLoader.load_metadata_from_file(full_path))

        return metadata

    @staticmethod
    def load_metadata_from_file(filepath: str) -> dict:
        metadata = None
        try:
            metadata = ffmpeg.probe(filename=f"{filepath}", cmd='/opt/homebrew/bin/ffprobe')
        except ffmpeg.Error as e:
            print(f'Error {e}')

        return metadata
