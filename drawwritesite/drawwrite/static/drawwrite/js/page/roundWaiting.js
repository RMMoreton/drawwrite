var drawwriteRoundWaiting = (function () {

    // Send an AJAX request to see if every user has finished the
    // round. If so, reload the page to move to the next round.
    function checkRoundComplete() {
        $.get(drawwriteAjaxUrl, function(data) {
            if(data.finished == true) {
                location.reload();
            }
        });
    }

    // Attach event listeners.
    function attachEventListeners() {
        $('#checkRoundCompletion').on('click', checkRoundComplete);
        window.setInterval(checkRoundComplete, 5000);
    }

    return {
        attachEventListeners: attachEventListeners,
    };
}());

// Attach the event listeners.
$(document).ready(drawwriteRoundWaiting.attachEventListeners);
