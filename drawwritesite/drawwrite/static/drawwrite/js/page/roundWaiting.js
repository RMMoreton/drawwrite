var drawwriteRoundWaiting = (function () {

    // Send an AJAX request to see if every user has finished the
    // round. If so, reload the page to move to the next round. If not,
    // add all the players who haven't finished the round to the list.
    function checkRoundComplete() {
        $.get(drawwriteAjaxUrl, function(data) {
            if(data.finished === true) {
                location.reload();
            } else {
                $('.stillPlayingWrapper').empty();
                for(var i = 0; i < data.stillPlaying.length; i++) {
                    var nameHolder = document.createElement('div');
                    nameHolder.innerText = data.stillPlaying[i];
                    $(nameHolder).addClass('indent');
                    $('.stillPlayingWrapper').append(nameHolder);
                }
            }
        });
    }

    // Attach event listeners.
    function attachEventListeners() {
        window.setInterval(checkRoundComplete, 2500);
    }

    // Called on document ready.
    function init() {
        attachEventListeners();
        checkRoundComplete();
    }

    // Return the init function.
    return {
        init: init,
    };
}());

// Attach the event listeners.
$(document).ready(drawwriteRoundWaiting.init);
