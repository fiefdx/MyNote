(function() {
    var $msg = $('#msg');
    var $text = $('#text');
    var local = window.location.host;
    var uri = 'wss://' + local + '/websocket';
    console.log('Uri: ' + uri)

    var WebSocket = window.WebSocket || window.MozWebSocket;
    if (WebSocket) {
        try {
            var socket = new WebSocket(uri);
        } catch (e) {}
    }

    if (socket) {
        socket.onmessage = function(event) {
            $msg.append('<p>' + event.data + '</p>');
        }

        $('form').submit(function() {
            socket.send($text.val());
            $text.val('').select();
            return false;
        });
    }
})();