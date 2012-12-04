$(document).ready(function() {
    updater.start();
});

var updater = {
    socket: null,

    start: function() {
        if("WebSocket" in window){
            var url = "ws://" + location.host + "/dashboard_socket";
            updater.socket = new WebSocket(url);

            updater.socket.onmessage = function(event) {
                updater.update(JSON.parse(event.data));
            }
        } else {
            $("#speed").text("Your browser doesn't support websockets. Sorry.");
        }
    },

    update: function(message) {
        $("hr").show();
        if(!message.paused){
            $("#speed").text(message.percent + "% @ " + parseInt(message.speed) + "kb/s")
            $("#name").text(message.name)
            $("#size").text(message.status + " - " + message.time_left + " left, " + message.size_left + "/" + message.size)

            var coming = $("#coming");

            for(i in message.waiting){
                var waiting = message.waiting[i];
                $("#" + i + " > h4").text(waiting.name);
                $("#" + i + " > p").text(waiting.status + " - " + waiting.percent + "% Done");
            }
        }
    }
};
