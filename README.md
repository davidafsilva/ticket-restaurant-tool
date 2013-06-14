<b>Ticket Restaurant Tool v0.10</b>

This project aims to provide a simple CLI tool to view an account balance and last movements of a Ticket Restaurant Account

<b>usage:</b> ticket.py [-h] [-s | -m] [-u <user>] [-p <password>] [-v] [-V]

Ticket Restaurant Tool v0.10 (c) David Silva 2013

optional arguments:<br/>
  -h, --help            show this help message and exit<br/>
  -s, --saldo           checks the balance of the account<br/>
  -m, --movimentos      checks the movements of the account<br/>
  -u &lt;user&gt;, --user &lt;user&gt;<br/>
                        specifies the user for the authentication<br/>
  -p &lt;password&gt;, --password &lt;password><br/>
                        specifies the password for the authentication<br/>
  -v, --verbose         turns on the debug/verbose output<br/>
  -V, --version         show program's version number and exit<br/>

Either -s or -m must be provided