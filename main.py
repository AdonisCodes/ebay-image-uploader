import requests
import math
from requests_toolbelt.multipart.encoder import MultipartEncoder
import imghdr
import struct
import xmltodict
import os
import cv2

EBAY_AUTH_TOKEN = 'v^1.1#i^1#p^3#f^0#I^3#r^1#t^Ul4xMF8xMTpCQzVFQUE2NTNFNTkzNzRFNUNFODZBMDU2MEVFQzY1Rl8zXzEjRV4xMjg0'
EBAY_API_URL = "https://api.sandbox.ebay.com/ws/api.dll"

def upload_image(path):
    filename = os.path.basename(path)
    # Set the endpoint URL
    url = EBAY_API_URL

    # Set the headers
    headers = {
        "X-EBAY-API-CALL-NAME": "UploadSiteHostedPictures",
        "X-EBAY-API-SITEID": "0",
        "X-EBAY-API-RESPONSE-ENCODING": "XML",
        "X-EBAY-API-COMPATIBILITY-LEVEL": "967",
        "X-EBAY-API-DETAIL-LEVEL": "0",
        "Cache-Control": "no-cache",
    }

    # Set the XML payload
    xml_payload = f'''
    <?xml version="1.0" encoding="utf-8"?>
    <UploadSiteHostedPicturesRequest xmlns="urn:ebay:apis:eBLBaseComponents">
        <RequesterCredentials>
            <ebl:eBayAuthToken xmlns:ebl="urn:ebay:apis:eBLBaseComponents">TOKEN</ebl:eBayAuthToken>
        </RequesterCredentials>
        <PictureName>{filename}</PictureName>
        <PictureSet>Standard</PictureSet>
        <ExtensionInDays>20</ExtensionInDays>
    </UploadSiteHostedPicturesRequest>
    '''

    # Replace "TOKEN" with your eBay authentication token
    xml_payload = xml_payload.replace("TOKEN", EBAY_AUTH_TOKEN)
    # Create the multipart form-data payload
    multipart_data = MultipartEncoder(
        fields={
            'XML Payload': ('payload.xml', xml_payload, 'text/xml'),
            'Gall-Peters Projection': (path, open(path, 'rb'), 'image/jpeg')
        }
    )

    # Update the headers with the multipart form-data content type
    headers['Content-Type'] = multipart_data.content_type

    # Make the API request
    response = requests.post(url, headers=headers, data=multipart_data)

    # Process the response
    if response.status_code == 200:
        print("Image upload successful!")
    else:
        print("Image upload failed. Status code:", response.status_code)

    return response.text

def get_image_dimensions(file_path):
    # Get the file type
    extension = os.path.splitext(file_path)[1].lower()
    image_extensions = ['.jpg', '.jpeg', '.png', '.tiff']

    if extension not in image_extensions:
        return None, None
    
    image = cv2.imread(file_path)
    width, height, channels = image.shape

    return width, height


def resize_image(path, new_size):
    resized = cv2.imread(path)
    resized = cv2.resize(resized, new_size)
    file = f"resized_{path}"
    cv2.imwrite(file, resized)
    return file

def main(folder_path=None):
    if folder_path is None:
        folder_path = input("What is the folder path: ")
    
    files = []
    if os.path.isfile(folder_path):
        files.append(folder_path)
    
    if os.path.isdir(folder_path):
        f = os.listdir(folder_path)
        for file in f:
            files.append(file)
    
    # Loop over every image...
    for index, file in enumerate(files):
        print(f"[UPLOAD IMAGE] - Uploading image | {index} | {file}")
        # check the image size
        print(f"[WIDTH HEIGHT] - Getting image Dimensions")
        width, height = get_image_dimensions(file)
        if width is None or height is None:
            continue

        # if image added > 15k, continue
        if width + height > 15000:
            print(f"[IMAGE OUT OF BOUNDS] - {width}x{height} | Image to big, scaling down and keeping aspect ratio")
            # Resize the image, save as new name, upload then
            ratio = width / height
            new_width = 1600
            new_height = new_width
            if height != width:
                new_height = math.floor(new_width / ratio)
                
            new_size = (new_width, new_height)
            file = resize_image(file, new_size)
            print(f"[IMAGE RESIZED] - Final image size | {new_size[0]}x{new_size[1]}")

        # upload image
        xml = None
        try:
            print("[UPLOAD ATTEMPT] - Attempting to upload image")
            xml = upload_image(file)
            print("[UPLOAD SUCCESS] - Uploaded image |", file)
        except:
            print("[UPLOAD FAILED] - Failed to upload image |", file)
            continue
        
        print("[WRITING LINK] - Attempting to write link to file")
        writeable_row = None
        if xml is not None:
            xml = xmltodict.parse(xml)
            images = xml.get("UploadSiteHostedPicturesResponse").get("SiteHostedPictureDetails")
            if images is not None:
                # add them to the writeable row
                writeable_row = images.get("FullURL")
                print("[SUCCESS WRITING LINK] - Successfully written link to file |", writeable_row)
        # save the row to the file
        with open("test.txt", 'a') as f:
            f.write(f"{writeable_row}\n")

        print(xml)
main("test.jpg")