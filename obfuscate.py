# obfuscate.py

import cv2
import numpy as np
from PIL import Image

def smooth_color_obfuscation(image_path, output_path="obfuscated.png"):
    image = Image.open(image_path).convert("RGB").resize((512, 512))
    img = np.array(image)

    gray = cv2.cvtColor(img, cv2.COLOR_RGB2GRAY)
    blurred = cv2.GaussianBlur(gray, (5, 5), 1.2)
    edges = cv2.Canny(blurred, 40, 100)
    edges = cv2.dilate(edges, np.ones((2, 2), np.uint8), iterations=1)

    edge_mask = np.stack([edges]*3, axis=-1)
    enhanced = cv2.convertScaleAbs(img, alpha=1.1, beta=10)
    composite = cv2.addWeighted(enhanced, 0.85, edge_mask, 0.5, 0)

    cv2.circle(composite, (256, 256), 3, (255, 255, 255), -1)
    Image.fromarray(composite).save(output_path)
