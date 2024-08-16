$(document).ready(() => {
    initDragDropImage();
    initButton();
});

function initDragDropImage() {
    function loadImage(file) {
        const img_reader = new FileReader();
        img_reader.readAsDataURL(file);
        img_reader.onloadend = () => {
            showImage(img_reader.result);
            $('#draw-btn').prop('disabled', false);
            $('#search-btn').prop('disabled', false);
        };
    }
    function showImage(imgData) {
        const $uploaded_img = $('<img>', {
            src: imgData,
            id: 'uploaded-img',
        });
        $('#upload-container').empty();
        $('#upload-container').append($uploaded_img);
    }

    function dropImageFile(event) {
        const uploadedFiles = event.originalEvent.dataTransfer.files;
        if (uploadedFiles.length === 1 && uploadedFiles[0].type.startsWith('image/')) {
            loadImage(uploadedFiles[0]);
            $('#imageInput')[0].files = uploadedFiles;
        }
    }
    ['dragenter', 'dragover', 'dragleave', 'drop'].forEach(event => {
        $('#upload-container').on(event, event => {
            event.preventDefault();
            event.stopPropagation();
        })
    });
    $('#upload-container').on('drop', dropImageFile);
}

function initButton() {
    function handleDrawBtnClick() {
        $('#draw-btn').prop('disabled', true);
        initCanvas();
    }
    function handleClearBtnClick() {
        $('#clear-btn').prop('disabled', true);
        initCanvas();
    }
    function handleSearchBtnClick() {
        SearchBtnLoading(true);
        const imageForm = new FormData($('#img-form')[0]);
        $.ajax({
            url: '/recommend-imgs/',
            type: 'POST',
            data: imageForm,
            processData: false,
            contentType: false,
            headers: {
                'X-CSRFToken': $('meta[name="csrf-token"]').attr('content')
            },
            success: function (img_info) {
                displayRecommendedImage(img_info.image_url);
                SearchBtnLoading(false);
            },
            error: function (_, error) {
                alert(error);
            }
        });
    }
    function SearchBtnLoading(isLoading) {
        const $searchBtn = $('#search-btn');
        $searchBtn.empty().prop('disabled', isLoading);
        if (isLoading) {
            $searchBtn.append($('<div>', {
                class: 'spinner-border',
                role: 'status'
            }));
        }
        else {
            $searchBtn.append($('<h4>', {
                text: 'Search'
            }));
        }
    }
    $('#draw-btn').click(handleDrawBtnClick);
    $('#clear-btn').click(handleClearBtnClick);
    $('#search-btn').click(handleSearchBtnClick);
}



function displayRecommendedImage(imageUrls) {
    function displayTop1Recommendation(imgUrl) {
        $top1ImageContainer.empty().append($('<img>', {
            src: imgUrl
        }));
    }
    function imageClickEvent($img) {
        displayTop1Recommendation($img.attr('src'));
        $recommenderContainer.children().each((_, imgContiner) => {
            $(imgContiner).removeClass('active')
        });
        $img.parent().addClass('active');
    }
    function createImageContainer(imgUrl) {
        const $imgContainer = $('<div>', {
            class: 'img-container'
        });
        const $img = $('<img>', {
            src: imgUrl,
            class: 'img-thumbnail recommendation'
        }).on('click', () => {
            imageClickEvent($img)
        });
        $imgContainer.append($img);
        return $imgContainer;
    }
    function displayRecommendations(imageUrls) {
        $recommenderContainer.empty();
        imageUrls.forEach((imgUrl, index) => {
            const $imgContainer = createImageContainer(imgUrl = imgUrl, isActive = index === 0)
            if (index === 0) $imgContainer.addClass('active')
            $recommenderContainer.append($imgContainer)
        });
    }
    const $top1ImageContainer = $('#target-img-container');
    const $recommenderContainer = $('#recommender-container');
    displayTop1Recommendation(imageUrls[0]);
    displayRecommendations(imageUrls);
}

function initCanvas() {
    function createCanvas() {
        if ($('#img-canvas').length === 0) {
            const $img_canvas = $('<canvas>', {
                id: 'img-canvas',
            });
            $img_canvas[0].width = imgWidth;
            $img_canvas[0].height = imgHeight;
            $img_canvas[0].style.left = `${imgStartX}px`;
            $img_canvas[0].style.top = `${imgStartY}px`;
            $img_canvas[0].style.width = `${imgWidth}px`;
            $img_canvas[0].style.height = `${imgHeight}px`;
            $uploadContainer.append($img_canvas);
        }
        const $imgCanvas = $('#img-canvas');
        const ctx = $imgCanvas[0].getContext('2d');
        ctx.strokeStyle = "#1A4870";
        ctx.lineWidth = 3;
        ctx.clearRect(0, 0, $('#img-canvas').width(), $('#img-canvas').height());
        $coords.val('');
        return $imgCanvas
    }
    function startDrawing(event) {
        if (isDrawing || already_drawn) return;
        isDrawing = true;
        x1 = event.offsetX * (imgWidth - 1) / imgWidth;
        y1 = event.offsetY * (imgHeight - 1) / imgHeight;
    }
    function onDrawing(event) {
        if (!isDrawing) return;
        x2 = event.offsetX * (imgWidth - 1) / imgWidth;
        y2 = event.offsetY * (imgHeight - 1) / imgHeight;
        ctx.clearRect(0, 0, $imgCanvas.width(), $imgCanvas.height())
        ctx.strokeRect(x1, y1, x2 - x1, y2 - y1);
    }
    function stopDrawing(event) {
        if (!isDrawing) return;
        x2 = event.offsetX * (imgWidth - 1) / imgWidth;
        y2 = event.offsetY * (imgHeight - 1) / imgHeight;
        if (x1 == x2 || y1 == y2) return;

        isDrawing = false;
        already_drawn = true;
        $coords.val(JSON.stringify({ x1: x1, y1: y1, x2: x2, y2: y2, width: imgWidth, height: imgHeight }));
        $('#draw-btn').prop("disabled", true);
        $('#clear-btn').prop("disabled", false);
    }
    const $uploadContainer = $('#upload-container');
    const $mainImage = $('#uploaded-img');
    const imgWidth = $mainImage.width();
    const imgHeight = $mainImage.height();
    const containerWidth = $uploadContainer.width();
    const containerHeight = $uploadContainer.height();
    const imgStartX = 0.5 * containerWidth - 0.5 * imgWidth;
    const imgStartY = 0.5 * containerHeight - 0.5 * imgHeight;
    const $coords = $('#coordsInput');

    let isDrawing = false;
    let already_drawn = false;

    const $imgCanvas = createCanvas();
    const ctx = $imgCanvas[0].getContext('2d');

    $imgCanvas.on('mousedown', (event) => {
        startDrawing(event);
    });
    $imgCanvas.on('mousemove', (event) => {
        onDrawing(event);
    });
    $imgCanvas.on('mouseup', (event) => {
        stopDrawing(event);
    });
}
