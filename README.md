<h3>Ticket Restaurant Tool v0.11</h3>

This project aims to provide a simple CLI tool to view an account balance and last movements of a Ticket Restaurant Account

<pre>
<b>usage:</b> ticket.py [-h] [-s | -m] [-u <user>] [-p <password>] [-v] [-V]

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

<h3>Soon:</h3>
- Ordered movements
- Filtered movements (debit/credit)
- JSON output
- XML output 