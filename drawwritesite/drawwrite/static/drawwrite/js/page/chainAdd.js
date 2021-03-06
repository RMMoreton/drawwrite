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
    var canvas, ctx, pointRadius, paint, wasPath, prevX, prevY, init, tool, TOOL_ENUM, addedMenuListeners,
        canvasStates, drawEvents, currentDrawEvent, undoParameter, colors, currentColor;

    addedMenuListeners = false;

    // Create the 'tool' object.
    var TOOL_ENUM = {
        DRAW: "draw",
        HAND: "hand",
    }

    // Create the colors.
    colors = {
        BLACK: '#000000',
        WHITE: '#FFFFFF',
        BROWN: '#987654',
        RED: '#FF0000',
        ORANGE: '#FF7F00',
        YELLOW: '#FFFF00',
        ELECTRICGREEN: '#7FFF00',
        GREEN: '#00FF00',
        TEAL: '#00FF7F',
        LIGHTBLUE: '#00FFFF',
        ROYALBLUE: '#007FFF',
        BLUE: '#0000FF',
        PURPLE: '#7F00FF',
        MAGENTA: '#FF00FF',
        PINK: '#FF007F',
    }

    // Toggle the "draw" tool.
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

    // Draw a dot where the a touch ended. This does not get executed if the
    // user draws a line (because wasPath will be set to true).
    function dot(e) {
        if(tool !== TOOL_ENUM.DRAW) {
            return;
        }
        if(currentDrawEvent === null) {
            return;
        }
        if(wasPath === true) {
            wasPath = false;
        } else {
            var offsets = $(this).offset()
            ctx.beginPath();
            ctx.arc(e.pageX-offsets.left, e.pageY-offsets.top, pointRadius, 0, 2*Math.PI);
            ctx.fill();
            // Add data to the currentDrawEvent.
            currentDrawEvent.type = 'dot';
            currentDrawEvent.radius = pointRadius;
            // Push currentDrawEvent onto drawEvents and set to null.
            drawEvents.push(currentDrawEvent);
            currentDrawEvent = null;
        }
    }

    // Start painting, and initalize the two 'previous' positions.
    function startPath(e) {
        if(tool !== TOOL_ENUM.DRAW) {
            return;
        }
        var offsets = $(this).offset()
        paint = true;
        wasPath = false;
        prevX = (e.type === 'touchstart' ? e.changedTouches[0].pageX : e.pageX) - offsets.left;
        prevY = (e.type === 'touchstart' ? e.changedTouches[0].pageY : e.pageY) - offsets.top;
        // Save the state of the canvas if I need to.
        if(drawEvents.length % undoParameter === 0) {
            canvasStates.push(ctx.getImageData(0, 0, canvas.width, canvas.height));
        }
        // Initialize currentDrawEvent.
        currentDrawEvent = {
            path: [prevX, prevY],
            type: 'path',
            radius: ctx.lineWidth,
            color: currentColor,
        }
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

            // Add prevX and prevY to the current draw event.
            currentDrawEvent.path.push(prevX);
            currentDrawEvent.path.push(prevY);

        }
        // Prevent the user from swiping left/right for navigation.
        e.preventDefault();
    }

    // If we end on the canvas, don't unset wasPath (in case this was a click),
    // but do unset everything else. If wasPath, push currentDrawEvent and set to null;
    // if not, don't do either of those things.
    function endPathOnCanvas(e) {
        if(!paint) {
            return;
        }
        paint = false;
        prevX = null;
        prevY = null;
        if(wasPath) {
            drawEvents.push(currentDrawEvent);
            currentDrawEvent = null;
        }
    }

    // If we end off the canvas, then unset everything. Also push the currentDrawEvent
    // onto the drawEvents stack.
    function endPathOffCanvas(e) {
        if(!paint) {
            return;
        }
        paint = false;
        wasPath = false;
        prevX = null;
        prevY = null;
        drawEvents.push(currentDrawEvent);
        currentDrawEvent = null;
    }

    // Undo the most recent drawing event.
    function undo() {
        // If there are no canvasStates, return.
        if(canvasStates === null || canvasStates.length === 0) {
            return;
        }
        // If there are no draw events, return.
        if(drawEvents === null || drawEvents.length === 0) {
            return;
        }

        drawEvents.pop();
        var numToRedraw = drawEvents.length % undoParameter;
        if(numToRedraw === 0) {
            var restore = canvasStates.pop();
            ctx.putImageData(restore, 0, 0);
        } else {
            var restore = canvasStates[canvasStates.length - 1];
            ctx.putImageData(restore, 0, 0);
            for(var i = 0; i < numToRedraw; i++) {
                redraw(drawEvents[drawEvents.length - numToRedraw+i]);
            }
        }
    }

    // Redraw a drawEvent.
    function redraw(drawEvent) {
        ctx.strokeStyle = drawEvent.color;
        ctx.fillStyle = drawEvent.color;
        if(drawEvent.type === 'dot') {
            ctx.beginPath();
            ctx.arc(drawEvent.path[0], drawEvent.path[1], drawEvent.radius, 0, 2*Math.PI);
            ctx.fill();
        } else if(drawEvent.type === 'path') {
            // Save current line width.
            var currentLineWidth = ctx.lineWidth;
            ctx.lineWidth = drawEvent.radius;
            for(var i = 0; i < drawEvent.path.length - 2; i += 2) {
                ctx.beginPath();
                ctx.moveTo(drawEvent.path[i], drawEvent.path[i+1]);
                ctx.lineTo(drawEvent.path[i+2], drawEvent.path[i+3]);
                ctx.closePath();
                ctx.stroke();
            }
            // Restore line width.
            ctx.lineWidth = currentLineWidth;
        }
        ctx.strokeStyle = currentColor;
        ctx.fillStyle = currentColor;
    }

    // Change the color.
    function changeColor(newColor) {
        currentColor = newColor;
        ctx.strokeStyle = newColor;
        ctx.fillStyle = newColor;
        $('.colorBlockCurrent').css('background-color', newColor);
    }

    // Change the pen size.
    function setPenWidth(newWidth) {
        ctx.lineWidth = newWidth;
        pointRadius = parseInt(newWidth / 2) + newWidth % 2;
        setShowingSize(newWidth);
    }

    // Change the size of the pen we show to the user.
    function setShowingSize(newWidth) {
        $('.currentSizeHolder').text(newWidth + ' px');
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
        $('.sizeToolInput').on('input', function() { setShowingSize( $('.sizeToolInput').val()); });
        $('.sizeToolInput').on('change', function() { setPenWidth( $('.sizeToolInput').val()); });
        $('.colorBlack').on('click', function() { changeColor(colors.BLACK) });
        $('.colorWhite').on('click', function() { changeColor(colors.WHITE) });
        $('.colorBrown').on('click', function() { changeColor(colors.BROWN) });
        $('.colorRed').on('click', function() { changeColor(colors.RED) });
        $('.colorOrange').on('click', function() { changeColor(colors.ORANGE) });
        $('.colorYellow').on('click', function() { changeColor(colors.YELLOW) });
        $('.colorElectricGreen').on('click', function() { changeColor(colors.ELECTRICGREEN) });
        $('.colorGreen').on('click', function() { changeColor(colors.GREEN) });
        $('.colorTeal').on('click', function() { changeColor(colors.TEAL) });
        $('.colorLightBlue').on('click', function() { changeColor(colors.LIGHTBLUE) });
        $('.colorRoyalBlue').on('click', function() { changeColor(colors.ROYALBLUE) });
        $('.colorBlue').on('click', function() { changeColor(colors.BLUE) });
        $('.colorPurple').on('click', function() { changeColor(colors.PURPLE) });
        $('.colorMagenta').on('click', function() { changeColor(colors.MAGENTA) });
        $('.colorPink').on('click', function() { changeColor(colors.PINK) });
        $('.undoToolButton').on('click', undo);
        addedMenuListeners = true;
    }

    // Add colors to all the color block elemnts.
    function addColorToColorBlocks() {
        $('.colorBlockBlack').css('background-color', colors.BLACK);
        $('.colorBlockWhite').css('background-color', colors.WHITE);
        $('.colorBlockBrown').css('background-color', colors.BROWN);
        $('.colorBlockRed').css('background-color', colors.RED);
        $('.colorBlockOrange').css('background-color', colors.ORANGE);
        $('.colorBlockYellow').css('background-color', colors.YELLOW);
        $('.colorBlockElectricGreen').css('background-color', colors.ELECTRICGREEN);
        $('.colorBlockGreen').css('background-color', colors.GREEN);
        $('.colorBlockTeal').css('background-color', colors.TEAL);
        $('.colorBlockLightBlue').css('background-color', colors.LIGHTBLUE);
        $('.colorBlockRoyalBlue').css('background-color', colors.ROYALBLUE);
        $('.colorBlockBlue').css('background-color', colors.BLUE);
        $('.colorBlockPurple').css('background-color', colors.PURPLE);
        $('.colorBlockMagenta').css('background-color', colors.MAGENTA);
        $('.colorBlockPink').css('background-color', colors.PINK);
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

        canvasStates = new Array();
        drawEvents = new Array();
        undoParameter = 50;

        makeCanvas();
        if(null === canvas) {
            return;
        }
        ctx = canvas.getContext('2d');
        ctx.fillStyle = colors.WHITE
        ctx.rect(0, 0, canvas.width, canvas.height);
        ctx.fill();
        ctx.lineJoin = 'round';
        ctx.strokeStyle = currentColor;
        ctx.fillStyle = currentColor;

        setPenWidth(3);
        $('.sizeToolInput').val(3);

        addColorToColorBlocks();
        changeColor(colors.BLACK);

        addCanvasListeners();
        addMenuListeners();
    }

    function getCanvasStates() {
        return canvasStates;
    }

    function getDrawEvents() {
        return drawEvents;
    }

    // Return an object with the init function mapped to init.
    return {
        init: init,
        setPenWidth: setPenWidth,
    };
}());

// Setup the menu stickyness and the conversion from a drawing to a file.
var initMisc = (function () {

    // Seems like a good idea.
    "use strict";

    // Variables!
    var canvasTop, canvasLeft;

    // Function to turn a canvas into a data-url.
    function makeDataUrl(e) {
        var canvas = document.getElementById('drawwriteCanvas');
        var data = canvas.toDataURL('image/png');
        $('#imgDataHolder').attr('value', data);
    }

    // Keep the draw menu at the top-left corner.
    function keepDrawMenuVisible() {
        var windowTop = $(window).scrollTop();
        if(windowTop > canvasTop) {
            if($('.canvas-menu').css('position') !== 'fixed') {
                $('.canvas-menu').css('position', 'fixed');
                $('.canvas-menu').css('top', '0px');
                $('.canvas-menu').css('left', canvasLeft + 'px');
            }
        } else {
            if($('.canvas-menu').css('position') !== 'absolute') {
                $('.canvas-menu').css('position', 'absolute');
                $('.canvas-menu').css('top', '1px');
                $('.canvas-menu').css('left', '1px');
            }
        }
    }

    // Read the canvas position into variables.
    function getCanvasPosition() {
        canvasTop = $('.canvas-menu').offset().top;
        canvasLeft = $('.canvas-menu').offset().left;
    }

    // Attach event listeners.
    function attachEventListeners() {
        $('#postForm').submit(makeDataUrl);
        $(window).scroll(keepDrawMenuVisible);
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
