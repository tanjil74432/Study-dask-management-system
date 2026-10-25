document.addEventListener('DOMContentLoaded', function () {
    const timers = document.querySelectorAll('.timer-live');

    timers.forEach(function (el) {
        const startTimeMs = parseInt(el.dataset.start, 10);

        function update() {
            const now = Date.now();
            const diffSeconds = Math.floor((now - startTimeMs) / 1000);

            const h = String(Math.floor(diffSeconds / 3600)).padStart(2, '0');
            const m = String(Math.floor((diffSeconds % 3600) / 60)).padStart(2, '0');
            const s = String(diffSeconds % 60).padStart(2, '0');

            el.textContent = `${h}:${m}:${s}`;
        }

        update();
        setInterval(update, 1000);
    });
});