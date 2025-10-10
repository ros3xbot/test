from dotenv import load_dotenv
import os

load_dotenv()

BASE_API_URL = os.getenv("BASE_API_URL")
BASE_CIAM_URL = os.getenv("BASE_CIAM_URL")
BASIC_AUTH = os.getenv("BASIC_AUTH")
AX_DEVICE_ID = os.getenv("AX_DEVICE_ID")
AX_FP_KEY = os.getenv("AX_FP_KEY")
UA = os.getenv("UA")
API_KEY = os.getenv("API_KEY")
AES_KEY_ASCII = os.getenv("AES_KEY_ASCII")

def java_like_timestamp(dt):
    return dt.strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3] + "Z"
