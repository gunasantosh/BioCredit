const cameraPreview = document.getElementById('cameraPreview');
const captureBtn = document.getElementById('captureBtn');
const imageCanvas = document.getElementById('imageCanvas');

async function startCamera() {
    const stream = await navigator.mediaDevices.getUserMedia({ video: true });
    cameraPreview.srcObject = stream;
}

const retakeBtn = document.getElementById('retakeBtn');
// const saveBtn = document.getElementById('saveBtn');
let capturedImageDataURL = null;

// const viewImageBtn = document.getElementById('viewImageBtn');


captureBtn.addEventListener('click', () => {
    const context = imageCanvas.getContext('2d');
    imageCanvas.width = cameraPreview.videoWidth;
    imageCanvas.height = cameraPreview.videoHeight;
    context.drawImage(cameraPreview, 0, 0, imageCanvas.width, imageCanvas.height);
    cameraPreview.style.display = 'none';
    imageCanvas.style.display = 'block';
    captureBtn.style.display = 'none';
    retakeBtn.style.display = 'block';  // Show the "Retake" button
    // saveBtn.style.display = 'block';    // Show the "Save" button
    capturedImageDataURL = imageCanvas.toDataURL('image/jpeg'); 
    var captured_image=document.getElementById("captured_image");
    captured_image.value=capturedImageDataURL;
});

retakeBtn.addEventListener('click', () => {
    cameraPreview.style.display = 'block';
    imageCanvas.style.display = 'none';
    captureBtn.style.display = 'block';
    retakeBtn.style.display = 'none';  // Hide the "Retake" button
});


// saveBtn.addEventListener('click', () => {
//     if (capturedImageDataURL) {
//         // Send the capturedImageDataURL to the server to save in the database
//         fetch('/save', {
//             method: 'POST',
//             headers: {
//                 'Content-Type': 'application/json'
//             },
//             body: JSON.stringify({ image_data: capturedImageDataURL })
//         })
//         .then(response => response.json())
//         .then(data => {
//             if (data.status === 'success') {
//                 console.log('Image saved:', data.image_id);
//             } else {
//                 console.error('Error saving image');
//             }
//         });
//         retakeBtn.style.display = 'none';  // Hide the "Retake" button
//         saveBtn.style.display = 'none';    // Hide the "Save" button
//         viewImageBtn.style.display = 'block';  // Show the "View Image" button
//         imageCanvas.style.display = 'none'; // Hide the canvas
//     }
// });
startCamera().catch(console.error);
