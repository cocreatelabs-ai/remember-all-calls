from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
import requests
import os
from datetime import datetime

app = Flask(__name__)
app.secret_key = os.urandom(24)

# API Configuration
API_BASE_URL = os.getenv("API_BASE_URL", "http://54.165.176.205:8000")

@app.route("/health")
def health():
    """Simple health check"""
    return {"status": "healthy", "message": "Webapp is running"}


@app.route("/")
def dashboard():
    """Main dashboard showing all calls"""
    try:
        response = requests.get(f"{API_BASE_URL}/calls")
        calls = response.json() if response.status_code == 200 else []
    except Exception as e:
        flash(f"Error fetching calls: {str(e)}", "error")
        calls = []

    return render_template("dashboard.html", calls=calls)


@app.route("/upload", methods=["GET", "POST"])
def upload_call():
    """Upload call audio file"""
    if request.method == "POST":
        if "file" not in request.files:
            flash("No file selected", "error")
            return redirect(request.url)

        file = request.files["file"]
        if file.filename == "":
            flash("No file selected", "error")
            return redirect(request.url)

        try:
            files = {"file": (file.filename, file.stream, file.content_type)}
            response = requests.post(f"{API_BASE_URL}/upload-call", files=files)

            if response.status_code == 200:
                result = response.json()
                flash(f'File uploaded successfully! Call ID: {result["id"]}', "success")
                return redirect(url_for("dashboard"))
            else:
                flash(f"Upload failed: {response.text}", "error")
        except Exception as e:
            flash(f"Upload error: {str(e)}", "error")

    return render_template("upload.html")


@app.route("/call/<int:call_id>")
def call_detail(call_id):
    """Show detailed call information"""
    try:
        response = requests.get(f"{API_BASE_URL}/calls/{call_id}")
        if response.status_code == 200:
            call = response.json()
            return render_template("call_detail.html", call=call)
        else:
            flash("Call not found", "error")
            return redirect(url_for("dashboard"))
    except Exception as e:
        flash(f"Error fetching call details: {str(e)}", "error")
        return redirect(url_for("dashboard"))


@app.route("/api/call-status/<int:call_id>")
def call_status(call_id):
    """API endpoint to check call processing status"""
    try:
        response = requests.get(f"{API_BASE_URL}/calls/{call_id}")
        if response.status_code == 200:
            call = response.json()
            return jsonify({"status": call["status"]})
        else:
            return jsonify({"status": "error"}), 404
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
