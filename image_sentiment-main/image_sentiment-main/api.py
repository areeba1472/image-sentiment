from fastapi import FastAPI, UploadFile, File
from typing import List, Dict, Any
import os
from PIL import Image, ImageChops, ImageEnhance, ExifTags
import exifread
import numpy as np
import cv2
import tempfile
import shutil
import hashlib
import imagehash
import matplotlib.pyplot as plt
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
import torch
import torchvision.models as models
import torchvision.transforms as transforms
from sklearn.metrics.pairwise import cosine_similarity
import piexif
from hachoir.metadata import extractMetadata
from hachoir.parser import createParser
from datetime import datetime
import io
app = FastAPI()

# Mount folders for static file access
app.mount("/ela_results", StaticFiles(directory="ela_results"), name="ela")
app.mount("/lighting_maps", StaticFiles(directory="lighting_maps"), name="heatmap")
temp_dir = tempfile.gettempdir()
app.mount("/tmp", StaticFiles(directory=temp_dir), name="tmp")
app.mount("/copy_move_maps", StaticFiles(directory="copy_move_maps"), name="copymove")
app.mount("/images", StaticFiles(directory="images"), name="images")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
@app.get("/")
def root():
    return {"message": "Image Sentiment API is up and running"}

# ===== Metadata Extraction =====
def extract_pil_metadata(image_path: str) -> Dict[str, Any]:
    metadata = {}
    try:
        image = Image.open(image_path)
        info = image._getexif()
        if info:
            for tag, value in info.items():
                tag_name = ExifTags.TAGS.get(tag, tag)
                metadata[str(tag_name)] = str(value)
        else:
            metadata['Info'] = "No EXIF metadata found using PIL."
    except Exception as e:
        metadata['Error'] = f"Error reading image with PIL: {e}"
    return metadata

def extract_exifread_metadata(image_path: str) -> Dict[str, Any]:
    metadata = {}
    try:
        with open(image_path, 'rb') as f:
            tags = exifread.process_file(f)
            if tags:
                for tag in tags.keys():
                    metadata[str(tag)] = str(tags[tag])
            else:
                metadata['Info'] = "No EXIF metadata found using exifread."
    except Exception as e:
        metadata['Error'] = f"Error reading image with exifread: {e}"
    return metadata

def extract_piexif_metadata(image_path: str) -> Dict[str, Any]:
    metadata = {}
    try:
        exif_dict = piexif.load(image_path)
        for ifd in exif_dict:
            for tag in exif_dict[ifd]:
                tag_name = piexif.TAGS[ifd][tag]["name"] if tag in piexif.TAGS[ifd] else tag
                value = exif_dict[ifd][tag]
                try:
                    if isinstance(value, bytes):
                        value = value.decode(errors='ignore')
                except Exception:
                    pass
                metadata[f"{ifd}:{tag_name}"] = str(value)
        if not metadata:
            metadata['Info'] = "No EXIF metadata found using piexif."
    except Exception as e:
        metadata['Error'] = f"Error reading image with piexif: {e}"
    return metadata

def extract_all_metadata(image_path: str) -> Dict[str, Any]:
    return {
        "PIL Metadata": extract_pil_metadata(image_path),
        "ExifRead Metadata": extract_exifread_metadata(image_path),
        "Piexif Metadata": extract_piexif_metadata(image_path)
    }
def extract_jpeg_structure_metadata(image_path: str) -> dict:
    try:
        print(f"[DEBUG] Trying to parse: {image_path}")
        parser = createParser(image_path)
        if not parser:
            print("[DEBUG] Parser could not be created")
            return {"Error": f"Could not parse image: {image_path}"}

        with parser:
            metadata = extractMetadata(parser)
        
        if not metadata:
            print("[DEBUG] Metadata extraction returned None")
            return {"Error": "No metadata extracted"}
        
        result = {}
        for item in metadata.exportPlaintext():
            # item is like "- Duration: 2s"
            key_value = item.strip("- ").split(": ", 1)
            if len(key_value) == 2:
                key, value = key_value
                result[key] = value
        
        print(f"[DEBUG] Extracted metadata: {result}")
        return result

    except Exception as e:
        print(f"[ERROR] Failed to extract metadata: {e}")
        return {"Error": str(e)}
def extract_digest_info(image_path: str) -> dict:
    try:
        digest_info = {}

        # Filename
        digest_info["Filename"] = os.path.basename(image_path)

        # Filetime (last modified)
        mtime = os.path.getmtime(image_path)
        digest_info["Filetime"] = datetime.utcfromtimestamp(mtime).strftime('%Y-%m-%d %H:%M:%S GMT')

        # File size
        digest_info["File Size"] = f"{os.path.getsize(image_path):,} bytes"

        # File type
        file_ext = os.path.splitext(image_path)[-1].lower()
        if file_ext == '.jpg' or file_ext == '.jpeg':
            file_type = 'image/jpeg'
        else:
            file_type = f"unknown ({file_ext})"
        digest_info["File Type"] = file_type

        # Image info
        with Image.open(image_path) as img:
            digest_info["Dimensions"] = f"{img.width}x{img.height}"
            digest_info["Color Channels"] = len(img.getbands())
            colors = img.getcolors(maxcolors=2**24)
            if colors:
                digest_info["Unique Colors"] = len(colors)
            else:
                digest_info["Unique Colors"] = "Too many to count"

        # Hashes
        with open(image_path, "rb") as f:
            data = f.read()
            digest_info["MD5"] = hashlib.md5(data).hexdigest()
            digest_info["SHA1"] = hashlib.sha1(data).hexdigest()
            digest_info["SHA256"] = hashlib.sha256(data).hexdigest()

        # First analyzed (current time)
        digest_info["First Analyzed"] = datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S GMT')

        return digest_info

    except Exception as e:
        return {"Error": str(e)}
def get_jpeg_quality_details(image_path):
    try:
        with Image.open(image_path) as img:
            if img.format != "JPEG":
                return {"quality_info": "Not a JPEG image"}
            
            quant_tables = img.quantization  # Dictionary of tables
            q_tables_info = {}

            for table_id, table in quant_tables.items():
                matrix = [table[i:i + 8] for i in range(0, len(table), 8)]
                label = "Luminance" if table_id == 0 else f"Chrominance {table_id}"
                q_tables_info[label] = matrix

            # You can estimate quality based on the luminance table (Q0)
            # This is a rough estimate and not standardized
            luminance = quant_tables.get(0, [])
            estimated_quality = "Unknown"
            if luminance:
                q_sum = sum(luminance)
                if q_sum < 300:
                    estimated_quality = "High (~95-100%)"
                elif q_sum < 500:
                    estimated_quality = "Medium (~75-95%)"
                else:
                    estimated_quality = "Low (<75%)"

            return {
                "quality_estimate": estimated_quality,
                "quantization_tables": q_tables_info
            }

    except Exception as e:
        return {"error": str(e)}

# ===== ELA Analysis =====
def perform_ela(image_path: str, ela_output_folder="ela_results", quality=90) -> str:
    try:
        os.makedirs(ela_output_folder, exist_ok=True)
        original = Image.open(image_path).convert('RGB')
        temp_path = os.path.join(ela_output_folder, "temp.jpg")
        original.save(temp_path, 'JPEG', quality=quality)
        resaved = Image.open(temp_path)
        ela_image = ImageChops.difference(original, resaved)
        extrema = ela_image.getextrema()
        max_diff = max([ex[1] for ex in extrema])
        scale = 255.0 / max_diff if max_diff != 0 else 1
        ela_image = ImageEnhance.Brightness(ela_image).enhance(scale)
        ela_filename = os.path.splitext(os.path.basename(image_path))[0] + "_ela.png"
        ela_output_path = os.path.join(ela_output_folder, ela_filename)
        ela_image.save(ela_output_path)
        return ela_output_path
    except Exception as e:
        return f"Error during ELA for {image_path}: {e}"

# ===== Splicing ELA =====
def generate_splicing_ela(image_path: str, output_folder="ela_results", quality=90) -> str:
    try:
        os.makedirs(output_folder, exist_ok=True)
        original = Image.open(image_path).convert('RGB')
        temp_path = os.path.join(output_folder, "splicing_temp.jpg")
        original.save(temp_path, 'JPEG', quality=quality)
        compressed = Image.open(temp_path)
        ela_image = ImageChops.difference(original, compressed)
        extrema = ela_image.getextrema()
        max_diff = max([ex[1] for ex in extrema])
        scale = 255.0 / max_diff if max_diff != 0 else 1
        ela_image = ImageEnhance.Brightness(ela_image).enhance(scale)
        filename = os.path.splitext(os.path.basename(image_path))[0] + "_splicing_ela.png"
        ela_path = os.path.join(output_folder, filename)
        ela_image.save(ela_path)
        return f"ela_results/{filename}"
    except Exception as e:
        return f"Error generating splicing ELA: {e}"

# ===== Lighting Analysis =====
def analyze_lighting_inconsistencies(image_path: str, output_folder="lighting_maps") -> Dict[str, Any]:
    result = {}
    try:
        os.makedirs(output_folder, exist_ok=True)
        image = cv2.imread(image_path, cv2.IMREAD_COLOR)
        if image is None:
            return {"error": "Could not read image with OpenCV."}
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        kernel_size = 15
        mean = cv2.blur(gray.astype(np.float32), (kernel_size, kernel_size))
        mean_sq = cv2.blur((gray.astype(np.float32) ** 2), (kernel_size, kernel_size))
        variance = mean_sq - (mean ** 2)
        result["mean_local_variance"] = float(np.mean(variance))
        result["std_local_variance"] = float(np.std(variance))
        hist = cv2.calcHist([gray], [0], None, [256], [0, 256])
        result["brightness_histogram"] = hist.flatten().tolist()
        norm_variance = cv2.normalize(variance, None, 0, 255, cv2.NORM_MINMAX).astype(np.uint8)
        heatmap = cv2.applyColorMap(norm_variance, cv2.COLORMAP_JET)
        heatmap_filename = os.path.splitext(os.path.basename(image_path))[0] + "_heatmap.png"
        heatmap_path = os.path.join(output_folder, heatmap_filename)
        cv2.imwrite(heatmap_path, heatmap)
        result["heatmap_path"] = heatmap_path
    except Exception as e:
        result["error"] = f"Lighting analysis failed: {e}"
    return result

# ===== Hashing =====
def calculate_hash(file_path, algo='md5'):
    with open(file_path, "rb") as f:
        data = f.read()
    if algo == 'md5':
        return hashlib.md5(data).hexdigest()
    return hashlib.sha256(data).hexdigest()

def perceptual_hash(file_path):
    img = Image.open(file_path)
    return str(imagehash.phash(img))

# ===== Noise Analysis =====
def visualize_noise(image_path):
    img = cv2.imread(image_path, cv2.IMREAD_GRAYSCALE)
    blurred = cv2.GaussianBlur(img, (5, 5), 0)
    noise_map = cv2.absdiff(img, blurred)
    noise_image_path = os.path.splitext(image_path)[0] + "_noise.png"
    plt.imsave(noise_image_path, noise_map, cmap='gray')
    return f"tmp/{os.path.relpath(noise_image_path, start=tempfile.gettempdir())}"

def region_noise_variation(image_path):
    img = cv2.imread(image_path, cv2.IMREAD_GRAYSCALE)
    h, w = img.shape
    results = []
    for y in range(2):
        for x in range(2):
            region = img[y*h//2:(y+1)*h//2, x*w//2:(x+1)*w//2]
            results.append({f"region_{y}_{x}": round(float(np.std(region)), 2)})
    return results

def lighting_histogram(image_path):
    img = cv2.imread(image_path)
    hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
    hist, _ = np.histogram(hsv[:, :, 2].ravel(), bins=256, range=[0, 256])
    return hist.tolist()

# ===== Copy-Move Forgery =====
def detect_copy_move(image_path, output_folder="copy_move_maps", block_size=32, stride=16, threshold=0.9):
    result = {}
    try:
        os.makedirs(output_folder, exist_ok=True)
        image = cv2.imread(image_path)
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        h, w = gray.shape
        model = models.resnet18(weights=models.ResNet18_Weights.DEFAULT)
        model.eval()
        model = torch.nn.Sequential(*list(model.children())[:-1])
        transform = transforms.Compose([
            transforms.ToPILImage(),
            transforms.Resize((32, 32)),
            transforms.ToTensor(),
        ])
        features, positions = [], []
        def extract_features(patch):
            with torch.no_grad():
                return model(transform(patch).unsqueeze(0)).squeeze().numpy()
        for y in range(0, h - block_size + 1, stride):
            for x in range(0, w - block_size + 1, stride):
                patch = image[y:y+block_size, x:x+block_size]
                features.append(extract_features(patch))
                positions.append((x, y))
        features = np.array(features)
        similarity = cosine_similarity(features)
        detected = []
        for i in range(len(features)):
            for j in range(i+1, len(features)):
                if similarity[i, j] > threshold:
                    detected.append((positions[i], positions[j]))
        for (x1, y1), (x2, y2) in detected:
            cv2.rectangle(image, (x1, y1), (x1 + block_size, y1 + block_size), (0, 255, 0), 2)
            cv2.rectangle(image, (x2, y2), (x2 + block_size, y2 + block_size), (0, 0, 255), 2)
        output_filename = os.path.splitext(os.path.basename(image_path))[0] + "_copymove.png"
        output_path = os.path.join(output_folder, output_filename)
        cv2.imwrite(output_path, image)
        result["copy_move_image_path"] = f"copy_move_maps/{output_filename}"
        result["matched_regions_count"] = len(detected)
    except Exception as e:
        result["error"] = f"Copy-move forgery detection failed: {e}"
    return result

# ===== Endpoint =====
@app.post("/process-images")
async def process_uploaded_images(files: List[UploadFile] = File(...)):
    supported_formats = ('.jpg', '.jpeg', '.png', '.tiff', '.bmp', '.webp')
    results = []
    for uploaded_file in files:
        if not uploaded_file.filename.lower().endswith(supported_formats):
            continue
        with tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(uploaded_file.filename)[1]) as temp_file:
            shutil.copyfileobj(uploaded_file.file, temp_file)
            temp_path = temp_file.name
            save_dir = "images"
            os.makedirs(save_dir, exist_ok=True)
            
            final_image_path = os.path.join(save_dir, uploaded_file.filename)
            shutil.copy(temp_path, final_image_path)

        #image_path = f"images/{uploaded_file.filename}"
        pil_metadata = extract_pil_metadata(temp_path)
        exif_metadata = extract_exifread_metadata(temp_path)
        jpeg_structure_metadata = extract_jpeg_structure_metadata(temp_path)
        ela_image_path = perform_ela(temp_path)
        splicing_ela_path = generate_splicing_ela(temp_path)
        lighting_result = analyze_lighting_inconsistencies(temp_path)
        copy_move_result = detect_copy_move(temp_path)
        md5 = calculate_hash(temp_path, 'md5')
        sha256 = calculate_hash(temp_path, 'sha256')
        perceptual = perceptual_hash(temp_path)
        noise_image_path = visualize_noise(temp_path)
        noise_regions = region_noise_variation(temp_path)
        lighting_hist = lighting_histogram(temp_path)
        digest_info = extract_digest_info(temp_path)
        jpeg_quality_details = get_jpeg_quality_details(temp_path)
        results.append({
        #"image": uploaded_file.filename,
        "source_image_path": f"/images/{uploaded_file.filename}",
        "metadata_pil": pil_metadata,
        "metadata_exifread": exif_metadata,
        "ela_image_path": ela_image_path,
        "lighting_inconsistencies": lighting_result,
        "hashes": {
          "md5": md5,
          "sha256": sha256,
          "perceptual": perceptual
    },
        "noise_analysis": {
        "noise_map_path": noise_image_path,
        "regional_variation": noise_regions
    },
        "lighting_histogram": lighting_hist,
        "copy_move_forgery": {
        "map_path": copy_move_result.get("copy_move_image_path", ""),
        "matches_found": copy_move_result.get("matched_regions_count", 0),
        "error": copy_move_result.get("error", "")
    },
        "splicing_analysis": {
        "ela_splicing_image": splicing_ela_path
    },
        "jpeg_structure_metadata": jpeg_structure_metadata,
        "digest_info": digest_info,
        "jpeg_quality_details": jpeg_quality_details
  
})


    return {"results": results}