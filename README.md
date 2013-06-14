<b>Ticket Restaurant Tool v0.10</b>

This project aims to provide a simple CLI tool to view an account balance and last movements of a Ticket Restaurant Account

<b>usage:</b> ticket.py [-h] [-s | -m] [-u <user>] [-p <password>] [-v] [-V]

Ticket Restaurant Tool v0.10 (c) David Silva 2013

<pre>
optional arguments:
  -h, --help            show this help message and exit
  -s, --saldo           checks the balance of the account
  -m, --movimentos      checks the movements of the account
  -u <user>, --user <user>
                        specifies the user for the authentication
  -p <password>, --password <password>
                        specifies the password for the authentication
  -v, --verbose         turns on the debug/verbose output
  -V, --version         show program's version number and exit

Either -s or -m must be provided
</pre>