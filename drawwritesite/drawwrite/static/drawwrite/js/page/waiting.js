var drawwriteWaiting = (function () {

    // Seems like a good idea.
    "use strict";

    // Replace the list of names currently being shown.
    function replaceNames(names) {
        var listString = "";
        for(var i = 0; i < names.length; i++) {
            listString = listString + "<li>" + names[i] + "</li>\n";
        }
        $('#nameList').html(listString);
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
        $('#getNameList').on('click', checkGameStart);
    }

    // Return an object holding the 'attachListeners' function.
    return {
        attachListeners: attachListeners,
    };
}());

// On document ready, attach event listeners.
$(document).ready(drawwriteWaiting.attachListeners);
