from flask import Flask, render_template, request, redirect, url_for, flash, session
from werkzeug.security import generate_password_hash, check_password_hash
from db_connection import get_connection
from datetime import date
from decimal import Decimal

app = Flask(__name__)
app.secret_key = "change-this-development-secret"

def require_login():
    if "user_id" not in session:
        return redirect(url_for("login"))
    return None

def require_admin():
    if "user_id" not in session:
        return redirect(url_for("login"))
    if session.get("role") != "admin":
        flash("Only an administrator can update or delete existing records.", "error")
        return redirect(url_for("home"))
    return None

def fetch(sql, params=()):
    con = get_connection()
    cur = con.cursor(dictionary=True)
    try:
        cur.execute(sql, params)
        return cur.fetchall()
    finally:
        cur.close()
        con.close()

def run(sql, params=()):
    con = get_connection()
    cur = con.cursor()
    try:
        cur.execute(sql, params)
        con.commit()
    except Exception:
        con.rollback()
        raise
    finally:
        cur.close()
        con.close()


@app.route("/welcome")
def welcome():
    if "user_id" in session:
        return redirect(url_for("home"))
    return render_template("landing.html")

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        users = fetch("SELECT User_ID, Username, Password_Hash, Role FROM App_User WHERE Username=%s",
                      (request.form["username"].strip(),))
        requested_role = request.args.get("role", "").lower()
        if (users and check_password_hash(users[0]["Password_Hash"], request.form["password"])
                and (not requested_role or users[0]["Role"] == requested_role)):
            session.clear()
            session["user_id"] = users[0]["User_ID"]
            session["username"] = users[0]["Username"]
            session["role"] = users[0]["Role"]
            return redirect(url_for("home"))
        flash("Invalid username, password, or account type. Choose the correct login option.", "error")
    requested_role = request.args.get("role", "")
    return render_template("login.html", requested_role=requested_role)

@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        password = request.form["password"]
        if len(password) < 8:
            flash("Password must be at least 8 characters.", "error")
        else:
            try:
                run("INSERT INTO App_User(Username, Password_Hash, Role) VALUES(%s,%s,'user')",
                    (request.form["username"].strip(), generate_password_hash(password)))
                flash("Registration successful. Please log in.", "success")
                return redirect(url_for("login"))
            except Exception:
                flash("Username already exists or registration failed.", "error")
    return render_template("register.html")

@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))

@app.route("/")
def home():
    if "user_id" not in session:
        return render_template("landing.html")
    stats = {
        "products": fetch("SELECT COUNT(*) n FROM Product")[0]["n"],
        "categories": fetch("SELECT COUNT(*) n FROM Category")[0]["n"],
        "suppliers": fetch("SELECT COUNT(*) n FROM Supplier")[0]["n"],
        "customers": fetch("SELECT COUNT(*) n FROM Customer")[0]["n"],
        "stock": fetch("SELECT COALESCE(SUM(Stock_Quantity),0) n FROM Product")[0]["n"],
        "sales": fetch("SELECT COALESCE(SUM(Total_Amount),0) n FROM Sales_Invoice")[0]["n"]
    }
    low = fetch("SELECT Product_ID, Product_Name, Stock_Quantity, Reorder_Level FROM Product WHERE Stock_Quantity <= COALESCE(Reorder_Level,0)")
    return render_template("index.html", stats=stats, low=low)

@app.route("/products", methods=["GET", "POST"])
def products():
    gate = require_login()
    if gate: return gate
    if request.method == "POST":
        gate = require_login()
        if gate: return gate
        try:
            run("""INSERT INTO Product
                (Product_ID,Product_Name,Description,Unit_Price,Stock_Quantity,Reorder_Level,Category_ID)
                VALUES(%s,%s,%s,%s,%s,%s,%s)""",
                (request.form["id"], request.form["name"], request.form.get("description") or None,
                 request.form["price"], request.form.get("stock") or 0,
                 request.form.get("reorder") or None, request.form.get("category") or None))
            flash("Product added successfully.", "success")
        except Exception as e:
            flash(f"Could not add product: {e}", "error")
        return redirect(url_for("products"))
    rows = fetch("""SELECT p.*, c.Category_Name FROM Product p
                    LEFT JOIN Category c ON p.Category_ID=c.Category_ID
                    ORDER BY p.Product_ID""")
    cats = fetch("SELECT * FROM Category ORDER BY Category_Name")
    return render_template("products.html", rows=rows, cats=cats)

@app.route("/products/update/<int:pid>", methods=["POST"])
def update_product(pid):
    gate = require_login()
    if gate: return gate
    gate = require_admin()
    if gate: return gate
    try:
        run("""UPDATE Product SET Product_Name=%s, Description=%s, Unit_Price=%s,
               Stock_Quantity=%s, Reorder_Level=%s, Category_ID=%s WHERE Product_ID=%s""",
            (request.form["name"], request.form.get("description") or None, request.form["price"],
             request.form["stock"], request.form.get("reorder") or None,
             request.form.get("category") or None, pid))
        flash("Product updated.", "success")
    except Exception as e:
        flash(f"Update failed: {e}", "error")
    return redirect(url_for("products"))

@app.route("/products/delete/<int:pid>", methods=["POST"])
def delete_product(pid):
    gate = require_login()
    if gate: return gate
    gate = require_admin()
    if gate: return gate
    try:
        run("DELETE FROM Product WHERE Product_ID=%s", (pid,))
        flash("Product deleted.", "success")
    except Exception as e:
        flash(f"Cannot delete product if it is referenced by a purchase or sale: {e}", "error")
    return redirect(url_for("products"))

@app.route("/categories", methods=["GET", "POST"])
def categories():
    gate = require_login()
    if gate: return gate
    if request.method == "POST":
        gate = require_login()
        if gate: return gate
        try:
            run("INSERT INTO Category(Category_ID,Category_Name,Description) VALUES(%s,%s,%s)",
                (request.form["id"], request.form["name"], request.form.get("description") or None))
            flash("Category added.", "success")
        except Exception as e:
            flash(f"Could not add category: {e}", "error")
        return redirect(url_for("categories"))
    return render_template("categories.html", rows=fetch("SELECT * FROM Category ORDER BY Category_ID"))

@app.route("/suppliers", methods=["GET", "POST"])
def suppliers():
    gate = require_login()
    if gate: return gate
    if request.method == "POST":
        gate = require_login()
        if gate: return gate
        try:
            run("""INSERT INTO Supplier(Supplier_ID,Company_Name,Contact_Person,Phone,Email,Address)
                   VALUES(%s,%s,%s,%s,%s,%s)""",
                (request.form["id"], request.form["company"], request.form.get("contact"),
                 request.form.get("phone"), request.form.get("email") or None, request.form.get("address")))
            flash("Supplier added.", "success")
        except Exception as e:
            flash(f"Could not add supplier: {e}", "error")
        return redirect(url_for("suppliers"))
    return render_template("suppliers.html", rows=fetch("SELECT * FROM Supplier ORDER BY Supplier_ID"))

@app.route("/customers", methods=["GET", "POST"])
def customers():
    gate = require_login()
    if gate: return gate
    if request.method == "POST":
        gate = require_login()
        if gate: return gate
        try:
            run("""INSERT INTO Customer(Customer_ID,Customer_Name,Phone,Email,Address)
                   VALUES(%s,%s,%s,%s,%s)""",
                (request.form["id"], request.form["name"], request.form.get("phone"),
                 request.form.get("email") or None, request.form.get("address")))
            flash("Customer added.", "success")
        except Exception as e:
            flash(f"Could not add customer: {e}", "error")
        return redirect(url_for("customers"))
    return render_template("customers.html", rows=fetch("SELECT * FROM Customer ORDER BY Customer_ID"))

@app.route("/purchases", methods=["GET", "POST"])
def purchases():
    gate = require_login()
    if gate: return gate
    if request.method == "POST":
        gate = require_login()
        if gate: return gate
        con = get_connection()
        cur = con.cursor()
        try:
            qty = int(request.form["quantity"])
            cost = Decimal(request.form["cost"])
            discount = Decimal(request.form.get("discount") or "0")
            amount = qty * cost - discount
            if qty <= 0 or discount < 0 or discount > qty * cost:
                raise ValueError("Check quantity and discount.")
            cur.execute("SELECT Product_ID FROM Product WHERE Product_ID=%s FOR UPDATE", (request.form["product"],))
            if not cur.fetchone():
                raise ValueError("Product not found.")
            cur.execute("""INSERT INTO Purchase_Order(Purchase_ID,Purchase_Date,Total_Cost,Payment_Status,Supplier_ID)
                           VALUES(%s,%s,%s,%s,%s)""",
                        (request.form["id"], request.form["date"], amount, request.form["status"], request.form["supplier"]))
            cur.execute("""INSERT INTO Purchase_Order_Item(Purchase_ID,Product_ID,Quantity,Unit_Cost,Discount,Amount)
                           VALUES(%s,%s,%s,%s,%s,%s)""",
                        (request.form["id"], request.form["product"], qty, cost, discount, amount))
            cur.execute("UPDATE Product SET Stock_Quantity=Stock_Quantity+%s WHERE Product_ID=%s",
                        (qty, request.form["product"]))
            con.commit()
            flash("Purchase saved; stock increased.", "success")
        except Exception as e:
            con.rollback()
            flash(f"Purchase failed: {e}", "error")
        finally:
            cur.close()
            con.close()
        return redirect(url_for("purchases"))
    return render_template("purchases.html",
        rows=fetch("""SELECT po.*,s.Company_Name FROM Purchase_Order po LEFT JOIN Supplier s
                      ON po.Supplier_ID=s.Supplier_ID ORDER BY Purchase_Date DESC"""),
        suppliers=fetch("SELECT Supplier_ID,Company_Name FROM Supplier"),
        products=fetch("SELECT Product_ID,Product_Name FROM Product"), today=date.today().isoformat())

@app.route("/sales", methods=["GET", "POST"])
def sales():
    gate = require_login()
    if gate: return gate
    if request.method == "POST":
        gate = require_login()
        if gate: return gate
        con = get_connection()
        cur = con.cursor()
        try:
            qty = int(request.form["quantity"])
            price = Decimal(request.form["price"])
            discount = Decimal(request.form.get("discount") or "0")
            amount = qty * price - discount
            if qty <= 0 or discount < 0 or discount > qty * price:
                raise ValueError("Check quantity and discount.")
            cur.execute("SELECT Stock_Quantity FROM Product WHERE Product_ID=%s FOR UPDATE", (request.form["product"],))
            stock = cur.fetchone()
            if not stock or stock[0] < qty:
                raise ValueError("Product not found or insufficient stock.")
            cur.execute("""INSERT INTO Sales_Invoice(Sale_ID,Sale_Date,Total_Amount,Payment_Status,Customer_ID)
                           VALUES(%s,%s,%s,%s,%s)""",
                        (request.form["id"], request.form["date"], amount, request.form["status"], request.form["customer"]))
            cur.execute("""INSERT INTO Sales_Invoice_Item(Sale_ID,Product_ID,Quantity,Unit_Selling_Price,Discount,Amount)
                           VALUES(%s,%s,%s,%s,%s,%s)""",
                        (request.form["id"], request.form["product"], qty, price, discount, amount))
            cur.execute("UPDATE Product SET Stock_Quantity=Stock_Quantity-%s WHERE Product_ID=%s",
                        (qty, request.form["product"]))
            con.commit()
            flash("Sale saved; stock decreased.", "success")
        except Exception as e:
            con.rollback()
            flash(f"Sale failed: {e}", "error")
        finally:
            cur.close()
            con.close()
        return redirect(url_for("sales"))
    return render_template("sales.html",
        rows=fetch("""SELECT si.*,c.Customer_Name FROM Sales_Invoice si LEFT JOIN Customer c
                      ON si.Customer_ID=c.Customer_ID ORDER BY Sale_Date DESC"""),
        customers=fetch("SELECT Customer_ID,Customer_Name FROM Customer"),
        products=fetch("SELECT Product_ID,Product_Name,Unit_Price,Stock_Quantity FROM Product"),
        today=date.today().isoformat())

@app.route("/reports")
def reports():
    gate = require_login()
    if gate: return gate
    return render_template("reports.html",
        low=fetch("SELECT * FROM Product WHERE Stock_Quantity <= COALESCE(Reorder_Level,0)"),
        sales=fetch("SELECT Sale_Date,COUNT(*) Invoice_Count,SUM(Total_Amount) Total FROM Sales_Invoice GROUP BY Sale_Date ORDER BY Sale_Date DESC"),
        purchases=fetch("SELECT Purchase_Date,COUNT(*) Order_Count,SUM(Total_Cost) Total FROM Purchase_Order GROUP BY Purchase_Date ORDER BY Purchase_Date DESC"))

if __name__ == "__main__":
    app.run(debug=True)
