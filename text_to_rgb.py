#!/usr/bin/env python

import argparse
from pathlib import Path
import PIL.Image
from main import three_bytes_to_rgb_hex_string


__version__ = '1.1.0'


IGNORED_FOLDER = Path('imgs') / 'upscale'


def get_parser() -> argparse.ArgumentParser:
    """Get this script's parser."""
    parser = argparse.ArgumentParser(description='convert text to colours codes and an image')

    parser.add_argument('--version', action='version', version=__version__)
    parser.add_argument('text', nargs='?', help='the text to convert')
    parser.add_argument('-s', '--scale', type=int, default=1, help='scale up the image this much before saving it')

    return parser


def sanitise_filename(string: str) -> str:
    """Remove non alphanumeric characters."""
    chars_to_remove = []
    for char in string:
        if not char.isalnum():
            chars_to_remove.append(char)
    for char in chars_to_remove:
        string = string.replace(char, '')
    return string


def main():
    """Take input and print the colours then save an image."""
    parser = get_parser()
    args = parser.parse_args()

    if args.text:
        text = args.text
        scale = args.scale
    else:
        text = input('Text: ')
        scale = int(input('Scale: '))
        if not scale:
            scale = args.scale

    text_encoded = text.encode('utf-8')

    padded_length = len(text_encoded) + (3 - len(text_encoded) % 3)
    text_encoded_padded = text_encoded.ljust(padded_length, b' ')

    for i in range(len(text_encoded_padded) // 3):
        colour = three_bytes_to_rgb_hex_string(text_encoded_padded[i*3:i*3 + 3])
        print(colour)

    img_size = (len(text_encoded_padded) // 3, 1)
    img = PIL.Image.frombytes(mode='RGB', size=img_size, data=text_encoded_padded)
    if scale != 1:
        new_size = (img.width*scale, img.height*scale)
        img_scaled = img.resize(new_size, resample=PIL.Image.NEAREST)
    else:
        img_scaled = img
    img_name = f'{sanitise_filename(text)}-utf-8,{scale}x,(,).png'
    img_scaled.save(IGNORED_FOLDER / img_name)


if __name__ == '__main__':
    main()
