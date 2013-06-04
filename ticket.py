"""
Copyright (c) 2013, David Silva
All rights reserved.

Redistribution and use in source and binary forms, with or without
modification, are permitted provided that the following conditions are met:
        * Redistributions of source code must retain the above copyright
            notice, this list of conditions and the following disclaimer.
        * Redistributions in binary form must reproduce the above copyright
            notice, this list of conditions and the following disclaimer in the
            documentation and/or other materials provided with the distribution.
        * Neither the name of the <organization> nor the
            names of its contributors may be used to endorse or promote products
            derived from this software without specific prior written permission.

THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" AND
ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
DISCLAIMED. IN NO EVENT SHALL <COPYRIGHT HOLDER> BE LIABLE FOR ANY
DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES
(INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES;
LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND
ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
(INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS
SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
"""

import urllib
import urllib2
import sys
import datetime
from bs4 import BeautifulSoup

# configuration

configuration = {
    # authentication parameters
    "LOGIN_USER": "xxx",
    "LOGIN_PWD": "xxx",
    # tipically you don't need to change nothing below
    "DEBUG": True,
    "BASE_URL": "https://www.unibancoconnect.pt",
    "LOGIN_URL": "https://www.unibancoconnect.pt/login.aspx",
    "BALANCE_URL": "https://www.unibancoconnect.pt/Consultas/Saldos.aspx",
    "MOVEMENTS_URL": "https://www.unibancoconnect.pt/Consultas/UltimosMovimentos.aspx",
    "HTTP_USER_AGENT": "Mozilla/5.0 (Macintosh) AppleWebKit/537 Chrome/26 Safari/537",
}

# /configuration

# Table mapping response codes to messages;
http_codes = {
    100: ('Continue', 'Request received, please continue'),
    101: ('Switching Protocols',
          'Switching to new protocol; obey Upgrade header'),
    200: ('OK', 'Request fulfilled, document follows'),
    201: ('Created', 'Document created, URL follows'),
    202: ('Accepted',
          'Request accepted, processing continues off-line'),
    203: ('Non-Authoritative Information', 'Request fulfilled from cache'),
    204: ('No Content', 'Request fulfilled, nothing follows'),
    205: ('Reset Content', 'Clear input form for further input.'),
    206: ('Partial Content', 'Partial content follows.'),
    300: ('Multiple Choices',
          'Object has several resources -- see URI list'),
    301: ('Moved Permanently', 'Object moved permanently -- see URI list'),
    302: ('Found', 'Object moved temporarily -- see URI list'),
    303: ('See Other', 'Object moved -- see Method and URL list'),
    304: ('Not Modified',
          'Document has not changed since given time'),
    305: ('Use Proxy',
          'You must use proxy specified in Location to access this '
          'resource.'),
    307: ('Temporary Redirect',
          'Object moved temporarily -- see URI list'),
    400: ('Bad Request',
          'Bad request syntax or unsupported method'),
    401: ('Unauthorized',
          'No permission -- see authorization schemes'),
    402: ('Payment Required',
          'No payment -- see charging schemes'),
    403: ('Forbidden',
          'Request forbidden -- authorization will not help'),
    404: ('Not Found', 'Nothing matches the given URI'),
    405: ('Method Not Allowed',
          'Specified method is invalid for this server.'),
    406: ('Not Acceptable', 'URI not available in preferred format.'),
    407: ('Proxy Authentication Required', 'You must authenticate with '
          'this proxy before proceeding.'),
    408: ('Request Timeout', 'Request timed out; try again later.'),
    409: ('Conflict', 'Request conflict.'),
    410: ('Gone',
          'URI no longer exists and has been permanently removed.'),
    411: ('Length Required', 'Client must specify Content-Length.'),
    412: ('Precondition Failed', 'Precondition in headers is false.'),
    413: ('Request Entity Too Large', 'Entity is too large.'),
    414: ('Request-URI Too Long', 'URI is too long.'),
    415: ('Unsupported Media Type', 'Entity body in unsupported format.'),
    416: ('Requested Range Not Satisfiable',
          'Cannot satisfy request range.'),
    417: ('Expectation Failed',
          'Expect condition could not be satisfied.'),
    500: ('Internal Server Error', 'Server got itself in trouble'),
    501: ('Not Implemented',
          'Server does not support this operation'),
    502: ('Bad Gateway', 'Invalid responses from another server/proxy.'),
    503: ('Service Unavailable',
          'The server cannot process the request due to a high load'),
    504: ('Gateway Timeout',
          'The gateway server did not receive a timely response'),
    505: ('HTTP Version Not Supported', 'Cannot fulfill request.')
}

# version
VERSION = "0.10a1"


# Unibanco custom HTTP redirect handler
class UnibancoRedirectHandler(urllib2.HTTPRedirectHandler):
    def http_error_301(self, req, fp, code, msg, headers):
        """
        Handles the 301 redirects
        """
        result = urllib2.HTTPRedirectHandler.http_error_301(self, req, fp, code, msg, headers)
        result.headers = headers
        result.status = code
        return result

    def http_error_302(self, req, fp, code, msg, headers):
        """
        Handles the 302 redirects
        """
        result = urllib2.HTTPRedirectHandler.http_error_302(self, req, fp, code, msg, headers)
        result.headers = headers
        result.status = code
        return result


# Ticket Restaurant scraper
class TicketRestaurantScraper:
    def __init__(self):
        """
        Scraper constructor
        """
        self.cookies = None
        self.error = None

    def __config(self, key):
        """
        Gets the configuration for the given key
        """
        return configuration[key]

    def __is_debug_enabled(self):
        """
        Checks if is debug enabled
        """
        return self.__config("DEBUG")

    def __debug(self, txt):
        if self.__is_debug_enabled():
            print "[DEBUG]-["+str(datetime.datetime.now())+"] "+txt

    def __handle_http_error(self, exception):
        """
        Handles the HTTP errors catched
        """
        msg = "An error occurred while querying the server: %s - %s"
        if exception.code in http_codes:
            return msg % (str(exception.code), http_codes[exception.code][0])
        else:
            return msg % (str(exception.code), exception.reason)

    def __build_request(self, url, data):
        """
        Builds an HTTP request
        """
        request = urllib2.Request(url, data)
        request.add_header("User-Agent", configuration["HTTP_USER_AGENT"])
        request.add_header("Accept", "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8")
        request.add_header("Origin", self.__config("BASE_URL"))
        request.add_header("Accept-Encoding", "gzip")
        request.add_header("Cache-Control", "max-age=0")
        request.add_header("Connection", "keep-alive")
        if not self.cookies is None:
            request.add_header("Cookie", self.cookies)
        return request

    def __get(self, url):
        """
        Executes an HTTP GET request
        """
        try:
            request = self.__build_request(url, None)
            print request.headers
            response = urllib2.urlopen(request)
            return response
        except urllib2.HTTPError, e:
            self.error = self.__handle_http_error(e)
        except urllib2.URLError, e:
            self.error = "Unable to reach the server:", e.reason
        return None

    def __post(self, url, parameters):
        """
        Executes an HTTP POST request
        Valid for login action only
        """
        try:
            data = urllib.urlencode(parameters)
            request = self.__build_request(url, data)
            request.add_header("Content-Type", "application/x-www-form-urlencoded")
            request.add_header("Referer", self.__config("LOGIN_URL"))
            opener = urllib2.build_opener(UnibancoRedirectHandler())
            response = opener.open(request)
            return response
        except urllib2.HTTPError, e:
            self.error = self.__handle_http_error(e)
        except urllib2.URLError, e:
            self.error = "Unable to reach the server:", e.reason
        return None

    def __login(self):
        """
        Logs in into the server
        """
        # get the view state / validation
        url = self.__config("LOGIN_URL")
        results = self.__get(url)
        viewState = None
        viewValidation = None
        if not self.has_errors():
            self.cookies = results.info()['Set-Cookie']
            html = BeautifulSoup(results.read())
            viewState = html.find("input", {"id": "__VIEWSTATE"})["value"]
            viewValidation = html.find("input", {"id": "__EVENTVALIDATION"})["value"]
            self.__debug("__VIEWSTATE: %s" % (viewState))
            self.__debug("__EVENTVALIDATION: %s" % (viewValidation))
        else:
            self.__debug("unable to get view state / validation")
            return False

        user = self.__config("LOGIN_USER")
        pwd = self.__config("LOGIN_PWD")
        self.__debug("Logging in as " + user + "...")
        parameters = {}
        parameters['__EVENTTARGET'] = "ctl00$Conteudo$BtnConfirmar"
        parameters['__VIEWSTATE'] = viewState
        parameters['__EVENTVALIDATION'] = viewValidation
        parameters['__EVENTARGUMENT'] = ''
        parameters['__LASTFOCUS'] = ''
        parameters['ctl00$Conteudo$TxtUserCard'] = user
        parameters['ctl00$Conteudo$TxtPwd'] = pwd
        response = self.__post(url, parameters)
        html = response.read()
        if not self.has_errors():
            html = BeautifulSoup(html)
            err = html.find("div", {"id": "ctl00_Conteudo_SumaErro"})
            if not err is None:
                self.__debug("Login failed: %s" % (err.get_text().replace('\n', '')))
                return False
            else:
                hbconnect_cookie = response.info()["Set-Cookie"].split()[0]
                self.cookies = self.cookies.split()[0] + " " + hbconnect_cookie[:len(hbconnect_cookie)-1]
                self.__debug(self.cookies)
                self.__debug("Successfully logged in!")
                return True
        return False

    ## public methods ##

    def has_errors(self):
        """
        Checks if any error occured in the last request
        """
        return not self.error is None

    def get_error(self):
        """
        Gets the error message for the last request, if any
        """
        return self.error

    def get_balance(self):
        """
        Gets the balance of the account
        """
        self.__debug("fetching URL: " + self.__config("BALANCE_URL"))
        results = self.__get(self.__config("BALANCE_URL"))
        if not self.has_errors():
            html = BeautifulSoup(results.read())
            err = html.find("div", {"id": "ctl00_Conteudo_SumaErro"})
            if not err is None:
                self.error = err.get_text().replace('\n', '')
                self.__debug("Fetch balance failed: %s" % (self.error))
            else:
                pass

        return None

    def get_movements(self):
        """
        Gets the movements of the account
        """
        pass

    def login(self):
        return self.__login()


def __handle_operation(opt):
    """
    Handles a given operation
    """
    scraper = TicketRestaurantScraper()
    if scraper.login():
        if opt == 1:
            return scraper.get_balance()
        elif opt == 2:
            return scraper.get_movements()
    else:
        print scraper.get_error()
    return None


def help():
    """
    Prints a little help statement
    """
    print "Ticket Restaurant Tool v%s (c) David Silva" % (VERSION)
    print "Usage: %s [balance|movements]" % (sys.argv[0])


def main():
    if not len(sys.argv) == 2:
        help()
    else:
        opt = sys.argv[1].lower()
        if opt == 'balance' or opt == 'b':
            print __handle_operation(1)
        elif opt == 'movements' or opt == 'movs' or opt == 'mov' or opt == 'm':
            movements = __handle_operation(2)
            for mov in movements:
                print mov
        else:
            help()


# call the main
if __name__ == "__main__":
    main()
