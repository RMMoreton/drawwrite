function checkRoundDone() {
    $.get(checkUrl, function(data) {
        if(data.finished == true) {
            location.reload();
        }
    });
}
