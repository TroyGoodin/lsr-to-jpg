import click
import errno
import more_itertools
import json
import os
import shutil
import zipfile
from PIL import Image

OUTPUT_PATH = 'output'
EXTRACTED_CONTENT_PATH = 'extracted-lsr-content'
COLOR_MODES = {'jpg': 'RGB', 'png': 'RGBA'}


def extract_lsr_content(input_file_path, extracted_content_path=EXTRACTED_CONTENT_PATH):
    with zipfile.ZipFile(input_file_path, 'r') as zip_ref:
        zip_ref.extractall(extracted_content_path)


def json_file_to_object(path):
    with open(path, 'r') as f:
        data = f.read()

    return json.loads(data)


def generate_images(extracted_content_path=EXTRACTED_CONTENT_PATH, output_path=OUTPUT_PATH, all_combinations=False,
                    background_layer=False, output_type='jpg'):
    lsr_content = json_file_to_object( f"{extracted_content_path}/Contents.json")
    width = lsr_content['properties']['canvasSize']['width']
    height = lsr_content['properties']['canvasSize']['height']
    num_layers = len(lsr_content['layers'])

    combinations = [[i for i in range(1, num_layers + 1)]]
    if all_combinations:
        combinations = [list(subset) for subset in list(more_itertools.powerset(combinations[0])) if subset]
        if background_layer:
            combinations = [subset for subset in combinations if num_layers in subset]
    
    for combination in combinations:
        img = Image.new(COLOR_MODES[output_type], (width, height))

        for layer_num in combination[::-1]:
            layer = lsr_content['layers'][layer_num - 1]
            layer_name = layer['filename']
            layer_content = json_file_to_object(f"{extracted_content_path}/{layer_name}/Contents.json")

            layer_width = layer_content['properties']['frame-size']['width']
            layer_height = layer_content['properties']['frame-size']['height']
            layer_center_x = layer_content['properties']['frame-center']['x']
            layer_center_y = layer_content['properties']['frame-center']['y']

            layer_image_set_content = json_file_to_object(
                f"{extracted_content_path}/{layer_name}/Content.imageset/Contents.json")

            for image in layer_image_set_content['images']:
                image_path = f"{extracted_content_path}/{layer_name}/Content.imageset/{image['filename']}"
                new_img = Image.open(image_path).convert('RGBA')
                img.paste(new_img, (int(layer_center_x - layer_width/2), int(layer_center_y - layer_height/2)), new_img)

        try:
            os.makedirs(output_path)
        except OSError as e:
            if e.errno != errno.EEXIST:
                raise
        
        combination_str = ','.join([str(i) for i in combination])
        img.save(f"{output_path}/{combination_str}.{output_type}")


def cleanup(extracted_content_path=EXTRACTED_CONTENT_PATH):
    shutil.rmtree(extracted_content_path, ignore_errors=True)


@click.command()
@click.argument('input-file-path', type=click.Path(exists=True, dir_okay=False))
@click.option('-o', '--output-path', type=click.Path(file_okay=False, writable=True), default=OUTPUT_PATH,
              help="Directory to output jpg file(s) to")
@click.option('-t', '--output-type', type=click.Choice(['jpg', 'png'], case_sensitive=False), default='jpg', help="Output type")
@click.option('-a', '--all-combinations', type=click.BOOL, default=False, help="For each combination of layers, output a jpg")
@click.option('-b', '--background-layer', type=click.BOOL, default=False,
              help="Always include the background layer in each combination")
def lsr_to_jpg(input_file_path, output_path, all_combinations, background_layer, output_type):
    """Convert an lsr file to a jpg file

    INPUT_FILE_PATH     Must be a valid path to an lsr file
    """
    extracted_content_path = f"{output_path}/{EXTRACTED_CONTENT_PATH}"
    extract_lsr_content(input_file_path, extracted_content_path=extracted_content_path)

    generate_images(extracted_content_path=extracted_content_path, output_path=output_path, all_combinations=all_combinations,
                    background_layer=background_layer, output_type=output_type)

    cleanup(extracted_content_path)


if __name__ == "__main__":
    lsr_to_jpg()
