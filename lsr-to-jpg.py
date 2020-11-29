import click
import errno
import json
import os
import shutil
import zipfile
from PIL import Image

EXTRACTED_CONTENT_PATH = 'extracted-content'
OUTPUT_PATH = 'output'


def extract_lsr_content(input_file_path, extracted_content_path=EXTRACTED_CONTENT_PATH):
    with zipfile.ZipFile(input_file_path, 'r') as zip_ref:
        zip_ref.extractall(extracted_content_path)


def json_file_to_object(path):
    with open(path, 'r') as f:
        data = f.read()

    return json.loads(data)


def generate_image(extracted_content_path=EXTRACTED_CONTENT_PATH, output_path=OUTPUT_PATH):
    lsr_content = json_file_to_object(
        f"{extracted_content_path}/Contents.json")
    width = lsr_content['properties']['canvasSize']['width']
    height = lsr_content['properties']['canvasSize']['height']

    img = Image.new('RGB', (width, height))

    for layer in lsr_content['layers'][::-1]:
        layer_name = layer['filename']
        layer_content = json_file_to_object(
            f"{extracted_content_path}/{layer_name}/Contents.json")

        layer_width = layer_content['properties']['frame-size']['width']
        layer_height = layer_content['properties']['frame-size']['height']
        layer_center_x = layer_content['properties']['frame-center']['x']
        layer_center_y = layer_content['properties']['frame-center']['y']

        layer_image_set_content = json_file_to_object(
            f"{extracted_content_path}/{layer_name}/Content.imageset/Contents.json")

        for image in layer_image_set_content['images']:
            image_path = f"{extracted_content_path}/{layer_name}/Content.imageset/{image['filename']}"
            new_img = Image.open(image_path)
            img.paste(new_img, (int(layer_center_x - layer_width/2),
                                int(layer_center_y - layer_height/2)), new_img)

    try:
        os.makedirs(output_path)
    except OSError as e:
        if e.errno != errno.EEXIST:
            raise
    img.save(f"{output_path}/output.jpg")


def cleanup(extracted_content_path=EXTRACTED_CONTENT_PATH):
    shutil.rmtree(extracted_content_path, ignore_errors=True)


@click.command()
@click.argument('input-file-path', type=click.Path(exists=True, dir_okay=False))
@click.option('-o', '--output-path', type=click.Path(file_okay=False, writable=True), default=OUTPUT_PATH, help="Directory to output jpg file(s) to")
def lsr_to_jpg(input_file_path, output_path):
    """Convert an lsr file to a jpg file

    INPUT_FILE_PATH     Must be a valid path to an lsr file
    """
    extract_lsr_content(input_file_path)

    generate_image(output_path=output_path)

    # cleanup()


if __name__ == "__main__":
    lsr_to_jpg()
