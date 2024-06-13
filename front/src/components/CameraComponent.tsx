import React, { useRef, useState, useCallback, useEffect } from 'react';
import Webcam from 'react-webcam';
import axios from 'axios';
import './CameraComponent.css';

const videoConstraints = {
  width: 640,
  height: 480,
  facingMode: "user"
};

const boundingBoxStyle = {
  width: '50%',
  height: '40%',
};

const CameraComponent: React.FC = () => {
  const webcamRef = useRef<Webcam>(null);
  const [capturing, setCapturing] = useState<boolean>(false);
  const [screenshots, setScreenshots] = useState<string[]>([]);
  const [mode, setMode] = useState<"train" | "predict">("predict");
  const [hasPermission, setHasPermission] = useState<boolean | null>(null);
  const [statusMessage, setStatusMessage] = useState<string>("");

  useEffect(() => {
    navigator.mediaDevices.getUserMedia({ video: true })
      .then(() => setHasPermission(true))
      .catch(err => {
        console.error("Camera permission denied:", err);
        setHasPermission(false);
      });
  }, []);

  const capture = useCallback(() => {
    if (webcamRef.current) {
      const screenshot = webcamRef.current.getScreenshot();
      if (screenshot) setScreenshots(prevScreenshots => [...prevScreenshots, screenshot]);
    }
  }, [webcamRef, setScreenshots]);

  const startCapturing = () => {
    setScreenshots([]);
    setCapturing(true);
    setStatusMessage("Training started...");

    let count = 0;
    const captureInterval = setInterval(() => {
      if (count >= 50) {
        setCapturing(false);
        clearInterval(captureInterval);
        sendScreenshots();
      } else {
        capture();
        count++;
      }
    }, 100);
  };

  const sendScreenshots = async () => {
    const imageElements = document.querySelectorAll('video');
    const imagesPromises = Array.from(imageElements).map(async (video, index) => {
      const canvas = document.createElement('canvas');
      canvas.width = video.videoWidth;
      canvas.height = video.videoHeight;
      const ctx = canvas.getContext('2d');
      if (ctx) {
        ctx.drawImage(video, 0, 0, canvas.width, canvas.height);
        const dataUrl = canvas.toDataURL('image/jpeg');
        const byteString = atob(dataUrl.split(',')[1]);
        const arrayBuffer = new ArrayBuffer(byteString.length);
        const intArray = new Uint8Array(arrayBuffer);
        for (let i = 0; i < byteString.length; i++) {
          intArray[i] = byteString.charCodeAt(i);
        }
        return new Blob([intArray], { type: 'image/jpeg' });
      }
    });

    const images = await Promise.all(imagesPromises);

    const formData = new FormData();
    const boundingBox = {
      x: (videoConstraints.width * (50 / 100)) / 2,
      y: (videoConstraints.height * (60 / 100)) / 2,
      width: videoConstraints.width * (50 / 100),
      height: videoConstraints.height * (40 / 100)
    };

    images.forEach((image, index) => {
      formData.append("images", image!, `image_${index}.jpg`);
      formData.append("labels", JSON.stringify({
        class: "head",
        x: boundingBox.x / videoConstraints.width,
        y: boundingBox.y / videoConstraints.height,
        width: boundingBox.width / videoConstraints.width,
        height: boundingBox.height / videoConstraints.height
      }));
    });

    try {
      const endpoint = "http://localhost:8001/api/train";
      const response = await axios.post(endpoint, formData, {
        headers: { "Content-Type": "multipart/form-data" }
      });
      console.log(response.data);
      setStatusMessage("Training completed!");
    } catch (error) {
      console.error("Error sending images:", error);
      setStatusMessage("Training failed! Please try again.");
    }
  };

  const captureAndSendPrediction = useCallback(async () => {
    if (!webcamRef.current) return;

    const screenshot = webcamRef.current.getScreenshot();
    if (!screenshot) return;

    try {
      setStatusMessage("Sending image for prediction...");
      const byteString = atob(screenshot.split(',')[1]);
      const arrayBuffer = new ArrayBuffer(byteString.length);
      const intArray = new Uint8Array(arrayBuffer);
      for (let i = 0; i < byteString.length; i++) {
        intArray[i] = byteString.charCodeAt(i);
      }
      const blob = new Blob([intArray], { type: 'image/jpeg' });

      const formData = new FormData();
      formData.append("file", blob, 'image.jpg');

      const endpoint = "http://localhost:8001/api/predict";
      const response = await axios.post(endpoint, formData, {
        headers: { "Content-Type": "multipart/form-data" }
      });

      console.log("Prediction result:", response.data);
      setStatusMessage("Prediction completed!");
    } catch (error) {
      console.error("Error sending image:", error);
      setStatusMessage("Prediction failed! Please try again.");
    }
  }, [webcamRef]);

  if (hasPermission === null) {
    return <div>Loading...</div>;
  }

  if (hasPermission === false) {
    return <div className="camera-container">Please allow camera access in your browser settings and reload the page.</div>;
  }

  return (
    <div className="camera-container">
      <div className="camera-wrapper">
        <Webcam
          audio={false}
          height={videoConstraints.height}
          ref={webcamRef}
          screenshotFormat="image/jpeg"
          width={videoConstraints.width}
          videoConstraints={videoConstraints}
        />
        <div className="bounding-box" style={boundingBoxStyle}></div>
      </div>
      <div className="button-wrapper">
        <button onClick={captureAndSendPrediction} disabled={capturing}>
          {mode === 'predict' ? 'Start Predict' : 'Stop Capture'}
        </button>
        <button onClick={startCapturing} disabled={capturing}>
          {capturing ? 'Capturing...' : 'Start Training'}
        </button>
        <button onClick={() => setMode(mode === 'train' ? 'predict' : 'train')}>
          Switch to {mode === 'train' ? 'Predict' : 'Train'} Mode
        </button>
      </div>
      {statusMessage && <div className="status-message">{statusMessage}</div>}
    </div>
  );
};

export default CameraComponent;