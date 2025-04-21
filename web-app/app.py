from flask import Flask, render_template

app = Flask(__name__)

@app.route("/")
def home():
    """Render the homepage."""
    return render_template("home.html")

if __name__ == "__main__":
    app.run(
        host="0.0.0.0", port=5003, debug=True, use_reloader=False, use_debugger=False
    )
