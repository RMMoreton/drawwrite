function replaceNames(names) {
    var listString = "";
    for(i = 0; i < names.length; i++) {
        listString = listString + "<li>" + names[i] + "</li>\n";
    }
    $('#name-list').html(listString);
    return true;
}

function checkGameStart() {
    $.get(ajaxNameUrl, function(data) {
        if(data.started === true) {
            location.reload();
        }
        else {
            replaceNames(data.names);
        }
    });
}
