document.addEventListener('DOMContentLoaded', () => {
    initDragDropImage();
    setRecommendationClick();
});

function initDragDropImage() {
    const uploadContainer = document.getElementById('upload-container');

    function loadImage(file) {
        const img_reader = new FileReader();
        img_reader.readAsDataURL(file);
        img_reader.onloadend = () => {
            const imgData = img_reader.result;
            showImage(imgData);
        };
    }
    function showImage(imgData) {
        const img = document.createElement('img');
        img.src = imgData;
        uploadContainer.innerHTML = '';
        uploadContainer.appendChild(img);
    }

    function dropImageFile(event) {
        const uploadedFiles = event.dataTransfer.files;
        const imgFileInput = document.getElementById('imageInput');
        if (uploadedFiles.length === 1 && uploadedFiles[0].type.startsWith('image/')) {
            uploadContainer.innerHTML = '';
            loadImage(uploadedFiles[0]);
            imgFileInput.files = uploadedFiles;
        }
    }

    ['dragenter', 'dragover', 'dragleave', 'drop'].forEach(event => {
        uploadContainer.addEventListener(event, event => {
            event.preventDefault();
            event.stopPropagation();
        });

    });
    uploadContainer.addEventListener('drop', dropImageFile);
}

function setRecommendationClick() {
    function showClickImage(src) {
        const targetImgContainer = document.getElementById('target-img-container');
        const targetImg = document.createElement('img');
        targetImg.src = src;
        targetImgContainer.innerHTML = '';
        targetImgContainer.appendChild(targetImg);
    }
    const recommendations = document.querySelectorAll('.recommendation')
    if (recommendations.length != 0) {
        const container = recommendations[0].parentElement;
        container.classList.add('active');
    }
    recommendations.forEach(recommendation => {
        recommendation.addEventListener('click', () => {
            showClickImage(recommendation.src);
            recommendations.forEach(r => {
                const container = r.parentElement;
                container.classList.remove('active');
            })
            const container = recommendation.parentElement;
            container.classList.add('active');
        });
    });
}