from flask import Flask, render_template, request, redirect, session, url_for, flash
import mysql.connector
import webbrowser
from werkzeug.serving import is_running_from_reloader
import pickle
import numpy as np
import joblib
import json
import io
import base64
import matplotlib.pyplot as plt

app=Flask(__name__)
app.secret_key = "123" 

@app.route('/')
def index():
    return render_template("index.html")

@app.route('/aboutus')
def aboutus():
    return render_template("aboutus.html")

@app.route("/contactus")
def contactus():
    return render_template("contactus.html")

#Admin Modules - Start -

# -----------------------------------------
# DATABASE CONNECTION
# -----------------------------------------
def get_db_connection():
    return mysql.connector.connect(
        host="localhost",
        port=3306,
        user="root",
        password="projain123",
        database="agriculturedatabase"
    )


# -----------------------------------------
# ADMIN LOGIN
# -----------------------------------------
@app.route("/adminlogin", methods=["GET", "POST"])
def admin_login():
    if request.method == "POST":
        adminid = request.form["adminid"]
        password = request.form["password"]

        conn = get_db_connection()
        cur = conn.cursor(dictionary=True)
        cur.execute("SELECT * FROM tbladmin WHERE adminid=%s AND password=%s", (adminid, password))
        admin = cur.fetchone()
        conn.close()

        if admin:
            session["adminid"] = adminid
            return redirect(url_for("admin_home"))
        else:
            flash("Invalid Login", "danger")

    return render_template("adminlogin.html")

# -----------------------------------------
# ADMIN LOGOUT
# -----------------------------------------
@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("admin_login"))

# -----------------------------------------
# ADMIN HOME DASHBOARD
# -----------------------------------------
@app.route("/adminhome")
def admin_home():
    if "adminid" not in session:
        return redirect(url_for("admin_login"))
    return render_template("adminhome.html")


# -----------------------------------------
# ADD MEMBERS
# -----------------------------------------
@app.route("/addmembers", methods=["GET", "POST"])
def add_members():
    if "adminid" not in session:
        return redirect(url_for("admin_login"))

    if request.method == "POST":
        mid = request.form["memberid"]
        pwd = request.form["password"]
        name = request.form["name"]
        mobile = request.form["mobile"]
        address = request.form["address"]

        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("INSERT INTO tblmembers(memberid, password, name, mobile, address) VALUES (%s, %s, %s, %s, %s)",
                    (mid, pwd, name, mobile, address))
        conn.commit()
        conn.close()
        flash("Member Added Successfully!", "success")
        return redirect(url_for("view_members"))

    return render_template("addmembers.html")


# -----------------------------------------
# VIEW MEMBERS
# -----------------------------------------
@app.route("/viewmembers")
def view_members():
    if "adminid" not in session:
        return redirect(url_for("admin_login"))

    conn = get_db_connection()
    cur = conn.cursor(dictionary=True)
    cur.execute("SELECT * FROM tblmembers")
    members = cur.fetchall()
    conn.close()

    return render_template("viewmembers.html", members=members)


# -----------------------------------------
# EDIT MEMBER
# -----------------------------------------
@app.route("/edit_member/<memberid>", methods=["GET", "POST"])
def edit_member(memberid):
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    if request.method == "POST":
        password = request.form["password"]
        name = request.form["name"]
        mobile = request.form["mobile"]
        address = request.form["address"]

        cursor.execute("""
            UPDATE tblmembers
            SET password=%s, name=%s, mobile=%s, address=%s
            WHERE memberid=%s
        """, (password, name, mobile, address, memberid))
        conn.commit()
        conn.close()
        flash("✅ Member details updated successfully!", "success")
        return redirect(url_for("view_members"))

    cursor.execute("SELECT * FROM tblmembers WHERE memberid=%s", (memberid,))
    member = cursor.fetchone()
    conn.close()

    if not member:
        flash("⚠️ Member not found.", "danger")
        return redirect(url_for("view_members"))

    return render_template("edit_member.html", member=member)


# -----------------------------------------
# DELETE MEMBER
# -----------------------------------------
@app.route("/deletemember/<memberid>")
def delete_member(memberid):
    if "adminid" not in session:
        return redirect(url_for("admin_login"))

    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("DELETE FROM tblmembers WHERE memberid=%s", (memberid,))
    conn.commit()
    conn.close()

    flash("Member Deleted Successfully!", "danger")
    return redirect(url_for("view_members"))


# -----------------------------------------
# UPDATE ADMIN PASSWORD
# -----------------------------------------
@app.route("/updatepassword", methods=["GET", "POST"])
def update_password():
    if "adminid" not in session:
        return redirect(url_for("admin_login"))

    if request.method == "POST":
        oldpass = request.form["oldpass"]
        newpass = request.form["newpass"]

        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("SELECT * FROM tbladmin WHERE adminid=%s AND password=%s", (session["adminid"], oldpass))
        admin = cur.fetchone()

        if admin:
            cur.execute("UPDATE tbladmin SET password=%s WHERE adminid=%s", (newpass, session["adminid"]))
            conn.commit()
            flash("Password Updated Successfully!", "success")
        else:
            flash("Old Password Incorrect!", "danger")

        conn.close()

    return render_template("updatepassword.html")


#Admin Modules - END -

#MEMBER MODULES - START -

# ---------------- MEMBER LOGIN ----------------
@app.route("/memberlogin", methods=["GET", "POST"])
def member_login():
    if request.method == "POST":
        mid = request.form["memberid"]
        pwd = request.form["password"]

        conn = get_db_connection()
        cur = conn.cursor(dictionary=True)
        cur.execute("SELECT * FROM tblmembers WHERE memberid=%s AND password=%s", (mid, pwd))
        data = cur.fetchone()
        conn.close()

        if data:
            session["memberid"] = mid
            return redirect(url_for("memberdashboard"))
        flash("Invalid Login", "danger")

    return render_template("memberlogin.html")


@app.route("/memberdashboard")
def memberdashboard():
    if "memberid" not in session:
        return redirect(url_for("member_login"))
    return render_template("memberdashboard.html")

@app.route("/memberupdatepassword", methods=["GET", "POST"])
def memberupdatepassword():
    if "memberid" not in session:
        flash("Please log in first!", "warning")
        return redirect(url_for("member_login"))

    member_id = session["memberid"]

    conn = get_db_connection()
    cursor = conn.cursor()

    if request.method == "POST":
        oldpass = request.form["oldpass"]
        newpass = request.form["newpass"]
        confirmpass = request.form["confirmpass"]

        cursor.execute("SELECT password FROM tblmembers WHERE memberid=%s", (member_id,))
        current_pass = cursor.fetchone()

        if not current_pass:
            flash("Member not found!", "danger")
        elif oldpass != current_pass[0]:
            flash("Old password is incorrect!", "danger")
        elif newpass != confirmpass:
            flash("New and Confirm Passwords do not match!", "warning")
        else:
            cursor.execute("UPDATE tblmembers SET password=%s WHERE memberid=%s", (newpass, member_id))
            conn.commit()
            flash("Password updated successfully!", "success")
            return redirect(url_for("memberupdatepassword"))

    cursor.close()
    conn.close()
    return render_template("memberupdatepassword.html")

#MEMBER MODULES - END -


# Load Models
rf_pulse = joblib.load("rf_pulse.pkl")
rf_vegetable = joblib.load("rf_vegetable.pkl")


@app.route("/pulsepredict", methods=["GET", "POST"])
def pulsepredict():
    import pandas as pd
    result = None

    if request.method == "POST":
        # Extract form inputs
        pulse_type = request.form["pulse_type"]
        season = request.form["season"]
        festival = request.form["festival"]
        market_demand = float(request.form["market_demand"])
        market_supply = float(request.form["market_supply"])
        import_cost = float(request.form["import_cost"])
        transport_cost = float(request.form["transport_cost"])

        # Create DataFrame with exact column names expected by model
        input_data = pd.DataFrame([{
            "pulse_type": pulse_type,
            "season": season,
            "festival": festival,
            "market_demand": market_demand,
            "market_supply": market_supply,
            "import_cost": import_cost,
            "transport_cost": transport_cost
        }])

        # Predict price using trained RF model
        result = round(rf_pulse.predict(input_data)[0], 2)

    return render_template("pulsepredict.html", result=result)


@app.route("/vegetablepredict", methods=["GET", "POST"])
def vegetablepredict():
    import pandas as pd
    result = None

    if request.method == "POST":
        # Extract form data
        seasonality = request.form["seasonality"]
        festival = request.form["festival"]
        transport_cost = float(request.form["transport_cost"])
        demand_index = float(request.form["demand_index"])
        supply_index = float(request.form["supply_index"])
        rainfall_level = float(request.form["rainfall_level"])

        # Create DataFrame with proper column names
        input_data = pd.DataFrame([{
            "seasonality": seasonality,
            "festival": festival,
            "transport_cost": transport_cost,
            "demand_index": demand_index,
            "supply_index": supply_index,
            "rainfall_level": rainfall_level
        }])

        # Predict using the trained RF model
        result = round(rf_vegetable.predict(input_data)[0], 2)

    return render_template("vegetablepredict.html", result=result)



@app.route("/pulse_knn_results")
def pulse_knn_results():
    with open("model_results_pulse_knn.json", "r") as f:
        r = json.load(f)
    return render_template("pulse_knn_results.html",
                           accuracy=r["Accuracy(%)"],
                           mae=r["MAE"],
                           time=r["Time_Taken(s)"])

@app.route("/pulse_rf_results")
def pulse_rf_results():
    with open("model_results_pulse_rf.json", "r") as f:
        r = json.load(f)
    return render_template("pulse_rf_results.html",
                           accuracy=r["Accuracy(%)"],
                           mae=r["MAE"],
                           time=r["Time_Taken(s)"])

@app.route("/vegetable_knn_results")
def vegetable_knn_results():
    with open("model_results_vegetable_knn.json", "r") as f:
        r = json.load(f)
    return render_template("vegetable_knn_results.html",
                           accuracy=r["Accuracy(%)"],
                           mae=r["MAE"],
                           time=r["Time_Taken(s)"])

@app.route("/vegetable_rf_results")
def vegetable_rf_results():
    with open("model_results_vegetable_rf.json", "r") as f:
        r = json.load(f)
    return render_template("vegetable_rf_results.html",
                           accuracy=r["Accuracy(%)"],
                           mae=r["MAE"],
                           time=r["Time_Taken(s)"])


@app.route("/graph")
def graph():
    # Load results
    with open("model_results_pulse_knn.json", "r") as f:
        pulse_knn = json.load(f)
    with open("model_results_pulse_rf.json", "r") as f:
        pulse_rf = json.load(f)
    with open("model_results_vegetable_knn.json", "r") as f:
        veg_knn = json.load(f)
    with open("model_results_vegetable_rf.json", "r") as f:
        veg_rf = json.load(f)

    # ----- Pulse Graph -----
    pulse_models = ["KNN", "Random Forest"]
    pulse_accuracy = [pulse_knn["Accuracy(%)"], pulse_rf["Accuracy(%)"]]
    pulse_time = [pulse_knn["Time_Taken(s)"], pulse_rf["Time_Taken(s)"]]

    fig1, ax = plt.subplots()
    ax.bar(pulse_models, pulse_accuracy)
    ax.set_ylabel("Accuracy (%)")
    ax.set_title("Pulse Price Prediction - Accuracy Comparison")

    img1 = io.BytesIO()
    plt.savefig(img1, format="png")
    img1.seek(0)
    pulse_accuracy_plot = base64.b64encode(img1.getvalue()).decode()

    plt.close()

    fig2, ax = plt.subplots()
    ax.bar(pulse_models, pulse_time)
    ax.set_ylabel("Time (seconds)")
    ax.set_title("Pulse Price Prediction - Time Efficiency Comparison")

    img2 = io.BytesIO()
    plt.savefig(img2, format="png")
    img2.seek(0)
    pulse_time_plot = base64.b64encode(img2.getvalue()).decode()

    plt.close()

    # ----- Vegetable Graph -----
    veg_models = ["KNN", "Random Forest"]
    veg_accuracy = [veg_knn["Accuracy(%)"], veg_rf["Accuracy(%)"]]
    veg_time = [veg_knn["Time_Taken(s)"], veg_rf["Time_Taken(s)"]]

    fig3, ax = plt.subplots()
    ax.bar(veg_models, veg_accuracy)
    ax.set_ylabel("Accuracy (%)")
    ax.set_title("Vegetable Price Prediction - Accuracy Comparison")

    img3 = io.BytesIO()
    plt.savefig(img3, format="png")
    img3.seek(0)
    vegetable_accuracy_plot = base64.b64encode(img3.getvalue()).decode()

    plt.close()

    fig4, ax = plt.subplots()
    ax.bar(veg_models, veg_time)
    ax.set_ylabel("Time (seconds)")
    ax.set_title("Vegetable Price Prediction - Time Efficiency Comparison")

    img4 = io.BytesIO()
    plt.savefig(img4, format="png")
    img4.seek(0)
    vegetable_time_plot = base64.b64encode(img4.getvalue()).decode()

    plt.close()

    # Render Template
    return render_template("graph.html",
                           pulse_accuracy_plot=pulse_accuracy_plot,
                           pulse_time_plot=pulse_time_plot,
                           vegetable_accuracy_plot=vegetable_accuracy_plot,
                           vegetable_time_plot=vegetable_time_plot)


@app.route("/compare")
def compare_models_page():
    import json, os

    # Load results
    def load_json(filename):
        if os.path.exists(filename):
            with open(filename, "r") as f:
                return json.load(f)
        return None

    pulse_knn = load_json("model_results_pulse_knn.json")
    pulse_rf = load_json("model_results_pulse_rf.json")
    veg_knn = load_json("model_results_vegetable_knn.json")
    veg_rf = load_json("model_results_vegetable_rf.json")

    if not all([pulse_knn, pulse_rf, veg_knn, veg_rf]):
        return render_template("compare.html", message="❌ Model results not found. Please train all models first.")

    pulse_results = [pulse_knn, pulse_rf]
    vegetable_results = [veg_knn, veg_rf]

    return render_template(
        "compare.html",
        pulse_results=pulse_results,
        vegetable_results=vegetable_results
    )

#EXECUTION OF THE APPLICATION
if __name__ == "__main__":
    # Only open browser once (avoid duplicate tabs when reloader runs)
    if not is_running_from_reloader():
        webbrowser.open_new_tab("http://127.0.0.1:5000/")

    app.run(port=5000, debug=True)

#END