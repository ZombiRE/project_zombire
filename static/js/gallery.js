const galleries = {
    'gallery-track': { position: 0, speed: 0.6, isMouseOver: false },
    'gallery-reverse-track': { position: 0, speed: -0.6, isMouseOver: false },
    'gallery-third-track': { position: 0, speed: 0.6, isMouseOver: false }
};

let autoScrollIntervals = [];

function shuffleArray(array) {
    for (let i = array.length - 1; i > 0; i--) {
        const j = Math.floor(Math.random() * (i + 1));
        [array[i], array[j]] = [array[j], array[i]];
    }
    return array;
}

async function loadPhotos() {
    try {
        const response = await fetch('/api/photos');
        const photos = await response.json();

        if (photos.length === 0) {
            console.log('Нет фотографий для отображения');
            return;
        }

        Object.keys(galleries).forEach(trackId => {
            const track = document.getElementById(trackId);
            if (!track) return;

            // больше копий для плавной бесконечной прокрутки
            const shuffledPhotos = shuffleArray([...photos]);
            const repeatedPhotos = [
                ...shuffledPhotos,
                ...shuffledPhotos,
                ...shuffledPhotos,
                ...shuffledPhotos,
                ...shuffledPhotos,
                ...shuffledPhotos
            ];

            track.innerHTML = repeatedPhotos.map(photo => `
                <div class="gallery-item" data-photo-id="${photo.id}">
                    <img src="${photo.file_path}" 
                        alt="Photo ${photo.id}" 
                        data-description="Фото: ${photo.id}. ${photo.description || ''}">
                </div>
            `).join('');

            // обработчик клика через addEventListener
            track.querySelectorAll('.gallery-item img').forEach(img => {
                img.addEventListener('click', function() {
                    openModal(this.src, this.dataset.description);
                });
            });


            // устанавливаем начальную позицию в середину
            const itemWidth = track.querySelector('.gallery-item').offsetWidth;
            galleries[trackId].position = itemWidth * shuffledPhotos.length;
            track.style.transform = `translateX(${-galleries[trackId].position}px)`;
        });

        stopAllAutoScroll();
        startAllAutoScroll();

        document.querySelectorAll('.gallery-container').forEach(container => {
            const trackId = container.querySelector('[id]').id;

            container.addEventListener('mouseenter', () => {
                galleries[trackId].isMouseOver = true;
                stopAutoScroll(trackId);
            });

            container.addEventListener('mouseleave', () => {
                galleries[trackId].isMouseOver = false;
                startAutoScroll(trackId);
            });
        });

    } catch (error) {
        console.error('Ошибка загрузки фотографий:', error);
    }
}

function startAutoScroll(trackId) {
    const gallery = galleries[trackId];
    if (!gallery || gallery.isMouseOver) return;

    const track = document.getElementById(trackId);
    if (!track) return;

    const interval = setInterval(() => {
        if (gallery.isMouseOver) return;

        gallery.position += gallery.speed;
        track.style.transform = `translateX(${-gallery.position}px)`;

        const items = track.querySelectorAll('.gallery-item');
        const itemWidth = items[0].offsetWidth;
        const totalWidth = itemWidth * items.length;
        const resetPosition = itemWidth * (items.length / 3);

        if (gallery.position > totalWidth - resetPosition) {
            gallery.position = resetPosition;
        } else if (gallery.position < 0) {
            gallery.position = totalWidth - resetPosition - itemWidth;
        }
    }, 20);

    autoScrollIntervals.push({ trackId, interval });
}

function startAllAutoScroll() {
    Object.keys(galleries).forEach(trackId => {
        startAutoScroll(trackId);
    });
}

function stopAutoScroll(trackId) {
    const intervalIndex = autoScrollIntervals.findIndex(item => item.trackId === trackId);
    if (intervalIndex !== -1) {
        clearInterval(autoScrollIntervals[intervalIndex].interval);
        autoScrollIntervals.splice(intervalIndex, 1);
    }
}

function stopAllAutoScroll() {
    autoScrollIntervals.forEach(({ interval }) => clearInterval(interval));
    autoScrollIntervals = [];
}

function scrollGallery(trackId, direction) {
    const gallery = galleries[trackId];
    if (!gallery) return;

    const track = document.getElementById(trackId);
    if (!track) return;

    const scrollAmount = 300;
    gallery.position += direction === 'left' ? -scrollAmount : scrollAmount;


    const items = track.querySelectorAll('.gallery-item');
    const itemWidth = items[0].offsetWidth;
    const totalWidth = itemWidth * items.length;
    const resetPosition = itemWidth * (items.length / 3);

    if (gallery.position > totalWidth - resetPosition) {
        gallery.position = resetPosition;
    } else if (gallery.position < 0) {
        gallery.position = totalWidth - resetPosition - itemWidth;
    }

    track.style.transform = `translateX(${-gallery.position}px)`;
}

function openModal(src, description) {
    const modal = document.getElementById('imageModal');
    const modalImage = document.getElementById('modalImage');
    const modalDescription = document.getElementById('modalDescription');

    if (modal && modalImage) {
        modalImage.src = src;
        modalDescription.textContent = description || '';
        modal.style.display = "block";
        modal.style.justifyContent = "center";
        modal.style.alignItems = "center";

    }
}

function closeModal() {
    const modal = document.getElementById('imageModal');
    if (modal) {
        modal.style.display = "none";
    }
}

document.addEventListener('DOMContentLoaded', () => {
    loadPhotos();

    const modal = document.getElementById('imageModal');
    if (modal) {
        modal.onclick = function(event) {
            if (event.target === this) {
                closeModal();
            }
        };
    }
});
