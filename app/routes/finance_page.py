from flask import Blueprint, render_template

finance_page = Blueprint("finance_page", __name__)

@finance_page.get("/finance")
def finance_home():
    return render_template("finance.html")
