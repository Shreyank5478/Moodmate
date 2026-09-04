const fileInput = document.getElementById('image');
const previewImage = document.getElementById('preview-img');
const video = document.getElementById('video');
const canvas = document.getElementById('canvas');
const imageData = document.getElementById('image-data');
const statusMessage = document.getElementById('statusMessage');
let cameraStream;

function setStatus(message) {
  if (statusMessage) {
    statusMessage.textContent = message;
  }
}

fileInput?.addEventListener('change', () => {
  const [file] = fileInput.files;
  if (!file) {
    return;
  }

  imageData.value = '';
  previewImage.src = URL.createObjectURL(file);
  previewImage.style.display = 'block';
  setStatus('Photo ready to analyze.');
});

async function startCamera() {
  if (!navigator.mediaDevices?.getUserMedia) {
    setStatus('Camera access is not supported by this browser.');
    return;
  }

  try {
    cameraStream = await navigator.mediaDevices.getUserMedia({ video: true });
    video.srcObject = cameraStream;
    video.style.display = 'block';
    setStatus('Camera ready.');
  } catch (error) {
    setStatus('Camera access was not granted.');
  }
}

function capturePhoto() {
  if (!cameraStream || !video.videoWidth) {
    setStatus('Start the camera before capturing a photo.');
    return;
  }

  canvas.width = video.videoWidth;
  canvas.height = video.videoHeight;
  canvas.getContext('2d').drawImage(video, 0, 0);
  imageData.value = canvas.toDataURL('image/jpeg');
  previewImage.src = imageData.value;
  previewImage.style.display = 'block';
  setStatus('Photo captured and ready to analyze.');
}

window.addEventListener('beforeunload', () => {
  cameraStream?.getTracks().forEach((track) => track.stop());
});
