import os
from io import BytesIO
import time
import numpy as np
from typing import List

import uvicorn
import yaml
from fastapi import FastAPI, File, Form, HTTPException, Request, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from PIL import Image, ImageDraw, UnidentifiedImageError
from ultralytics import YOLO
from minio import Minio
from minio.error import S3Error

app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

model = None

minio_client = Minio(
    "s3.nclsp.com",
    secure=False,
)


def load_model(force_reload=False):
    global model
    if model is None or force_reload:
        model_path = "models/yolov8n.pt"
        model = YOLO(model_path)
        print("Model loaded successfully.")


def create_yaml(folder_path: str, filename: str):
    data = {
        "val": os.path.join(os.getcwd(), "Datasets", "val"),
        "train": os.path.join(os.getcwd(), "Datasets", "train"),
        "names": ["target"],
        "nc": 1,
    }

    os.makedirs(folder_path, exist_ok=True)

    path = os.path.join(folder_path, filename)

    with open(path, "w") as f:
        yaml.dump(data, f, default_flow_style=False, allow_unicode=True)


def create_labels(labels: List[str], folder_path: str, filename: str):
    os.makedirs(folder_path, exist_ok=True)

    path = os.path.join(folder_path, filename)
    with open(path, "w") as f:
        for label in labels:
            label_dict = eval(label)
            f.write(
                f"0 {label_dict['x']} {label_dict['y']} {label_dict['width']} {label_dict['height']}\n"
            )
    print(f"Saved labels to {path}")


def recompose_image(file_data: bytes, folder_path: str, filename: str):
    print(f"File data received for {filename}, size: {len(file_data)} bytes")
    try:
        png_image = Image.open(BytesIO(file_data))
        os.makedirs(folder_path, exist_ok=True)
        path = os.path.join(folder_path, filename)
        png_image.convert("RGB").save(path, format="JPEG")
        print(f"Saved image to {path}")
    except UnidentifiedImageError as e:
        print(f"Failed to open image {filename}: {e}")
        raise HTTPException(
            status_code=400, detail=f"Failed to open image {filename}: {e}"
        )


def ensure_directory_structure(base_folder: str):
    os.makedirs(os.path.join(base_folder, "train", "images"), exist_ok=True)
    os.makedirs(os.path.join(base_folder, "train", "labels"), exist_ok=True)
    os.makedirs(os.path.join(base_folder, "val", "images"), exist_ok=True)
    os.makedirs(os.path.join(base_folder, "val", "labels"), exist_ok=True)


def clear_directory_contents(directory: str):
    for root, dirs, files in os.walk(directory):
        for file in files:
            os.unlink(os.path.join(root, file))
        for dir in dirs:
            os.rmdir(os.path.join(root, dir))
    print(f"Cleared contents of {directory}")


def train_custom_model(
    dataset_path: str,
    yaml_file: str = "data_custom.yaml",
    yolo_model: str = "models/yolov8n.pt",
):
    global model

    create_yaml(dataset_path, yaml_file)
    path = os.path.join(dataset_path, yaml_file)
    if os.path.exists(path):
        model = YOLO(yolo_model)
        model.train(data=path, epochs=1, batch=1, imgsz=608, save=True)

        # Get the path of the trained model
        trained_model_path = model.export()
        print(f"Exported model path: {trained_model_path}")

        if trained_model_path and os.path.exists(trained_model_path):
            # Upload the model to MinIO
            try:
                bucket_name = "tellopa"
                # Generate a unique file name using timestamp
                timestamp = int(time.time())
                object_name = f"models/model_{timestamp}.pt"

                print(
                    f"Attempting to upload {trained_model_path} to MinIO bucket '{bucket_name}' as '{object_name}'"
                )

                minio_client.fput_object(
                    bucket_name,
                    object_name,
                    trained_model_path,
                )
                print(
                    f"Successfully uploaded {trained_model_path} to MinIO bucket '{bucket_name}'"
                )
            except S3Error as e:
                print(f"Error uploading to MinIO: {e}")
                print("Continuing with training process despite upload failure.")
            except Exception as e:
                print(f"Unexpected error during MinIO upload: {e}")
                print("Continuing with training process despite upload failure.")
        else:
            print(
                f"Trained model path not found or does not exist: {trained_model_path}"
            )

        # Force reload the model after training to ensure updated weights
        load_model(force_reload=True)
    else:
        print(f"YAML file not found at {path}")


@app.post("/api/train")
async def rec_img(
    request: Request,
    images: List[UploadFile] = File(...),
    labels: List[str] = Form(...),
):
    base_folder = "./Datasets"

    try:
        if not images or not labels:
            raise HTTPException(
                status_code=400, detail="Images and labels are required."
            )

        if len(images) != len(labels):
            raise HTTPException(
                status_code=400, detail="Number of images and labels must match."
            )

        ensure_directory_structure(base_folder)

        clear_directory_contents(os.path.join(base_folder, "train/images"))
        clear_directory_contents(os.path.join(base_folder, "train/labels"))
        clear_directory_contents(os.path.join(base_folder, "val/images"))
        clear_directory_contents(os.path.join(base_folder, "val/labels"))

        total_images = len(images)

        if total_images == 0:
            raise HTTPException(
                status_code=400, detail="At least one image is required for training."
            )

        if total_images == 1:
            train_images = images
            val_images = images
            train_labels = labels
            val_labels = labels
        else:
            train_size = max(1, int(total_images * 0.45))
            train_images = images[:train_size]
            val_images = images[train_size:]
            train_labels = labels[:train_size]
            val_labels = labels[train_size:]

        print(f"Number of training images: {len(train_images)}")
        print(f"Number of validation images: {len(val_images)}")

        # Process training images and labels
        for index, (image_file, label) in enumerate(zip(train_images, train_labels)):
            img_data = await image_file.read()
            if not img_data:
                raise HTTPException(
                    status_code=400, detail=f"File {image_file.filename} is empty."
                )
            print(
                f"Processing {image_file.filename}, size: {len(img_data)} bytes for TRAINING"
            )

            recompose_image(
                img_data,
                os.path.join(base_folder, "train/images"),
                f"image_{index}.jpg",
            )
            create_labels(
                [label], os.path.join(base_folder, "train/labels"), f"image_{index}.txt"
            )

        if total_images == 1:
            val_images[0].file.seek(0)

        for index, (image_file, label) in enumerate(zip(val_images, val_labels)):
            img_data = await image_file.read()
            if not img_data:
                raise HTTPException(
                    status_code=400, detail=f"File {image_file.filename} is empty."
                )
            print(
                f"Processing {image_file.filename}, size: {len(img_data)} bytes for VALIDATION"
            )

            recompose_image(
                img_data, os.path.join(base_folder, "val/images"), f"image_{index}.jpg"
            )
            create_labels(
                [label], os.path.join(base_folder, "val/labels"), f"image_{index}.txt"
            )

        # Validate directories content after writing
        train_images_list = os.listdir(os.path.join(base_folder, "train/images"))
        val_images_list = os.listdir(os.path.join(base_folder, "val/images"))
        train_labels_list = os.listdir(os.path.join(base_folder, "train/labels"))
        val_labels_list = os.listdir(os.path.join(base_folder, "val/labels"))

        print(f"Training images directory listing: {train_images_list}")
        print(f"Validation images directory listing: {val_images_list}")
        print(f"Training labels directory listing: {train_labels_list}")
        print(f"Validation labels directory listing: {val_labels_list}")

        if (
            not train_images_list
            or not val_images_list
            or not train_labels_list
            or not val_labels_list
        ):
            raise HTTPException(
                status_code=400,
                detail="Training and validation datasets should not be empty.",
            )

        train_custom_model(base_folder, "data_custom.yaml", "models/yolov8n.pt")

        return {"message": "Training Ended."}
    except HTTPException as e:
        print(f"HTTP Exception: {e.detail}")
        raise e
    except Exception as e:
        print(f"Unexpected error: {str(e)}")
        for file in os.listdir(os.path.join(base_folder, "train/images")):
            print(f"File in train/images: {file}")
        for file in os.listdir(os.path.join(base_folder, "val/images")):
            print(f"File in val/images: {file}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/predict")
async def predict(file: UploadFile = File(...)):
    load_model()

    img_data = await file.read()
    image = Image.open(BytesIO(img_data))
    image = image.convert("RGB")

    # Convert image to numpy array
    image_array = np.array(image)

    # Print image size and type for debugging
    print(f"Image size: {image.size}, Image array shape: {image_array.shape}")

    # Run YOLO model prediction with a lower confidence threshold
    assert model
    results = model.predict(source=image_array, save=False, conf=0.90)

    predictions = []
    for result in results:
        if result.boxes is not None and len(result.boxes) > 0:
            print(f"Number of detected boxes: {len(result.boxes)}")  # Debug statement
            for box in result.boxes:
                print(f"Box Detected: {box}")  # Debug statement
                xyxy = box.xyxy[0].numpy()  # Extract bounding box coordinates
                conf = box.conf[0].numpy()  # Extract confidence score
                cls_idx = box.cls[0].numpy()  # Extract class id
                predictions.append(
                    {
                        "box": xyxy.tolist(),
                        "score": float(conf),
                        "class_id": int(cls_idx),
                    }
                )
                # Draw bounding box on the image
                draw = ImageDraw.Draw(image)
                draw.rectangle(xyxy, outline="red", width=3)
                draw.text((xyxy[0], xyxy[1]), f"Conf: {conf:.2f}", fill="red")

    # Save the resultant image with bounding boxes
    output_path = "result_image.jpg"
    image.save(output_path)

    print(f"Predictions: {predictions}")  # Debug statement
    return predictions


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8001)
