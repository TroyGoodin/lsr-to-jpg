import json
import shutil
import sys
import zipfile
from PIL import Image

EXTRACTED_CONTENT_PATH = 'extracted_content'


def extract_lsr_content(source_file_path, destination_path):
    with zipfile.ZipFile(source_file_path, 'r') as zip_ref:
        zip_ref.extractall(destination_path)


def json_file_to_object(path):
    with open(path, 'r') as f:
        data = f.read()

    return json.loads(data)

def generate_image(extracted_content_path):
    lsr_content = json_file_to_object(f"{EXTRACTED_CONTENT_PATH}/Contents.json")
    width = lsr_content['properties']['canvasSize']['width']
    height = lsr_content['properties']['canvasSize']['height']

    img = Image.new('RGB', (width, height))

    for layer in lsr_content['layers'][::-1]:
        layer_name = layer['filename']
        layer_content = json_file_to_object(f"{EXTRACTED_CONTENT_PATH}/{layer_name}/Contents.json")

        layer_width = layer_content['properties']['frame-size']['width']
        layer_height = layer_content['properties']['frame-size']['height']
        layer_center_x = layer_content['properties']['frame-center']['x']
        layer_center_y = layer_content['properties']['frame-center']['y']

        layer_image_set_content = json_file_to_object(f"{EXTRACTED_CONTENT_PATH}/{layer_name}/Content.imageset/Contents.json")

        for image in layer_image_set_content['images']:
            image_path = f"{EXTRACTED_CONTENT_PATH}/{layer_name}/Content.imageset/{image['filename']}"
            new_img = Image.open(image_path)
            img.paste(new_img, (int(layer_center_x - layer_width/2), int(layer_center_y - layer_height/2)), new_img)

    img.save('output.jpg')


def cleanup():
    shutil.rmtree(EXTRACTED_CONTENT_PATH, ignore_errors=True)


def main():
    source_file_path = sys.argv[1]

    extract_lsr_content(source_file_path, EXTRACTED_CONTENT_PATH)
    
    generate_image(EXTRACTED_CONTENT_PATH)

    # cleanup()

if __name__ == "__main__":
    main()