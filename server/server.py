from flask import Flask, render_template, request
import os

app = Flask(__name__)

# Function to process the uploaded file
def process_file(file):
    # You can write your processing logic here
    # For this example, it simply reads the content of the file
    content = file.read().decode("utf-8")
    return content

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/upload", methods=["POST"])
def upload():
    if request.method == "POST":
        # Check if the post request has the file part
        if "file" not in request.files:
            return "No file part"
        file = request.files["file"]
        # If user does not select file, browser also
        # submits an empty part without filename
        if file.filename == "":
            return "No selected file"
        if file:
            result = process_file(file)
            return render_template("index.html", result=result)
    return "Something went wrong"

if __name__ == "__main__":
    app.run(debug=True, port=8000)
