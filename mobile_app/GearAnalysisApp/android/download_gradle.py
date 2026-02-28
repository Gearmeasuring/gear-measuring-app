import urllib.request
import os

url = "https://raw.githubusercontent.com/gradle/gradle/v7.5.1/gradle/wrapper/gradle-wrapper.jar"
output_path = "gradle/wrapper/gradle-wrapper.jar"

os.makedirs(os.path.dirname(output_path), exist_ok=True)

print(f"Downloading {url}...")
urllib.request.urlretrieve(url, output_path)
print(f"Saved to {output_path}")
