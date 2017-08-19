var indexJs = (function() {

    // Get a list of available games and append them all the the select element.
    function getAvailable() {
        $.get(refreshAvailableAjaxUrl, function(data) {
            $('#join select').empty();
            if(data.options == null || data.options.length == 0) {
                $('#join select').append('<option value="">- None -</option>');
            }
            else {
                $('#join select').append('<option value="">- Select -</option>');
                for(var i = 0; i < data.options.length; i++) {
                    $('#join select').append('<option value="' + data.options[i] + '">' + data.options[i] + '</option>');
                }
            }
        });
    }

    // Attach the getAvailable function to the Refresh List link. Prevent
    // the link from actually triggering.
    function addEventListeners() {
        $('.refresh-available').on('click', function(e) {
            e.preventDefault();
            getAvailable();
        });
    }

    // Return the addEventListeners function.
    return {
        init: addEventListeners,
    }

})();

$(document).ready(indexJs.init);
