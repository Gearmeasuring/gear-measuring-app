from PIL import Image
import sys

def make_transparent(input_path, output_path):
    img = Image.open(input_path)
    img = img.convert("RGBA")
    datas = img.getdata()

    new_data = []
    for item in datas:
        # Change all white (also shades of whites) pixels to transparent
        if item[0] > 200 and item[1] > 200 and item[2] > 200:
            new_data.append((255, 255, 255, 0))
        else:
            new_data.append(item)

    img.putdata(new_data)
    img.save(output_path, "PNG")
    print(f"Saved transparent image to {output_path}")

if __name__ == "__main__":
    input_path = r"C:/Users/Administrator/.gemini/antigravity/brain/d0acefa3-b89e-4299-b4ab-01eca8a4e09c/spacing_tolerance_icon_transparent_1764722118035.png"
    output_path = r"e:\python\gear measuring software - 20251202\gear_analysis_refactored\ui\resources\spacing_tolerance_icon.png"
    make_transparent(input_path, output_path)
