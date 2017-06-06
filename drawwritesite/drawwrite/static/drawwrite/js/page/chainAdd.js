// Test whether the canvas wrapper exists on this page. If not, there's no
// need to do anything.
var canvasExists = (function () {

    // Seems like a good idea.
    "use strict";

    // Return whether the canvas exists or not.
    function test() {
        if($('#drawwriteCanvasWrapper').length > 0) {
            return true;
        } else {
            return false;
        }
    }

    return {
        test: test,
    };
}());

// Set up the canvas for drawing, and the menu for selecting tools.
var initCanvas = (function () {

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
    function toggleDrawTool(e) {
        var button = $('#drawToolButton');
        if(tool === TOOL_ENUM.DRAW) {
            tool = TOOL_ENUM.HAND;
            button.removeClass('active');
        } else if(tool === TOOL_ENUM.HAND) {
            tool = TOOL_ENUM.DRAW;
            button.addClass('active');
        }
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
        $('#drawToolButton').on('click', toggleDrawTool);
        addedMenuListeners = true;
    }

    // Create the canvas element, and make it the only child of the #drawwriteCanvasHolder div.
    function makeCanvas() {
        var canvasHolder = $('#drawwriteCanvasHolder');
        canvas = document.createElement('canvas');
        canvas.id = 'drawwriteCanvas';
        canvas.width = canvasHolder.width();
        canvas.height = 500;
        $(canvas).addClass('boxed');
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

// Setup the menu stickyness and the conversion from a drawing to a file.
var initMisc = (function () {

    // Seems like a good idea.
    "use strict";

    // Variables!
    var canvasTop, canvasLeft, canvasPositionTop, canvasPositionLeft;

    // Function to turn a canvas into a data-url.
    function makeDataUrl(e) {
        var canvas = document.getElementById('drawwriteCanvas');
        var data = canvas.toDataURL('image/png');
        $('#imgDataHolder').attr('value', data);
    }

    // Keep the draw menu at the top-left corner.
    function keepDrawMenuVisible() {
        var windowTop = $(window).scrollTop();
        var windowLeft = $(window).scrollLeft();
        var windowPositionTop = windowTop - canvasTop;
        var windowPositionLeft = windowLeft - canvasLeft;
        if(windowTop > canvasTop) {
            $('.canvas-menu').css('top', windowPositionTop + 1);
        } else {
            $('.canvas-menu').css('top', canvasPositionTop);
        }
        if(windowLeft > canvasLeft) {
            $('.canvas-menu').css('left', windowPositionLeft + 1);
        } else {
            $('.canvas-menu').css('left', canvasPositionLeft);
        }
    }

    // Attach event listeners.
    function attachEventListeners() {
        $('#postForm').submit(makeDataUrl);
        $(window).scroll(keepDrawMenuVisible);
    }

    // Read the canvas position into variables.
    function getCanvasPosition() {
        canvasTop = $('.canvas-menu').offset().top;
        canvasLeft = $('.canvas-menu').offset().left;
        canvasPositionTop = canvasTop - $('.canvas-menu').parent().offset().top;
        canvasPositionLeft = canvasLeft - $('.canvas-menu').parent().offset().left;
    }

    // Initialize variables, attach event handlers.
    function init() {
        getCanvasPosition();
        attachEventListeners();
    }

    // Return the init function.
    return {
        init: init,
    };
}());

// On document ready, initialize all the JS.
$(document).ready(function () {
    if(canvasExists.test()) {
        initCanvas.init();
        initMisc.init();
    }
});
