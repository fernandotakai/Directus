import logging
import tornado.escape
import tornado.ioloop
import tornado.options
import tornado.web
import tornado.websocket

from tornado.httpclient import AsyncHTTPClient

import os.path

from tornado.options import define, options

define("port", default=8888, help="run on the given port", type=int)

API_KEY = "750cceb52eee244d7a44a8a412d5f538"
SERVER_URL = "http://localhost:8085/sabnzbd/api?mode=queue&output=json&apikey=%s" % API_KEY

class Application(tornado.web.Application):
    def __init__(self):
        handlers = [
            ('/', MainHandler),
            ('/dashboard_socket', DashboardHandler)
        ]

        settings = dict(
            cookie_secret="c62878993e2711e2abeac82a1451e257c6287a0c3e2711e28ce2c82a1451e257",
            template_path=os.path.join(os.path.dirname(__file__), "templates"),
            static_path=os.path.join(os.path.dirname(__file__), "static"),
            xsrf_cookies=True,
            autoescape=None,
            debug=True,
        )
        tornado.web.Application.__init__(self, handlers, **settings)

class MainHandler(tornado.web.RequestHandler):
    def get(self):
        self.render("index.html")

class DashboardHandler(tornado.websocket.WebSocketHandler):

    clients = set()
    periodic_updater = None

    def open(self):
        logging.info("Opened %s, clients %s" % (self, DashboardHandler.clients))
        if not DashboardHandler.periodic_updater:
            logging.info("Starting updater")
            DashboardHandler.periodic_updater = tornado.ioloop.PeriodicCallback(DashboardHandler.callback, 4000)
            DashboardHandler.periodic_updater.start()

        DashboardHandler.clients.add(self)

    def on_close(self):
        DashboardHandler.clients.remove(self)
        logging.info("Closed %s, remaining %s" % (self, DashboardHandler.clients))

        if len(DashboardHandler.clients) == 0:
            DashboardHandler.periodic_updater.stop()
            DashboardHandler.periodic_updater = None

    @classmethod
    def callback(cls):
        http_client = AsyncHTTPClient()
        http_client.fetch(SERVER_URL, cls.handle_request)

    @classmethod
    def handle_request(cls, response):
        if response.error:
            logging.error("Error on response! %s" % response)
            return

        queue = tornado.escape.json_decode(response.body)['queue']
        slots = queue['slots']

        response = dict(speed=queue['kbpersec'], paused=queue['paused'], waiting=[])
        
        if slots:
            downloading = slots[0]
            response['name'] = downloading['filename']
            response['percent'] = downloading['percentage']
            response['size'] = downloading['size']
            response['size_left'] = downloading['sizeleft']
            response['time_left'] = downloading['timeleft']
            response['status'] = downloading['status']

            for slot in slots[1:5]:
                response['waiting'].append(dict(name=slot['filename'], 
                                             status=slot['status'], 
                                             percent=slot['percentage']))

        for client in cls.clients:
            client.write_message(response)

def main():
    tornado.options.parse_command_line()
    app = Application()
    app.listen(options.port, '0.0.0.0')
    print "Serving on %s" % options.port

    tornado.ioloop.IOLoop.instance().start()

if __name__ == "__main__":
    main()
