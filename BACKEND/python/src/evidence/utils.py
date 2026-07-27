import hashlib
import logging
from hachoir.parser import createParser
from hachoir.metadata import extractMetadata
from hachoir.core import config as hachoir_config
from PIL import Image
from PIL.ExifTags import TAGS, GPSTAGS

# Reducing Hachoir noise to ensure terminal logs only show relevant forensic data.
hachoir_config.quiet = True
logger = logging.getLogger(__name__)

def calculate_sha256(file_obj):
    """
    THE DIGITAL SEAL:
    Generates a SHA-256 cryptographic hash. This acts as the file's unique 
    fingerprint; if even one bit of the file changes, the hash will be different.
    """
    sha256_hash = hashlib.sha256()
    # Resetting file pointer to ensure we scan the file from the very first byte.
    file_obj.seek(0)
    
    # Reading in 4KB chunks to efficiently handle large exhibits like CCTV or audio.
    # The 'iter' approach is memory-efficient and doesn't lock large files.
    for byte_block in iter(lambda: file_obj.read(4096), b""):
        sha256_hash.update(byte_block)
        
    # Resetting the pointer again so subsequent functions can read the file data.
    file_obj.seek(0) 
    return sha256_hash.hexdigest()

def get_gps_data(gps_info):
    """
    GEOLOCATION PARSER:
    Converts raw EXIF GPS coordinates (Degrees, Minutes, Seconds) into 
    standard Decimal Degrees for mapping and legal reporting.
    """
    try:
        parts = {GPSTAGS.get(t, t): v for t, v in gps_info.items()}
        
        def convert_to_degrees(value):
            d = float(value[0])
            m = float(value[1])
            s = float(value[2])
            return d + (m / 60.0) + (s / 3600.0)

        lat = convert_to_degrees(parts['GPSLatitude'])
        # Adjusting for Northern vs. Southern hemisphere.
        if parts['GPSLatitudeRef'] != 'N': lat = 0 - lat
        
        lon = convert_to_degrees(parts['GPSLongitude'])
        # Adjusting for Eastern vs. Western hemisphere.
        if parts['GPSLongitudeRef'] != 'E': lon = 0 - lon
        
        return f"{lat:.5f}, {lon:.5f}"
    except Exception:
        # If coordinates are corrupted or missing, we return None to avoid false data.
        return None

def get_exif_metadata(file_obj):
    """
    IMAGE FORENSICS:
    Digs into the EXIF headers of an image to find the exact capture time, 
    camera model, and GPS data.
    """
    metadata = {'date_time': None, 'device': None, 'gps': None}
    try:
        file_obj.seek(0)
        # --- THE FIX: USE 'with' TO ENSURE THE IMAGE FILE IS CLOSED IMMEDIATELY ---
        with Image.open(file_obj) as img:
            info = img._getexif()
            if info:
                for tag, value in info.items():
                    decoded = TAGS.get(tag, tag)
                    if decoded == 'DateTimeOriginal':
                        metadata['date_time'] = value
                    elif decoded in ('Make', 'Model'):
                        current = metadata.get('device') or ""
                        metadata['device'] = f"{current} {value}".strip()
                    elif decoded == 'GPSInfo':
                        metadata['gps'] = get_gps_data(value)
        # <--- FILE IS RELEASED HERE --->
    except Exception as e:
        print(f"Non-critical metadata error: {e}")
    finally:
        file_obj.seek(0)
    return metadata

def get_media_metadata(file_path):
    """
    MEDIA STREAM ANALYSIS:
    Uses Hachoir to verify the duration and resolution of video or audio.
    """
    metadata_dict = {'duration': None, 'resolution': None}
    try:
        # Creating a parser based on the actual bitstream of the file.
        parser = createParser(file_path)
        if not parser:
            return metadata_dict

        # Hachoir uses its own internal context manager ('with parser') to release the file.
        with parser:
            metadata = extractMetadata(parser)
            if metadata:
                # Extracting runtime for audio/video evidence.
                if metadata.has('duration'):
                    metadata_dict['duration'] = str(metadata.get('duration'))
                # Capturing frame dimensions for visual evidence.
                if metadata.has('width') and metadata.has('height'):
                    metadata_dict['resolution'] = f"{metadata.get('width')}x{metadata.get('height')}"
    except Exception as e:
        print(f"Media extraction error: {e}")
    return metadata_dict