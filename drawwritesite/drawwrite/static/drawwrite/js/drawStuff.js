var drawWriteApp = (function () {

    // Seems like a good idea I guess.
    "use strict";

    // Variables!
    var canvas, ctx, pointRadius, paint, wasPath, prevX, prevY, init, tool, TOOL_ENUM, addedMenuListeners;

    addedMenuListeners = false;

    // Create the 'tool' object.
    var TOOL_ENUM = {
        DRAW: "draw",
        HAND: "hand",
    }

    // Switch the tool to the "draw" tool.
    function switchToDrawTool(e) {
        tool = TOOL_ENUM.DRAW;
    }

    // Switch the tool to the "hand" tool.
    function switchToHandTool(e) {
        tool = TOOL_ENUM.HAND;
    }

    // Draw a dot where the user clicked. This does not get executed if the
    // user draws a line.
    function dot(e) {
        if(tool !== TOOL_ENUM.DRAW) {
            return;
        }
        if(wasPath === true) {
            wasPath = false;
        } else {
            var offsets = $(this).offset()
            ctx.beginPath();
            ctx.arc(e.pageX-offsets.left, e.pageY-offsets.top, pointRadius, 0, 2*Math.PI);
            ctx.fill();
        }
    }

    // Start painting, and initalize the two 'previous' positions.
    function startPath(e) {
        if(tool !== TOOL_ENUM.DRAW) {
            return;
        }
        var offsets = $(this).offset()
        paint = true;
        prevX = (e.type === 'touchstart' ? e.changedTouches[0].pageX : e.pageX) - offsets.left;
        prevY = (e.type === 'touchstart' ? e.changedTouches[0].pageY : e.pageY) - offsets.top;
    }

    // If we're painting, draw a line  between the previous point and the current point,
    // then update the current point.
    function continuePath(e) {
        if(tool !== TOOL_ENUM.DRAW) {
            return;
        }
        if(paint) {
            var offsets = $(this).offset()
            var mX = (e.type === 'touchmove' ? e.changedTouches[0].pageX : e.pageX) - offsets.left;
            var mY = (e.type === 'touchmove' ? e.changedTouches[0].pageY : e.pageY) - offsets.top;

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
    function addCanvasListeners() {
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

    // Add menu listeners if we haven't already.
    function addMenuListeners() {
        if(addedMenuListeners) {
            return;
        }
        $('#selectDrawTool').on('click', switchToDrawTool);
        $('#selectHandTool').on('click', switchToHandTool);
        addedMenuListeners = true;
    }

    // Create the canvas element, and make it the only child of the #drawWriteCanvasHolder div.
    function makeCanvas() {
        var canvasHolder = $('#drawWriteCanvasHolder');
        //canvasHolder.first().empty();
        canvas = document.createElement('canvas');
        canvas.id = 'drawWriteCanvas';
        canvas.width = canvasHolder.width();
        canvas.height = 500;
        canvasHolder.first().append(canvas);
        return;
    }

    // Initialize the canvas, add the listeners.
    function init() {
        tool = TOOL_ENUM.HAND;
        makeCanvas();
        if(null === canvas) {
            return;
        }
        ctx = canvas.getContext('2d');
        ctx.lineJoin = 'round';
        ctx.lineWidth = 3;
        pointRadius = ctx.lineWidth / 2 + ctx.lineWidth % 2;
        addCanvasListeners();
        addMenuListeners();
    }

    // Return an object with the init function mapped to init.
    return {
        init: init,
    };
}());

// On document ready, call drawWriteApp.init().
$(document).ready(drawWriteApp.init);
