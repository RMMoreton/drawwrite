var drawwriteWaiting = (function () {

    // Seems like a good idea.
    "use strict";

    // Replace the list of names currently being shown.
    function replaceNames(names) {
        var listString = "";
        $('#nameList').empty();
        for(var i = 0; i < names.length; i++) {
            var nameHolder = document.createElement('div');
            nameHolder.innerText = names[i];
            $(nameHolder).addClass('indented');
            $('#nameList').append(nameHolder);
        }
        return true;
    }

    // Perform an AJAX request to see if the game has started or new players
    // have joined.
    function checkGameStart() {
        $.get(drawwriteAjaxUrl, function(data) {
            if(data.started === true) {
                location.reload();
            }
            else {
                replaceNames(data.names);
            }
        });
    }

    // Attach an event listener to the 'refresh' button.
    function attachListeners() {
        window.setInterval(checkGameStart, 5000);
    }

    // Return an object holding the 'attachListeners' function.
    return {
        attachListeners: attachListeners,
    };
}());

// On document ready, attach event listeners.
$(document).ready(drawwriteWaiting.attachListeners);
