var drawwriteGameWaiting = (function () {

    // Send an AJAX request to see if the game is done. If so,
    // reload the page (and get redirected to the end page). If not,
    // show a list of all players who haven't finished yet.
    function checkGameComplete() {
        $.get(drawwriteAjaxUrl, function(data) {
            if(data.finished === true) {
                location.reload();
            } else {
                $('.stillPlayingWrapper').empty();
                for(var i = 0; i < data.still_playing.length; i++) {
                    var nameHolder = document.createElement('div');
                    nameHolder.innerText = data.still_playing[i];
                    $(nameHolder).addClass('indent');
                    $('.stillPlayingWrapper').append(nameHolder);
                }
            }
        });
    }

    // Attach event listeners.
    function attachEventListeners() {
        window.setInterval(checkGameComplete, 2500);
    }

    // Call on document ready.
    function init() {
        attachEventListeners();
        checkGameComplete();
    }

    // Return the init function.
    return {
        init: init,
    };
}());

// On document ready, attach event listeners.
$(document).ready(drawwriteGameWaiting.init);
