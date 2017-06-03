var drawWriteApp = (function () {

    // Seems like a good idea I guess.
    "use strict";

    // Variables!
    var canvas, ctx, pointRadius, paint, wasPath, prevX, prevY, init;

    // Draw a dot where the user clicked. This does not get executed if the
    // user draws a line.
    function dot(e) {
        if(wasPath === true) {
            wasPath = false;
        } else {
            ctx.beginPath();
            ctx.arc(e.pageX-this.offsetLeft, e.pageY-this.offsetTop, pointRadius, 0, 2*Math.PI);
            ctx.fill();
        }
    }

    // Start painting, and initalize the two 'previous' positions.
    function startPath(e) {
        paint = true;
        prevX = (e.type === 'touchstart' ? e.changedTouches[0].pageX : e.pageX) - this.offsetLeft;
        prevY = (e.type === 'touchstart' ? e.changedTouches[0].pageY : e.pageY) - this.offsetTop;
    }

    // If we're painting, draw a line  between the previous point and the current point,
    // then update the current point.
    function continuePath(e) {
        if(paint) {
            var mX = (e.type === 'touchmove' ? e.changedTouches[0].pageX : e.pageX) - this.offsetLeft;
            var mY = (e.type === 'touchmove' ? e.changedTouches[0].pageY : e.pageY) - this.offsetTop;

            if(mX !== prevX || mY !== prevY) {
                wasPath = true;

                ctx.beginPath();
                ctx.moveTo(prevX, prevY);
                ctx.lineTo(mX, mY);
                ctx.closePath();
                ctx.stroke();

                prevX = mX;
                prevY = mY;
            }
        }
        // Prevent the user from swiping left/right for navigation.
        e.preventDefault();
    }

    // If we end on the canvas, don't unset wasPath, but do unset everything else.
    function endPathOnCanvas(e) {
        paint = false;
        prevX = null;
        prevY = null;
    }

    // If we end off the canvas, then unset everything.
    function endPathOffCanvas(e) {
        paint = false;
        wasPath = false;
        prevX = null;
        prevY = null;
    }

    // Add all the event listeners.
    function addListeners() {
        // Mouse events.
        canvas.addEventListener('click', dot);
        canvas.addEventListener('mousedown', startPath);
        canvas.addEventListener('mousemove', continuePath);
        canvas.addEventListener('mouseup', endPathOnCanvas);
        canvas.addEventListener('mouseleave', endPathOffCanvas);
        // Touch events.
        // Touch 'taps' trigger the on-click event, so there's no tap event here.
        canvas.addEventListener('touchstart', startPath);
        canvas.addEventListener('touchmove', continuePath);
        canvas.addEventListener('touchend', endPathOnCanvas);
        canvas.addEventListener('touchcancel', endPathOffCanvas);
    }

    // Initialize the canvas, add the listeners.
    function init() {
        canvas = document.getElementById('drawWriteCanvas');
        if(null === canvas) {
            return;
        }
        ctx = canvas.getContext('2d');
        ctx.lineJoin = 'round';
        ctx.lineWidth = 3;
        pointRadius = ctx.lineWidth / 2 + ctx.lineWidth % 2;
        addListeners();
    }

    // Return an object with the init function mapped to init.
    return {
        init: init,
    };
}());

// On document ready, call drawWriteApp.init().
$(document).ready(drawWriteApp.init);
