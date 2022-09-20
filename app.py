from flask import Flask, render_template, request, redirect, flash, session, url_for
from flask_mysqldb import MySQL
from passlib.hash import sha256_crypt
import random
import os
from datetime import datetime
app = Flask(__name__)
app.config['SECRET_KEY'] = 'abgtehysi#%^*TGysrekx'
app.config['MYSQL_HOST'] = '127.0.0.1'
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = 'root' 
app.config['MYSQL_DB'] = 'project_data'
mysql = MySQL(app)
@app.route('/')
def home():
    return render_template('index.html')

@app.route("/user")
def user():
    if "user" in session:
        user = session["user"]  
        return redirect(url_for("profile"))
    else:
        return redirect(url_for("Login"))

@app.route('/Login', methods = ["POST","GET"])
def Login():
    if "user" in session:
        return redirect(url_for("user"))
    if request.method == "POST":
        if len(request.form['email']) == 0 or len(request.form['password']) == 0:
            flash("Invalid credentials!")

        else:
            email = request.form['email']
            password = (request.form['password'])
            cursor = mysql.connection.cursor()
            cursor.execute('SELECT * FROM users WHERE email=%s', ([email]))
            account = cursor.fetchone()
            row_count = cursor.rowcount
            if row_count == 0:
                flash("You don't have an account, Please create an account!")
            elif account[2] == email and (sha256_crypt.verify(password,account[3])):
                session["id"] = account[0]
                session["username"] = account[1]
                session['user'] = "user"
                return redirect(url_for("home"))
            else:
                flash("Wrong password!")
    return render_template("login.html")

@app.route('/signup', methods = ['GET','POST'])
def signup():
    session.clear()
    if request.method == "POST":
        userDetails = request.form
        username = userDetails['username']
        email = userDetails['email']
        password = userDetails['password']
        if len(username) == 0 or len(email) == 0 or len(password) == 0:
            flash("Please fill the form completely!")
        else:            
            password = sha256_crypt.encrypt(password)
            cursor = mysql.connection.cursor()
            cursor.execute('SELECT * FROM users WHERE email=%s', (email,))
            account = cursor.fetchone()
            row_count = cursor.rowcount
            if row_count != 0:
                flash("You already have an account, Please sign in")
            else:
                session["email"] = email
                session["password"] = password
                session["username"] = username
                if request.method == "POST":
                    cur = mysql.connection.cursor()
                    now = datetime.now()
                    formatted_date = now.strftime('%Y-%m-%d %H:%M:%S')
                    cur.execute("INSERT INTO users(username, email, password, join_date) Values(%s,%s, %s, %s)",
                                (session["username"], session["email"], session["password"], formatted_date))
                    mysql.connection.commit()
                    session['email'] = cur.execute("SELECT email FROM users WHERE username=%s AND email=%s AND password=%s AND join_date=%s",
                                [session["username"], session["email"], (session["password"]), formatted_date])
                    cursor.execute('SELECT * FROM users WHERE email=%s', ([email]))
                    account = cursor.fetchone()
                    session['user'] = "user"
                    session['id'] = account[0]
                    return redirect(url_for('home'))
    return render_template('signup.html')

@app.route('/profile')
def profile():

    return render_template('profile.html')

@app.route("/logout")
def logout():
    session.pop("user",None)
    return redirect(url_for("home"))

def update_cart(user_id):
    cur = mysql.connection.cursor()
    cur.execute("SELECT * FROM cart WHERE user_id =%s", [user_id])
    rows = cur.fetchall()
    for row in rows:
        cur.execute("UPDATE cart SET quantity = %s WHERE id = %s", [row[3], row[0]])
        mysql.connection.commit()
    cur.close()

@app.route('/decrease_in_cart/<int:pro_id>')
def decrease_in_cart(pro_id):
    if "user" not in session:
        return redirect(url_for('Login'))
    cur = mysql.connection.cursor()
    cur.execute("SELECT * FROM cart WHERE user_id = %s AND pid=%s", [session["id"], pro_id])
    row = cur.fetchone()
    count = row[3] - 1
    cur.execute("UPDATE cart SET quantity = %s WHERE user_id = %s AND pid = %s",
                [count, session["id"], pro_id])
    mysql.connection.commit()
    if count == 0:
        cur.execute("DELETE FROM cart WHERE user_id = %s AND pid=%s", [session["id"], pro_id])
    mysql.connection.commit()
    cur.close()
    return redirect(url_for('cart'))

@app.route('/increase_in_cart/<int:pro_id>')
def increase_in_cart(pro_id):
    if "user" not in session:
        return redirect(url_for('Login'))
    cur = mysql.connection.cursor()
    cur.execute("SELECT * FROM cart WHERE user_id = %s AND pid=%s", [session["id"], pro_id])
    row = cur.fetchone()
    count = row[3] + 1
    cur.execute("UPDATE cart SET quantity = %s WHERE user_id = %s AND pid = %s",
                [count, session["id"], pro_id])
    mysql.connection.commit()
    cur.close()
    return redirect(url_for('cart'))

@app.route('/cart', methods=['GET', 'POST'])
def cart():
    if "user" not in session:
        return redirect(url_for('Login'))
    cur = mysql.connection.cursor()
    update_cart(session['id'])
    cur.execute("SELECT * FROM cart WHERE user_id LIKE %s", [session["id"]])
    cartitems = cur.fetchall()
    cnt = cur.rowcount
    cartlist = []
    tprice = 0
    for item in cartitems:
        cur = mysql.connection.cursor()
        pid = int(item[2])
        cur.execute("SELECT * FROM products WHERE pid LIKE %s", [pid])
        allproducts = cur.fetchall()
        Dict = {}
        for products in allproducts:
            Dict['pid'] = products[0]
            Dict['proname'] = products[1]
            Dict['quantity'] = item[3]
            Dict['price'] = products[2]
            Dict['totalprice'] = int(item[3]) * int(Dict['price'])
            cartlist.append(Dict)
            tprice = tprice + Dict['totalprice']
    return render_template('cart.html', carts=cartlist, totalprice=tprice, cnt = cnt)

@app.route('/shop')
def shop():
    cur = mysql.connection.cursor()
    category1 = []
    cur.execute('SELECT * FROM products')
    allproducts = cur.fetchall()
    for products in allproducts:
        Dict = {}
        Dict['pid'] = products[0]
        Dict['proname'] = products[1]
        Dict['price'] = products[2]
        category1.append(Dict)
    return render_template('category.html', category1=category1)

@app.route('/contact')
def contact():
    return render_template('contact.html')

@app.route('/single_product_page/<int:pro_id>', methods=['GET', 'POST'])
def single_product_page(pro_id):
    if "user" not in session:
        return redirect(url_for('Login'))
    update_cart(session['id'])
    cur = mysql.connection.cursor()
    cur.execute("SELECT * FROM products WHERE pid = %s", [pro_id])
    curr_product = cur.fetchone()
    curr_id = curr_product[0]
    pro_name = curr_product[1]
    curr_price = curr_product[2]
    cur.execute("SELECT * FROM cart WHERE user_id = %s AND pid = %s", [session["id"], pro_id])
    all_in_cart = cur.fetchall()
    total_in_cart = 0
    for row in all_in_cart:
        total_in_cart += row[3]
    cur.execute("SELECT * FROM cart WHERE user_id = %s AND pid = %s", [session["id"], pro_id])
    row_cnt = cur.rowcount
    in_cart = 0
    prod = 0
    # # agr already exist karta hai vo product cart me...
    if row_cnt != 0:
        prod = cur.fetchone()
        # quantity in cart already
        in_cart = prod[3]
    cur.close()
    if request.method == 'POST':
        if request.form['btn1'] == "Add to cart":
            quan = 1
            # if cart me exist nahi karta
            if row_cnt == 0:
                in_cart = 1
                total_in_cart += 1
                cur = mysql.connection.cursor()
                # saath me vid me daal dena idhar.....
                cur.execute("INSERT INTO cart(user_id, pid, quantity) Values(%s, %s, %s)",
                            (session["id"], pro_id, quan))
                # print("hello")
                mysql.connection.commit()
                cur.close()
            else:
                total_in_cart -= in_cart
                count = in_cart +1
                in_cart = count
                total_in_cart += count
                cur = mysql.connection.cursor()
                cur.execute("UPDATE cart SET quantity = %s WHERE user_id = %s AND pid = %s",
                            (count, session["id"], pro_id))
                mysql.connection.commit()
                cur.close()
            return render_template('single-product.html',  curr_id=curr_id,pro_name=pro_name,curr_price=curr_price)                                   
    return render_template('single-product.html', curr_id=curr_id,pro_name=pro_name,curr_price=curr_price)

@app.route('/checkout', methods=['GET', 'POST'])
def checkout():
    if "user" not in session:
        return render_template('login.html')
    if request.method == "POST":
        first_name = request.form['first']
        last_name = request.form['last']
        number = request.form['number']
        email = request.form['email']
        add1 = request.form['add1']
        city = request.form['city']
        Postcode = request.form['Postcode']
        if len(request.form['first'])==0 or len(request.form['last'])==0 or len(request.form['number'])==0 or len(request.form['email'])==0 or len(request.form['add1'])==0 or len(request.form['city'])==0 or len(request.form['Postcode'])==0:    
            flash("Please Fill all the necessary details!")
            cur = mysql.connection.cursor()
            cur.execute("SELECT * FROM cart WHERE user_id LIKE %s", [session["id"]])
            cartitems = cur.fetchall()
            cartlist = []
            tprice = 0
            for item in cartitems:
                cur = mysql.connection.cursor()
                pid = int(item[2])
                cur.execute("SELECT * FROM products WHERE pid LIKE %s", [pid])
                allproducts = cur.fetchall()
                Dict = {}
                for products in allproducts:
                    Dict['pid'] = products[0]
                    Dict['proname'] = products[1]
                    Dict['quantity'] = item[3]
                    Dict['price'] = products[2]
                    Dict['totalprice'] = item[3] * Dict['price']
                    cartlist.append(Dict)
                    tprice = tprice + Dict['totalprice']
            return render_template("checkout.html", carts=cartlist, totalprice=tprice)
        else:
            if request.form['btn2'] == "Proceed to Order": 
                cur = mysql.connection.cursor()
                now = datetime.now()
                formatted_date = now.strftime('%Y-%m-%d %H:%M:%S')
                cur.execute(
                    "INSERT INTO orders(first_name, last_name, number, email, add1, city, Postcode, datetime) Values(%s,%s, %s, %s, %s, %s, %s, %s)",
                    (first_name, last_name, number, email, add1, city, Postcode, formatted_date))
                mysql.connection.commit()
                cur.execute("SELECT * FROM cart WHERE user_id LIKE %s", [session["id"]])
                cartitems = cur.fetchall()
                cur.close()
                tprice = 0
                for item in cartitems:
                    cur = mysql.connection.cursor()
                    cur.execute("SELECT * FROM products WHERE pid=%s", [item[2]])
                    curr_price = cur.fetchone()
                    # for order id
                    cur.execute(
                        "SELECT * FROM orders WHERE first_name=%s AND last_name=%s AND number=%s AND email=%s AND add1=%s AND city=%s AND Postcode=%s AND datetime=%s",
                        [first_name, last_name, number, email, add1, city, Postcode, formatted_date])
                    curr_order = cur.fetchone()
                    cur.close()
                return redirect(url_for('confirmation', order_id=curr_order[0]))
    cur = mysql.connection.cursor()
    cur.execute("SELECT * FROM cart WHERE user_id LIKE %s", [session["id"]])
    cartitems = cur.fetchall()
    cartlist = []
    tprice = 0
    for item in cartitems:
        cur = mysql.connection.cursor()
        pid = int(item[2])
        cur.execute("SELECT * FROM products WHERE pid LIKE %s", [pid])
        allproducts = cur.fetchall()
        Dict = {}
        for products in allproducts:
            Dict['pid'] = products[0]
            Dict['proname'] = products[1]
            Dict['quantity'] = item[3]
            Dict['price'] = products[2]
            Dict['totalprice'] = item[3] * Dict['price']
            cartlist.append(Dict)
            tprice = tprice + Dict['totalprice']
    return render_template("checkout.html", carts=cartlist, totalprice=tprice)

@app.route('/confirmation/<int:order_id>', methods=['GET', 'POST'])
def confirmation(order_id):
    if "user" not in session:
        return redirect(url_for('login'))
    cur = mysql.connection.cursor()
    now = datetime.now()
    formatted_date = now.strftime('%Y-%m-%d %H:%M:%S')
    cur.execute("SELECT * FROM cart WHERE user_id LIKE %s", [session["id"]])
    cartitems = cur.fetchall()
    cur.execute("SELECT * FROM orders WHERE order_id = %s", [order_id])
    details = cur.fetchone()
    cartlist = []
    tprice = 0
    tquantity = 0
    for item in cartitems:
        pid = int(item[2])
        cur.execute("SELECT * FROM products WHERE pid LIKE %s", [pid])
        allproducts = cur.fetchall()
        Dict = {}
        for products in allproducts:
            Dict['pid'] = products[0]
            Dict['proname'] = products[1]
            Dict['quantity'] = item[3]
            Dict['price'] = products[2]
            tquantity += item[3]
            Dict['totalprice'] = item[3] * Dict['price']
            cartlist.append(Dict)
            tprice = tprice + Dict['totalprice']
    cur.execute("DELETE FROM cart WHERE user_id LIKE %s", [session["id"]])
    mysql.connection.commit()
    cur.close()

    return render_template("confirmation.html", carts=cartlist, totalprice=tprice, totalquantity=tquantity,
                           details=details)

@app.route('/bean')
def bean():
    return render_template('bean_bag.html')

@app.route('/sofa')
def sofa():
    return render_template('sofa.html')

if __name__ == '__main__':
    app.run(debug=True)