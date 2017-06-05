var drawwriteGameWaiting = (function () {

    // Send an AJAX request to see if the game is done. If so,
    // reload the page (and get redirected to the end page).
    function checkGameComplete() {
        $.get(drawwriteAjaxUrl, function(data) {
            if(data.finished === true) {
                location.reload();
            }
        });
    }

    // Attach event listeners.
    function attachEventListeners() {
        $('#checkGameCompletion').on('click', checkGameComplete);
        window.setInterval(checkGameComplete, 5000);
    }

    // Return the attachEventListeners function.
    return {
        attachEventListeners: attachEventListeners,
    };
}());

// On document ready, attach event listeners.
$(document).ready(drawwriteGameWaiting.attachEventListeners);
