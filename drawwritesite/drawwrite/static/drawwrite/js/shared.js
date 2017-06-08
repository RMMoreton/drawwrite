function setMainColBackground() {
    var possibleColors = [
        'rgba(255, 0, 0, 0.1)',
        'rgba(255, 127, 0, 0.1)',
        'rgba(255, 255, 0, 0.1)',
        'rgba(127, 255, 0, 0.1)',
        'rgba(0, 255, 0, 0.1)',
        'rgba(0, 255, 127, 0.1)',
        'rgba(0, 255, 255, 0.1)',
        'rgba(0, 127, 255, 0.1)',
        'rgba(0, 0, 255, 0.1)',
        'rgba(127, 0, 255, 0.1)',
        'rgba(255, 0, 255, 0.1)',
        'rgba(255, 0, 127, 0.1)',
    ];
    var randomColor = possibleColors[Math.floor(Math.random() * possibleColors.length)];
    $('.mainCol').css('background-color', randomColor);
}

//$(document).ready(setMainColBackground);
