var indexJs = (function() {

    // Seems like a good idea.
    "use strict";

    function updateInput(name) {
        $('#id_gamename').val(name);
    }

    function pushAvailableGameName() {
        updateInput($('#id_open_games').val());
    }

    function addEventListeners() {
        $('#id_open_games').change(pushAvailableGameName);
    }

    return {
        addEventListeners: addEventListeners,
    }

})();

$(document).ready(indexJs.addEventListeners);
