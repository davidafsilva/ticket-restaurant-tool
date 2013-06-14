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
import re
import argparse
from bs4 import BeautifulSoup, element

# configuration

configuration = {
    # authentication parameters (if not set by -u and -p options)
    "LOGIN_USER": "xxx",
    "LOGIN_PWD": "xxx",
    # tipically you don't need to change nothing below
    "DEBUG": False,
    "BASE_URL": "https://www.unibancoconnect.pt",
    "LOGIN_URL": "https://www.unibancoconnect.pt/login.aspx",
    "BALANCE_URL": "https://www.unibancoconnect.pt/Consultas/Saldos.aspx",
    "MOVEMENTS_URL": "https://www.unibancoconnect.pt/Consultas/UltimosMovimentos.aspx",
    "HTTP_USER_AGENT": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_7_5) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/27.0.1453.110 Safari/537.36"
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
VERSION = "0.11"


# Movement class
class UnibancoMovement:
    def __init__(self, date, description, debit_amount, credit_amount):
        """
        constructor
        """
        self.date = date
        self.description = " ".join(description.split())
        self.__is_debit = credit_amount is None or len(credit_amount) == 0
        if self.__is_debit:
            self.amount = debit_amount
        else:
            self.amount = credit_amount

    def get_date(self):
        """
        Get the movement date
        """
        return self.date

    def get_description(self):
        """
        Get the movement description
        """
        return self.description

    def is_debit(self):
        """
        Check if the movement is a debit
        """
        return self.__is_debit

    def is_credit(self):
        """
        Check if the movement is a credit
        """
        return not self.__is_debit

    def get_amount(self):
        """
        Gets the movement amount
        """
        return self.amount

    def __str__(self):
        """
        String representation method
        """
        if self.is_credit():
            _mov = u"Credit: "
        else:
            _mov = u"Debit: "
        _mov += self.get_description() + " (" + self.get_date() + ")" + " - " + self.get_amount()
        return _mov


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
        request.add_header("DNT", "1")
        request.add_header("User-Agent", self.__config("HTTP_USER_AGENT"))
        if not self.cookies is None:
            request.add_header("Cookie", self.cookies)
        return request

    def __get(self, url):
        """
        Executes an HTTP GET request
        """
        try:
            request = self.__build_request(url, None)
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

    def __login(self, user, pwd):
        """
        Logs in into the server
        """
        # get the view state / validation
        self.__debug("getting view state, event validation...")
        url = self.__config("LOGIN_URL")
        results = self.__get(url)
        viewState = None
        viewValidation = None
        if not self.has_errors():
            html = BeautifulSoup(results.read())
            viewState = html.find("input", {"id": "__VIEWSTATE"})["value"]
            viewValidation = html.find("input", {"id": "__EVENTVALIDATION"})["value"]
            self.__debug("__VIEWSTATE: %s" % (viewState))
            self.__debug("__EVENTVALIDATION: %s" % (viewValidation))
        else:
            self.__debug("unable to get view state / validation")
            return False

        self.__debug("Logging in as " + user + "...")
        parameters = {}
        parameters['__EVENTTARGET'] = "ctl00$Conteudo$BtnConfirmar"
        parameters['__VIEWSTATE'] = viewState
        parameters['__EVENTVALIDATION'] = viewValidation
        parameters['ctl00$Conteudo$TxtUserCard'] = user
        parameters['ctl00$Conteudo$TxtPwd'] = pwd
        response = self.__post(url, parameters)
        html = response.read()
        if not self.has_errors():
            html = BeautifulSoup(html)
            err = html.find("div", {"id": "ctl00_Conteudo_SumaErro"})
            if not err is None:
                self.error = err.get_text().replace('\n', '')
                self.__debug("Login failed: %s" % (self.error))
                return False
            else:
                self.cookies = self.__parse_cookies(response.info())
                self.__debug("Cookies: " + self.cookies)
                self.__debug("Successfully logged in!")
                return True
        return False

    def __parse_cookies(self, headers):
        """
        Parses the received cookies
        """
        ret = None
        if "Set-Cookie" in headers:
            cookies = headers["Set-Cookie"]
            idx = 0
            pattern = re.compile(r';|,')
            for cookie in pattern.split(cookies):
                cookie = cookie.strip()
                idx = cookie.find("=")
                if idx >= 0:
                    if cookie[:idx] == "ASP.NET_SessionId" or cookie[:idx] == ".HBCONNECT":
                        if ret is None:
                            ret = cookie.strip()
                        else:
                            if ret[-1] == ";":
                                ret = ret + " " + cookie.strip()
                            else:
                                ret = ret + "; " + cookie.strip()

        return ret

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

    def __do_http_operation(self, url):
        self.__debug("fetching URL: " + url)
        results = self.__get(url)
        if not self.has_errors():
            html = BeautifulSoup(results.read())
            err = html.find("div", {"id": "ctl00_Conteudo_SumaErro"})
            if not err is None:
                self.error = err.get_text().replace('\n', '')
                self.__debug("Fetch balance failed: %s" % (self.error))
            else:
                return html
        return None

    def get_balance(self):
        """
        Gets the balance of the account
        """
        html = self.__do_http_operation(self.__config("BALANCE_URL"))
        if not html is None:
            balance = html.find("span", {"id": "ctl00_Conteudo_lblMontDisponivel"}).get_text()
            return balance
        return None

    def get_movements(self):
        """
        Gets the movements of the account
        """
        html = self.__do_http_operation(self.__config("MOVEMENTS_URL"))
        movements = []
        if not html is None:
            div_container = html.find("div", {"id": "ctl00_Conteudo_PanelConteud"})
            m_table = div_container.find_all(["table"])[1]
            for idx in range(5, len(m_table.contents)):
                tr = m_table.contents[idx]
                if type(tr) is element.Tag:
                    td_date = tr.contents[0].get_text().strip()
                    td_description = tr.contents[1].get_text().strip()
                    td_debit = tr.contents[2].get_text().strip()
                    td_credit = tr.contents[3].get_text().strip()
                    movements.append(UnibancoMovement(td_date, td_description, td_debit, td_credit))
        return movements

    def login(self, user, pwd):
        return self.__login(user, pwd)


def __handle_operation(opt, user, pwd):
    """
    Handles a given operation
    """
    scraper = TicketRestaurantScraper()
    if scraper.login(user, pwd):
        if opt == 1:
            return scraper.get_balance()
        elif opt == 2:
            return scraper.get_movements()
    else:
        print scraper.get_error()
    return None


# arg parser
parser = argparse.ArgumentParser(description='Ticket Restaurant Tool v%s (c) David Silva 2013' % (VERSION), epilog="Either -s or -m must be provided")
group = parser.add_mutually_exclusive_group()
group.add_argument('-s', '--saldo', action='store_true', help='checks the balance of the account')
group.add_argument('-m', '--movimentos', action='store_true', help='checks the movements of the account')
parser.add_argument('-u', '--user', metavar='<user>', default=configuration["LOGIN_USER"], help='specifies the user for the authentication')
parser.add_argument('-p', '--password', metavar='<password>', default=configuration["LOGIN_PWD"], help='specifies the password for the authentication')
parser.add_argument('-v', '--verbose', action='store_true', help='turns on the debug/verbose output')
parser.add_argument('-V', '--version', action='version', version='Ticket Restaurant v%s' % (VERSION))
args = parser.parse_args()

# setup debug
configuration["DEBUG"] = args.verbose

# execute the options
if args.saldo:
    balance = __handle_operation(1, args.user, args.password)
    if not balance is None:
        print "Montante dispon" + u"\u00ED" + "vel: " + balance + u"\u20AC"
elif args.movimentos:
    movements = __handle_operation(2, args.user, args.password)
    if not movements is None and len(movements) > 0:
        for mov in movements:
            print str(mov)
    elif not movements is None:
        print "Nenhum movimento efectuado"
else:
    parser.error("Either -s or -m must be provided.\n%s -h for help" % (sys.argv[0]))
