import os

from cs50 import SQL
from flask import Flask, flash, redirect, render_template, request, session
from flask_session import Session
from tempfile import mkdtemp
from werkzeug.exceptions import default_exceptions, HTTPException, InternalServerError
from werkzeug.security import check_password_hash, generate_password_hash

import datetime
dt = datetime.datetime.now()
from helpers import apology, login_required, lookup, usd
# export API_KEY=pk_e5bb8dde3ef64a05b4cf2dca4fcc6d75
# Configure application
app = Flask(__name__)

# Ensure templates are auto-reloaded
app.config["TEMPLATES_AUTO_RELOAD"] = True


# Ensure responses aren't cached
@app.after_request
def after_request(response):
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Expires"] = 0
    response.headers["Pragma"] = "no-cache"
    return response


# Custom filter
app.jinja_env.filters["usd"] = usd

# Configure session to use filesystem (instead of signed cookies)
app.config["SESSION_FILE_DIR"] = mkdtemp()
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# Configure CS50 Library to use SQLite database
db = SQL("sqlite:///finance.db")

# Make sure API key is set
if not os.environ.get("API_KEY"):
    raise RuntimeError("API_KEY not set")


@app.route("/")
@login_required
def index():

    """Show portfolio of stocks"""
    # get current session
    info = session.get("user_id")

    # query to users with id
    data = db.execute("SELECT * FROM users WHERE id =?",info)

    # query to transaction return a dictionary to get : symbol, name company
    # using SUM to get sum all share, and total money with persion id
    transaction = db.execute("SELECT symbol, company, SUM(shares), prices, SUM(total) FROM share_transaction WHERE person_id =? GROUP BY symbol",info)
    # print(f"{transaction}")

    for i in range(len(transaction)):
        transaction[i]['prices'] = usd(transaction[i]['prices'])
        transaction[i]['SUM(total)'] = usd(transaction[i]['SUM(total)'])
    # print(f"{transaction}")
    CASH = db.execute("SELECT SUM(addmoney) FROM addcash WHERE person_id =?",info)
    return render_template("index.html", data=data, transaction=transaction, CASH=CASH)


@app.route("/buy", methods=["GET", "POST"])
@login_required
def buy():
    """Buy shares of stock"""

    if request.method == "POST":

        share = request.form.get("shares", type = int)
        print(f"{share}")
        print(type(share))

        if not request.form.get("symbol"):
            return apology("missing symbol", 400)

        elif not share:
            return apology("missing shares", 400)

        elif int(share) < 0:
            return apology("invalid shares", 400)

      # get company info
        get_data = lookup(request.form.get("symbol"))
        # {'name': 'Agilent Technologies Inc.', 'price': 148.93, 'symbol': 'A'}
        if get_data == None:
            return apology("invalid symbol", 400)

        else:
            sym = get_data['symbol']
            price = get_data['price']
            name_com = get_data['name']

        # get datetime transasction
        time_record = dt.strftime("%Y-%m-%d %H:%M:%S")

      # query user cash
        info = session.get("user_id")
        get_cash = db.execute("SELECT cash FROM users WHERE id = ?",info)
        user_cash = get_cash[0]['cash']

        # calculate user buy and cash remaing
        shares = int(share)
        user_buy = shares * price

    # check if user_cash < user_buy then render apology
        if user_buy > user_cash:
            return apology("can't afford", 400)

    # insert new row trasaction to table
        else:
            cash_remain = user_cash - user_buy

             # update user_cash:
            db.execute("UPDATE users SET cash = ? WHERE id =?", cash_remain, info)
            rows = db.execute("INSERT INTO share_transaction (person_id, symbol, company, shares, prices, total, time)  VALUES (?, ?, ?, ?, ?, ?, ?)", info, sym, name_com, shares, price, user_buy, time_record)

            flash("Buy!")
            return redirect("/")
    return render_template("buy.html")


@app.route("/history")
@login_required
def history():
    """Show history of transactions"""
    point_trade_add = db.execute("SELECT addmoney, time FROM addcash")
    print(f"{point_trade_add}")

    point_trade = db.execute("SELECT symbol, shares, prices, time FROM share_transaction")
    return render_template("history.html", point_trade=point_trade, point_trade_add=point_trade_add)



# SELECT Orders.OrderID, Customers.CustomerName, Orders.OrderDate
# FROM Orders
# INNER JOIN Customers ON Orders.CustomerID=Customers.CustomerID;

@app.route("/login", methods=["GET", "POST"])
def login():
    """Log user in"""

    # Forget any user_id
    session.clear()

    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":

        # Ensure username was submitted
        if not request.form.get("username"):
            return apology("must provide username", 403)

        # Ensure password was submitted
        elif not request.form.get("password"):
            return apology("must provide password", 403)

        # Query database for username
        rows = db.execute("SELECT * FROM users WHERE username = ?", request.form.get("username"))

        # Ensure username exists and password is correct
        if len(rows) != 1 or not check_password_hash(rows[0]["hash"], request.form.get("password")):
            return apology("invalid username and/or password", 403)

        # Remember which user has logged in
        session["user_id"] = rows[0]["id"]

        # Redirect user to home page
        return redirect("/")

    # User reached route via GET (as by clicking a link or via redirect)
    else:
        return render_template("login.html")


@app.route("/logout")
def logout():
    """Log user out"""

    # Forget any user_id
    session.clear()

    # Redirect user to login form
    return redirect("/")


@app.route("/quote", methods=["GET", "POST"])
@login_required
def quote():
    """Get stock quote."""
    if request.method == "POST":
        company = request.form.get("symbol")
        result = lookup(company)

        if result == None:
            print("none")
            return apology("invalid symbol", 400)
        else:
            return render_template("quoted.html", result=result)
    return render_template("quote.html")


@app.route("/register", methods=["GET", "POST"])
def register():
    """Register user"""

        # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":

        # Ensure username was submitted
        if not request.form.get("username"):
            return apology("must provide username", 400)

        # Ensure password was submitted
        elif not request.form.get("password"):
            return apology("must provide password", 400)

        # ensure password was submitted
        elif not request.form.get("confirmation"):
            return apology("password don't match", 400)

        # ensure password and password again match
        elif (request.form.get("confirmation") != request.form.get("password")):
            return apology("password don't match", 400)

        rows = db.execute("SELECT username FROM users")
        print(f"{rows}")

        for user in rows :
            if request.form.get("username") == user['username']:
                return apology("already exist username", 400)

        # insert user into database
        username = request.form.get("username")
        password = generate_password_hash(request.form.get("password"))
        rows = db.execute("INSERT INTO users (username, hash)  VALUES (?, ?)", username, password)

        flash("Registered!")
        # Redirect user to home page
        return redirect("/login")
    # User reached route via GET (as by clicking a link or via redirect)
    else:
        return render_template("register.html")


@app.route("/sell", methods=["GET", "POST"])
@login_required
def sell():
    """Sell shares of stock"""

    list_company = db.execute("SELECT DISTINCT symbol from share_transaction")

    if request.method == "POST":

        time_record = dt.strftime("%Y-%m-%d %H:%M:%S")
        sell_shares = request.form.get("shares", type = int)
        symbol = request.form.get("symbol")

        if not sell_shares:
            return apology("missing symbol", 400)

        elif sell_shares < 0:
            return apology("invalid shares", 400)

        # get company info
        get_data = lookup(symbol)
        sym = get_data['symbol']
        price = get_data['price']
        name_com = get_data['name']

        # get user info
        info = session.get("user_id")
        shares = db.execute("SELECT SUM(shares) FROM share_transaction WHERE person_id =? AND symbol =? GROUP BY symbol",info, symbol)

        if sell_shares > shares[0]['SUM(shares)']:
            return apology("can't sell", 400)

        else:
            # money that sell share:
            user_sell = sell_shares * price

            # record sell shares:
            rows = db.execute("INSERT INTO share_transaction (person_id, symbol, company, shares, prices, total, time)  VALUES (?, ?, ?, ?, ?, ?, ?)", info, sym, name_com, (-1)*sell_shares, price, (-1)*user_sell, time_record)

            # update user cash:
            get_cash = db.execute("SELECT cash FROM users WHERE id =?", info)
            user_current_cash = get_cash[0]['cash']
            db.execute("UPDATE users SET cash =? WHERE id =?", user_current_cash + user_sell, info)

            flash("Sell!")
            return redirect("/")
    return render_template("sell.html", list_company=list_company)


@app.route("/add", methods=["GET", "POST"])
@login_required
def add_cash():

    if request.method == "POST":
        if not request.form.get("cash"):
            return apology("missing cash", 400)
        else:

            time_record = dt.strftime("%Y-%m-%d %H:%M:%S")
            info = session.get("user_id")
            get_cash = db.execute("SELECT cash FROM users WHERE id =?", info)
            user_current_cash = get_cash[0]['cash']
            db.execute("INSERT INTO addcash (person_id, addmoney, time) VALUES (?, ?, ?)", info, float(request.form.get("cash")), time_record)

            db.execute("UPDATE users SET cash =?", user_current_cash + float(request.form.get("cash")))
            return redirect("/")
    return render_template("add.html")


def errorhandler(e):
    """Handle error"""
    if not isinstance(e, HTTPException):
        e = InternalServerError()
    return apology(e.name, e.code)


# Listen for errors
for code in default_exceptions:
    app.errorhandler(code)(errorhandler)