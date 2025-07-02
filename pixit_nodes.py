import os
import json
import re
import numpy as np
import torch
from PIL import Image
from PIL.PngImagePlugin import PngInfo

class AnyType(str):
    """A special type that can be connected to any other types"""

    def __ne__(self, __value: object) -> bool:
        return False

any_type = AnyType("*")


class CheckTensorAllZeros:
    @classmethod
    def INPUT_TYPES(s):
        return {
            "required": {
                "mask": ("MASK",),
            }
        }

    RETURN_TYPES = ("BOOLEAN",)
    FUNCTION = "check_zeros"
    CATEGORY = "Pixit Custom Nodes"

    def check_zeros(self, mask):
        print(type(mask))
        print(mask)
        is_zero_tensor = (mask == 0)
        is_all_zeros = is_zero_tensor.all().item()
        return (is_all_zeros,)


class StringToCombo:
    @classmethod
    def INPUT_TYPES(s):
        return {
            "required": {
                "input_string": ("STRING", {"multiline": False, "default": "Option1, Option2, Option3"}),
            }
        }

    RETURN_TYPES = ("COMBO",)
    FUNCTION = "string_to_combo"
    CATEGORY = "Pixit Custom Nodes"

    def string_to_combo(self, input_string):
        options = [s.strip() for s in input_string.split(',')]
        if options:
            return (options[0],)
        else:
            return ("",)


class SplitString:
    @classmethod
    def INPUT_TYPES(s):  
    
        return {"required": {
                    "text": ("STRING", {"multiline": False, "default": "text"}),
                },
                "optional": {
                    "delimiter": ("STRING", {"multiline": False, "default": ","}),
                }            
        }

    RETURN_TYPES = (any_type, any_type, any_type, any_type, "STRING", )
    RETURN_NAMES = ("string_1", "string_2", "string_3", "string_4", "show_help", )    
    FUNCTION = "split"
    CATEGORY = "Pixit Custom Nodes"

    def split(self, text, delimiter=""):
        # Split the text string
        parts = text.split(delimiter)
        strings = [part.strip() for part in parts[:4]]
        string_1, string_2, string_3, string_4 = strings + [""] * (4 - len(strings))            

        show_help = "https://github.com/Suzie1/ComfyUI_Comfyroll_CustomNodes/wiki/Other-Nodes#cr-split-string"

        return (string_1, string_2, string_3, string_4, show_help, )


class SwitchBooleanString:
    CATEGORY = "Logic"
    FUNCTION = "select_string"
    INPUT_TYPES = lambda: {
        "required": {
            "boolean_condition": ("BOOLEAN", {"default": True}),
            "string_if_true": ("STRING", {"multiline": True, "default": ""}),
            "string_if_false": ("STRING", {"multiline": True, "default": ""}),
        },
    }

    RETURN_TYPES = ("STRING",)
    RETURN_NAMES = ("selected_string",)

    def select_string(self, boolean_condition, string_if_true, string_if_false):
        if boolean_condition:
            selected_value = string_if_true
        else:
            selected_value = string_if_false
        return (selected_value,)

    
class ImageSave:
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "images": ("IMAGE", ),
                "output_path": ("STRING", {"default": "", "multiline": False}),
                "filename_prefix": ("STRING", {"default": "Pixit"}),
                "filename_delimiter": ("STRING", {"default":"_"}),
                "filename_number_padding": ("INT", {"default":4, "min":1, "max":9, "step":1}),
                "filename_number_start": (["false", "true"],),
                "extension": (['png', 'jpg', 'jpeg', 'gif', 'tiff', 'bmp'], ),
                "dpi": ("INT", {"default": 300, "min": 1, "max": 2400, "step": 1}),
                "quality": ("INT", {"default": 95, "min": 1, "max": 100, "step": 1}),
                "optimize_image": (["true", "false"],),
                "prompt": ("STRING", {"default": "", "multiline": False}),
            },
        }
    
    RETURN_TYPES = ("STRING",)
    FUNCTION = "save_images"
    OUTPUT_NODE = True 

    def save_images(self, images, output_path='', filename_prefix="Pixit", filename_delimiter='_', extension='png', dpi=300, quality=95, optimize_image="true", prompt="", filename_number_padding=4, filename_number_start='false'):
        delimiter = filename_delimiter
        number_padding = filename_number_padding
        optimize_image = (optimize_image == "true")

        if output_path == '':
            print("Please define an output path")
            return

        if output_path.strip() != '':
            if not os.path.exists(output_path.strip()):
                print(f'The path `{output_path.strip()}` specified doesn\'t exist! Creating directory.')
                os.makedirs(output_path, exist_ok=True)

        # Find existing counter values
        if filename_number_start == 'true':
            pattern = f"(\\d+){re.escape(delimiter)}{re.escape(filename_prefix)}"
        else:
            pattern = f"{re.escape(filename_prefix)}{re.escape(delimiter)}(\\d+)"
        existing_counters = [int(re.search(pattern, filename).group(1)) for filename in os.listdir(output_path) if re.match(pattern, os.path.basename(filename))]
        existing_counters.sort(reverse=True)

        # Set initial counter value
        if existing_counters:
            counter = existing_counters[0] + 1
        else:
            counter = 1

        # Set Extension
        file_extension = '.' + extension
        if file_extension not in ['.png', '.jpg', '.jpeg', '.gif', '.tiff', '.bmp']:
            print(f"The extension `{extension}` is not valid. The valid formats are: {', '.join(sorted(['.png', '.jpg', '.jpeg', '.gif', '.tiff', '.bmp']))}")
            file_extension = ".png"

        output_files = list()
        for idx_img, image in enumerate(images):
            i = 255. * image.cpu().numpy()
            img = Image.fromarray(np.clip(i, 0, 255).astype(np.uint8))

            metadata = PngInfo()
            if prompt.strip() != "":
                metadata.add_text("prompt", json.dumps(prompt))
            exif_data = metadata


            if filename_number_start == 'true':
                file = f"{counter:0{number_padding}}{delimiter}{filename_prefix}{file_extension}"
            else:
                file = f"{filename_prefix}{delimiter}{counter:0{number_padding}}{file_extension}"

            # Save the images
            try:
                output_file = os.path.abspath(os.path.join(output_path, file))
                if extension in ["jpg", "jpeg"]:
                    img.save(output_file, quality=quality, optimize=optimize_image, dpi=(dpi, dpi))
                elif extension == 'png':
                    img.save(output_file, pnginfo=exif_data, optimize=optimize_image)
                elif extension == 'bmp':
                    img.save(output_file)
                elif extension == 'tiff':
                    img.save(output_file, quality=quality, optimize=optimize_image)
                else:
                    img.save(output_file, pnginfo=exif_data, optimize=optimize_image)

                print(f"Image file saved to: {output_file}")
                counter = counter + 1
                output_files.append(output_file)

            except OSError as e:
                print(f'Unable to save file to: {output_file}')
                print(e)
            except Exception as e:
                print('Unable to save file due to the to the following error:')
                print(e)

        return output_files
        


NODE_CLASS_MAPPINGS = {
    "StringToCombo": StringToCombo,
    "SwitchBooleanString": SwitchBooleanString,
    "ImageSave": ImageSave,
    "SplitString": SplitString,
    "CheckTensorAllZeros": CheckTensorAllZeros,
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "StringToCombo": "String to Combo",
    "SwitchBooleanString": "Switch String",
    "ImageSave": "Pixit Image Save",
    "SplitString": "Pixit Split String",
    "CheckTensorAllZeros": "Pixit Check Tensor All Zeros"
}
