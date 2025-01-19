import io
import pdfplumber
import re
from collections import OrderedDict
from flask import Flask, render_template, request, jsonify, redirect, make_response, session
import requests
import hashlib
import random
import string
import pdfplumber

app = Flask(__name__)
app.secret_key = 'your_unique_secret_key'

database_url = "https://medcompanion-e671e-default-rtdb.firebaseio.com"
session_store = {}
def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()
def generate_session_token():
    return ''.join(random.choices(string.ascii_letters + string.digits, k=32))

@app.route('/register', methods=['POST'])
def register():
    data = request.json
    username = data['username']
    email = data['email']
    password = hash_password(data['password'])
    users = requests.get(f"{database_url}/users.json").json() or {}
    if any(user.get('email') == email for user in users.values()):
        return jsonify({"error": "User already exists"}), 400
    new_user = {"username": username, "email": email, "password": password}
    response = requests.post(f"{database_url}/users.json", json=new_user)
    if response.ok:
        return jsonify({"message": "Registration successful"}), 201
    return jsonify({"error": "Registration failed"}), 500

@app.route('/blogs/<blog_id>/comments', methods=['POST'])
def add_comment(blog_id):
    # Ensure JSON data is received
    data = request.get_json()
    if not data or "content" not in data or "email" not in data:
        return jsonify({"error": "Content and email are required."}), 400

    # Construct the new comment
    comment = {
        "content": data["content"],
        "email": data["email"],
        "replies": {}
    }

    # Fetch existing comments for the blog
    response = requests.get(f"{database_url}/blogs/{blog_id}/comments.json")
    if response.status_code != 200:
        return jsonify({"error": "Failed to fetch comments."}), 500

    comments = response.json() or {}  # Load comments or initialize as empty
    if isinstance(comments, list):  # Convert list to dict if necessary
        comments = {str(i): comment for i, comment in enumerate(comments)}

    # Generate a new comment ID
    if comments:
        try:
            last_id = max(map(int, comments.keys()))  # Find the highest numeric key
        except ValueError:
            last_id = 0  # Handle cases where keys are not numeric
        comment_id = str(last_id + 1)  # Increment the ID
    else:
        comment_id = "1"  # Start with "1" if no comments exist

    # Add the new comment
    comments[comment_id] = comment

    # Update the comments in the database
    put_response = requests.put(f"{database_url}/blogs/{blog_id}/comments.json", json=comments)
    if put_response.status_code != 200:
        return jsonify({"error": "Failed to update comments in the database."}), 500

    # Return success response
    return jsonify({"message": "Comment added successfully!", "comment_id": comment_id}), 200





def get_commentdetails(blog_id, comment_id):
    url = f"{database_url}/blogs/{blog_id}/comments/{comment_id}.json"
    response = requests.get(url)
    if response.status_code == 200:
        comment = response.json() 
        if comment:
            return comment
        else:
            return None 
    else:
        return None



@app.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    email = data.get('email')
    password =password = hash_password(data['password'])
    users = requests.get(f"{database_url}/users.json").json() or {}
    user = next((u for u in users.values() if u['email'] == email and u['password'] == password), None)
    if user:
        session_token = generate_session_token()
        requests.post(f"{database_url}/sessions.json", json={"email": email, "sessionToken": session_token})
        session[session_token] = {'email': email}
        session_store[session_token] = {'email': email}
        response = make_response(jsonify({'message': 'Login successful', 'sessionToken': session_token, 'email': email}))
        response.set_cookie('sessionToken', session_token, httponly=True, secure=True)
        return response
    else:
        return jsonify({'error': 'Invalid email or password'}), 401


@app.route('/check_session', methods=['GET'])
def check_session():
    session_token = request.cookies.get('sessionToken')
    if not session_token:
        return jsonify({'error': 'Session expired or not valid'}), 403

    user_data = session[session_token].get('email')

    if user_data:
        return jsonify({'email': user_data})

    return jsonify({'error': 'Session expired or invalid'}), 403

@app.route('/blogs/<blog_id>/comments', methods=['GET'])
def get_all_comments(blog_id):
    response = requests.get(f"{database_url}/blogs/{blog_id}/comments.json")
    if response.status_code != 200:
        return jsonify({"error": "Failed to fetch comments."}), 500

    comments = response.json() or {}
    return jsonify({"comments": comments}), 200


@app.route('/logout', methods=['GET'])
def logout():
    session_token = request.cookies.get('sessionToken')
    if session_token in session:
        session.pop('session_token', None)
        response = jsonify({'message': 'Logout successful'})
        response.delete_cookie('sessionToken') 
        return response
    return jsonify({'error': 'No active session'}), 400

@app.route('/blogs/<blog_id>/comments/<comment_id>/replies', methods=['POST'])
def add_reply(blog_id, comment_id):
    data = request.get_json()

    # Extract the reply content and email from the request
    reply_content = data.get('content')
    email = data.get('email')

    # Validate required fields
    if not reply_content or not email:
        return jsonify({"error": "Reply content and email are required."}), 400

    # Get the comment by blog_id and comment_id (you should define this function)
    comment = get_commentdetails(blog_id, comment_id)
    if not comment:
        return jsonify({"error": "Comment not found."}), 404

    # Initialize replies as an empty list if it doesn't exist
    if 'replies' not in comment or not isinstance(comment['replies'], list):
        comment['replies'] = []

    # Create a new reply dictionary
    reply = {
        "id": len(comment['replies']) + 1,  # Generate a unique reply_id
        "content": reply_content,
        "email": email
    }

    # Append the new reply to the replies list
    comment['replies'].append(reply)

    # Update the comment in the database
    url = f"{database_url}/blogs/{blog_id}/comments/{comment_id}.json"
    response = requests.put(url, json=comment)

    # Handle response from the database
    if response.status_code == 200:
        return jsonify({"message": "Reply added successfully.", "reply": reply}), 200
    else:
        return jsonify({"error": "Failed to add reply."}), 500


@app.route('/blogs', methods=['POST'])
def post_blog():
    data = request.json
    session_token = request.cookies.get('sessionToken')
    email = session.get(session_token)['email']

    if not email:
        return jsonify({"error": "Unauthorized"}), 403

    blog = {"title": data['title'], "content": data['content'], "email": email}
    response = requests.post(f"{database_url}/blogs.json", json=blog)
    if response.ok:
        return jsonify({"message": "Blog posted successfully"}), 201
    return jsonify({"error": "Failed to post blog"}), 500

@app.route('/blogs/<blog_id>/comments/<comment_id>', methods=['GET'])
def get_comment(blog_id, comment_id):
    response = requests.get(f"{database_url}/blogs/{blog_id}/comments/{comment_id}.json")
    if response.status_code != 200:
        return jsonify({"error": "Failed to fetch the comment."}), 500

    comment = response.json()
    if not comment:
        return jsonify({"error": "Comment not found."}), 404

    return jsonify({"comment": comment}), 200


@app.route('/blogs', methods=['GET'])
def fetch_blogs():
    blogs = requests.get(f"{database_url}/blogs.json").json() or {}
    return jsonify(blogs), 200

@app.route('/blogs/<blog_id>', methods=['GET'])
def get_blog(blog_id):
    # Fetch the blog data from the database
    url = f"{database_url}/blogs/{blog_id}.json"
    response = requests.get(url)
    
    # Check if the blog exists
    if response.status_code != 200 or response.json() is None:
        return jsonify({"error": "Blog not found."}), 404
    
    blog_data = response.json()
    
    # Return the blog data
    return jsonify(blog_data), 200


@app.route('/blogs/<blog_id>', methods=['PUT'])
def edit_blog(blog_id):
    data = request.json
    session_token = request.cookies.get('sessionToken')
    email = session.get(session_token)['email']

    if not email:
        return jsonify({"error": "Unauthorized"}), 403

    blog = requests.get(f"{database_url}/blogs/{blog_id}.json").json()
    if not blog or blog['email'] != email:
        return jsonify({"error": "Permission denied"}), 403

    updated_blog = {"title": data['title'], "content": data['content'], "email": email}
    response = requests.put(f"{database_url}/blogs/{blog_id}.json", json=updated_blog)
    if response.ok:
        return jsonify({"message": "Blog updated successfully"}), 200
    return jsonify({"error": "Failed to update blog"}), 500

@app.route('/blogs/<blog_id>', methods=['DELETE'])
def delete_blog(blog_id):
    session_token = request.cookies.get('sessionToken')
    email = session.get(session_token)['email']

    if not email:
        return jsonify({"error": "Unauthorized"}), 403

    blog = requests.get(f"{database_url}/blogs/{blog_id}.json").json()
    if not blog or blog['email'] != email:
        return jsonify({"error": "Permission denied"}), 403

    response = requests.delete(f"{database_url}/blogs/{blog_id}.json")
    if response.ok:
        return jsonify({"message": "Blog deleted successfully"}), 200
    return jsonify({"error": "Failed to delete blog"}), 500

def get_email_from_session(session_token):
    sessions = requests.get(f"{database_url}/sessions.json").json() or {}
    session = next((s for s in sessions.values() if s['sessionToken'] == session_token), None)
    return session['email'] if session else None

@app.route('/blogs/<blog_id>/comments/<comment_id>', methods=['PUT'])
def edit_comment(blog_id, comment_id):
    data = request.get_json()
    
    # Extract the content and email from the incoming request
    content = data.get('content')
    session_token = request.cookies.get('sessionToken')
    email = session.get(session_token)['email']
    
    # Validate content and email
    if not content or not email:
        return jsonify({"error": "Content or email is missing."}), 400
    
    # Fetch the current comment from Firebase
    comment = get_commentdetails(blog_id, comment_id)
    if not comment:
        return jsonify({"error": "Comment not found."}), 404
    # Check if the logged-in user is the owner of the comment
    if comment.get('email') != email:
        return jsonify({"error": "Unauthorized access. You can only edit your own comment."}), 403

    # Update the content of the comment
    comment['content'] = content

    # Save the updated comment back to Firebase
    url = f"{database_url}/blogs/{blog_id}/comments/{comment_id}.json"
    response = requests.put(url, json=comment)
    
    if response.status_code == 200:
        return jsonify({"message": "Comment updated successfully."}), 200
    else:
        return jsonify({"error": "Failed to update comment."}), 500



@app.route('/blogs/<blog_id>/comments/<comment_id>', methods=['DELETE'])
def delete_comment(blog_id, comment_id):
    session_token = request.cookies.get('sessionToken')
    email = session.get(session_token)['email']

    if not email:
        return jsonify({"error": "Unauthorized"}), 403

    comment = get_commentdetails(blog_id, comment_id)
    if not comment or comment['email'] != email:
        return jsonify({"error": "Permission denied"}), 403

    url = f"{database_url}/blogs/{blog_id}/comments/{comment_id}.json"
    response = requests.delete(url)
    
    if response.ok:
        return jsonify({"message": "Comment deleted successfully"}), 200
    return jsonify({"error": "Failed to delete comment"}), 500

@app.route('/blogs/<blog_id>/comments/<comment_id>/replies/<int:reply_id>', methods=['DELETE'])
def delete_reply(blog_id, comment_id, reply_id):
    # Get the session token from cookies
    session_token = request.cookies.get('sessionToken')
    email = session.get(session_token)['email']

    # Check if the user is authenticated
    if not email:
        return jsonify({"error": "Unauthorized"}), 403

    # Fetch the comment from the database
    comment = get_commentdetails(blog_id, comment_id)
    if not comment:
        return jsonify({"error": "Comment not found."}), 404

    # Get the replies list from the comment
    replies = comment.get('replies', [])

    # Validate the reply ID
    if reply_id < 1 or reply_id > len(replies):
        return jsonify({"error": "Reply not found."}), 404

    # Find the reply by index (adjust for 0-based indexing)
    reply_index = reply_id - 1
    reply = replies[reply_index]

    # Check if the reply belongs to the authenticated user
    if reply['email'] != email:
        return jsonify({"error": "Unauthorized access. You can only delete your own reply."}), 403

    # Delete the reply from the replies list
    del replies[reply_index]

    # Update the replies in the comment
    comment['replies'] = replies

    # Update the comment in the database
    url = f"{database_url}/blogs/{blog_id}/comments/{comment_id}.json"
    response = requests.put(url, json=comment)

    # Return the appropriate response based on the database operation result
    if response.status_code == 200:
        return jsonify({"message": "Reply deleted successfully."}), 200
    else:
        return jsonify({"error": "Failed to delete reply."}), 500

@app.route('/blogs/<blog_id>/comments/<comment_id>/replies/<int:reply_id>', methods=['PUT'])
def edit_reply(blog_id, comment_id, reply_id):
    # Parse the JSON payload
    data = request.get_json()
    reply_content = data.get('content')

    # Get the session token from cookies
    session_token = request.cookies.get('sessionToken')

    # Validate the session and retrieve the user's email
    if not session_token or session_token not in session:
        return jsonify({"error": "Unauthorized. Please log in."}), 403
    email =session.get(session_token)['email']

    # Validate the reply content
    if not reply_content or reply_content.strip() == "":
        return jsonify({"error": "Reply content cannot be empty."}), 400

    # Fetch the comment from the database
    comment = get_commentdetails(blog_id, comment_id)
    if not comment:
        return jsonify({"error": "Comment not found."}), 404

    # Get the replies list
    replies = comment.get('replies', [])
    if not isinstance(replies, list):
        return jsonify({"error": "Invalid data format for replies."}), 500

    # Find the reply by its ID
    reply = next((r for r in replies if r.get('id') == reply_id), None)
    if not reply:
        return jsonify({"error": "Reply not found."}), 404

    # Check if the reply belongs to the authenticated user
    if reply.get('email') != email:
        return jsonify({"error": "Unauthorized access. You can only edit your own reply."}), 403

    # Update the reply content
    reply['content'] = reply_content

    # Update the comment in Firebase
    url = f"{database_url}/blogs/{blog_id}/comments/{comment_id}.json"
    response = requests.put(url, json=comment)

    # Handle the response from Firebase
    if response.status_code == 200:
        return jsonify({"message": "Reply updated successfully."}), 200
    else:
        return jsonify({"error": "Failed to update reply."}), 500

@app.route('/blogs/<blog_id>/comments/<comment_id>/replies', methods=['GET'])
def get_replies(blog_id, comment_id):
    # Get the session token from cookies
    session_token = request.cookies.get('sessionToken')

    # Validate the session
    if not session_token or session_token not in session:
        return jsonify({"error": "Unauthorized. Please log in."}), 403

    # Fetch the comment from the database
    comment = get_commentdetails(blog_id, comment_id)
    if not comment:
        return jsonify({"error": "Comment not found."}), 404

    # Get the replies list
    replies = comment.get('replies', [])
    if not isinstance(replies, list):
        return jsonify({"error": "Invalid data format for replies."}), 500

    # Return the replies as JSON
    return jsonify({"replies": replies}), 200


def extract_text_from_pdf(pdf_file):
    text = ""
    with pdfplumber.open(io.BytesIO(pdf_file.read())) as pdf:
        for page in pdf.pages:
            text += page.extract_text() + "\n"
    return text
    
def extract_values(text):
    values = OrderedDict([
            ("Haemoglobin", 0),
            ("Total RBC Count", 0),
            ("Packed Cell Volume / Hematocrit", 0),
            ("MCV", 0),
            ("MCH", 0),
            ("MCHC", 0),
            ("RDW", 0),
            ("Total Leucocytes Count", 0),
            ("Neutrophils", 0),
            ("Lymphocytes", 0),
            ("Eosinophils", 0),
            ("Monocytes", 0),
            ("Basophils", 0),
            ("Absolute Neutrophil Count", 0),
            ("Absolute Lymphocyte Count", 0),
            ("Absolute Eosinophil Count", 0),
            ("Absolute Monocyte Count", 0),
            ("Platelet Count", 0),
            ("Erythrocyte Sedimentation Rate", 0),
            ("Fasting Plasma Glucose", 0),
            ("Glycated Hemoglobin", 0),
            ("Triglycerides", 0),
            ("Total Cholesterol", 0),
            ("LDL Cholesterol", 0),
            ("HDL Cholesterol", 0),
            ("VLDL Cholesterol", 0),
            ("Total Cholesterol / HDL Cholesterol Ratio", 0),
            ("LDL Cholesterol / HDL Cholesterol Ratio", 0),
            ("Total Bilirubin", 0),
            ("Direct Bilirubin", 0),
            ("Indirect Bilirubin", 0),
            ("SGPT/ALT", 0),
            ("SGOT/AST", 0),
            ("Alkaline Phosphatase", 0),
            ("Total Protein", 0),
            ("Albumin", 0),
            ("Globulin", 0),
            ("Protein A/G Ratio", 0),
            ("Gamma Glutamyl Transferase", 0),
            ("Creatinine", 0),
            ("e-GFR (Glomerular Filtration Rate)", 0),
            ("Urea", 0),
            ("Blood Urea Nitrogen", 0),
            ("Uric Acid", 0),
            ("T3 Total", 0),
            ("T4 Total", 0),
            ("TSH Ultrasensitive", 0),
            ("Vitamin B12", 0),
            ("Vitamin D Total (D2 + D3)", 0),
            ("Iron", 0),
            ("Total Iron Binding Capacity", 0),
            ("Transferrin Saturation", 0)
        ])
    patterns = {
    "Haemoglobin": r"\s*(.*?HEMOGLOBIN[^0-9\n]*|.*?Haemoglobin[^0-9\n]*|.*?Hgb[^0-9\n]*)(\d{1,7}(?:,\d{3})*(?:\.\d+)?)\s*.*?\s*.?.?g.?.?.?/.?d.?l",
    "Total RBC Count": r"\s*(.*?\bR.?B.?C\b.?count[^0-9\n]*|.*?\bR.?B.?C[^0-9\n]*)(\d{1,7}(?:,\d{3})*(?:\.\d+)?)\s*.*?\s*(/.?cu.?mm|.?/.?l)",
    "Packed Cell Volume / Hematocrit": r"\s*(.*?Packed Cell Volume[^0-9\n]*|.*?Hematocrit[^0-9\n]*|.*?\bP.?C.?V[^0-9\n]*|.*?\bH.?c.?t[^0-9\n]*)(\d{1,7}(?:,\d{3})*(?:\.\d+)?)\s*.*?\s*%",
    "MCV": r"\s*(\bM.?C.?V\b[^0-9\n]*|.*?Mean Corpuscular Volume[^0-9\n]*)(\d{1,7}(?:,\d{3})*(?:\.\d+)?)\s*.*?\s*f.?l",
    "MCH": r"\s*(\bMCH[^0-9\n]*|.*?Mean Corpuscular Hemoglobin[^0-9\n]*)(\d{1,7}(?:,\d{3})*(?:\.\d+)?)\s*.*?\s*p.?g",
    "MCHC": r"\s*(\bMCHC[^0-9\n]*|.*?Mean Corpuscular Hemoglobin Concentration[^0-9\n]*)(\d{1,7}(?:,\d{3})*(?:\.\d+)?)\s*.*?\s*.?.?g.?.?.?/.?d.?l",
    "RDW": r"\s*(\bR.?D.?W[^0-9\n]*|.*?Red Cell Distribution Width[^0-9\n]*)(\d{1,7}(?:,\d{3})*(?:\.\d+)?)\s*.*?\s*%",
    "Total Leucocytes Count": r"\s*(.*?Total Leucocytes Count[^0-9\n]*|.*?TLC[^0-9\n]*|\bWBC[^0-9\n]*)(\d{1,7}(?:,\d{3})*(?:\.\d+)?)\s*.*?\s*(/.?cu.?mm|/.?µ.?l)",
    "Neutrophils": r"\s*(Neutrophils[^0-9\n]*)(\d{1,7}(?:,\d{3})*(?:\.\d+)?)\s*.*?\s*%",
    "Lymphocytes": r"\s*(Lymphocytes[^0-9\n]*)(\d{1,7}(?:,\d{3})*(?:\.\d+)?)\s*.*?\s*%",
    "Eosinophils": r"\s*(Eosinophils[^0-9\n]*)(\d{1,7}(?:,\d{3})*(?:\.\d+)?)\s*.*?\s*%",
    "Monocytes": r"\s*(Monocytes[^0-9\n]*)(\d{1,7}(?:,\d{3})*(?:\.\d+)?)s*.*?\s*%",
    "Basophils": r"\s*(Basophils[^0-9\n]*)(\d{1,7}(?:,\d{3})*(?:\.\d+)?)\s*.*?\s*%",
    "Absolute Neutrophil Count": r".*?Neutrophil[^0-9\n]*(\d{1,7}(?:,\d{3})*(?:\.\d+)?)\s*.*?\s*(/.?cu.?mm|/.?.?.?l)",
    "Absolute Lymphocyte Count": r".*?Lymphocyte[^0-9\n]*(\d{1,7}(?:,\d{3})*(?:\.\d+)?)\s*.*?\s*(/.?cu.?mm|/.?.?.?l)",
    "Absolute Eosinophil Count": r".*?Eosinophil[^0-9\n]*(\d{1,7}(?:,\d{3})*(?:\.\d+)?)\s*.*?\s*(/.?cu.?mm|/.?.?.?l)",
    "Absolute Monocyte Count": r".*?Monocyte[^0-9\n]*(\d{1,7}(?:,\d{3})*(?:\.\d+)?)\s*.*?\s*(/.?cu.?mm|/.?.?.?l)",
    "Platelet Count": r"\s*(Platelet Count[^0-9\n]*|PLT[^0-9\n]*)(\d{1,7}(?:,\d{3})*(?:\.\d+)?)\s*.*?\s*(/.?cu.?mm|/.?µ.?L)",
    "Erythrocyte Sedimentation Rate": r"\s*(.*?Erythrocyte sedimentation[^0-9\n]*|.*?Erythrocyte Sedimentation Rate[^0-9\n]*|\bE.?S.?R[^0-9\n]*)(\d{1,7}(?:,\d{3})*(?:\.\d+)?)\s*.*?\s*mm.*?",
    "Fasting Plasma Glucose": r"\s*(.*?Fasting Plasma Glucose[^0-9\n]*|.*?Fasting[^0-9\n]*|.*?Fasting Blood Glucose[^0-9\n]*|.*?\bFPG[^0-9\n]*)(\d{1,7}(?:,\d{3})*(?:\.\d+)?)\s*.*?\s*.?.?g.?.?.?/.?d.?l",
    "Glycated Hemoglobin": r"\s*(.*?Glycated Haemoglobin.*?HBA1C[^0-9\n]*|.*?Glycated Haemoglobin[^0-9\n]*|.*?Glycated Hemoglobin[^0-9\n]*|\bHbA1C[^0-9\n]*)(\d{1,7}(?:,\d{3})*(?:\.\d+)?)\s*.*?\s*%",
    "Triglycerides": r"\s*(.*?Triglycerides[^0-9\n]*|.*?TG[^0-9\n]*)(\d{1,7}(?:,\d{3})*(?:\.\d+)?)\s*.*?\s*.?.?g.?.?.?/.?d.?l",
    "Total Cholesterol": r"\s*(Total Cholesterol[^0-9\n]*|TC[^0-9\n]*)(\d{1,7}(?:,\d{3})*(?:\.\d+)?)\s*.*?\s*.?.?g.?.?.?/.?d.?l",
    "LDL Cholesterol": r"\s*(L.?D.?L Cholesterol[^0-9\n]*|\bL.?D.?L[^0-9\n]*)(\d{1,7}(?:,\d{3})*(?:\.\d+)?)\s*.*?\s*.?.?g.?.?.?/.?d.?l",
    "HDL Cholesterol": r"\s*(H.?D.?L Cholesterol[^0-9\n]*|\bH.?D.?L[^0-9\n]*)(\d{1,7}(?:,\d{3})*(?:\.\d+)?)\s*.*?\s*.?.?g.?.?.?/.?d.?l",
    "VLDL Cholesterol": r"\s*(V.?L.?D.?L Cholesterol[^0-9\n]*|\bV.?L.?D.?L[^0-9\n]*)(\d{1,7}(?:,\d{3})*(?:\.\d+)?)\s*.*?\s*.?.?g.?.?.?/.?d.?l",
    "Total Cholesterol / HDL Cholesterol Ratio": r"\s*(.*?Total Cholesterol.?/.?HDL.*?|.*?Total Cholesterol.?/.?HDL Cholesterol Ratio.*?|.*?TC.?/.?HDL.?Ratio.*?|.*?CHOL.?/.?HDL\b.*?|.*?CHO.?/.?HDL\b.*?)\s*[:\-]?\s*(\d{1,7}(,\d{3})*(\.\d+)?)\s*",
    "LDL Cholesterol / HDL Cholesterol Ratio": r"\s*(.*?L.?D.?L.?/.?H.?D.?L.*?|.*?L.?D.?L.?/.?H.?D.?L Cholesterol Ratio.*?|.*?LDL Cholesterol.?/.?HDL Cholesterol Ratio.*?|.*?LDL.?/.?HDL Ratio.*?)\s*[:\-]?\s*(\d{1,7}(,\d{3})*(\.\d+)?)\s*",
    "Total Bilirubin": r"\s*(.*?Total.?Bilirubin[^0-9\n]*|.*?BILIRUBIN.*?Total[^0-9\n]*|.*?BIL-T[^0-9\n]*)(\d{1,7}(?:,\d{3})*(?:\.\d+)?)\s*.*?\s*.?.?g.?.?.?/.?d.?l",
    "Direct Bilirubin": r"\s*(.*?Direct.?Bilirubin[^0-9\n]*|.*?BILIRUBIN.*?direct[^0-9\n]*|.*?BIL-D[^0-9\n]*)(\d{1,7}(?:,\d{3})*(?:\.\d+)?)\s*.*?\s*.?.?g.?.?.?/.?d.?l",
    "Indirect Bilirubin": r"\s*(.*?Indirect.?Bilirubin[^0-9\n]*|.*?BILIRUBIN.*?indirect[^0-9\n]*|.*?BIL-I[^0-9\n]*)(\d{1,7}(?:,\d{3})*(?:\.\d+)?)\s*.*?\s*.?.?g.?.?.?/.?d.?l",
    "SGPT/ALT": r"\s*(.*?ALANINE AMINOTRANSFERASE[^0-9\n]*|\bS.?G.?P.?T.?/.?A.?L.?T[^0-9\n]*|\bS.?G.?P.?T[^0-9\n]*|\bA.?L.?T[^0-9\n]*)(\d{1,7}(?:,\d{3})*(?:\.\d+)?)\s*.*?\s*u.?/.?l",
    "SGOT/AST": r"\s*(.*?ASPARTATE AMINOTRANSFERASE[^0-9\n]*|\bS.?G.?O.?T.?/.?A.?S.?T[^0-9\n]*|\bS.?G.?O.?T[^0-9\n]*)(\d{1,7}(?:,\d{3})*(?:\.\d+)?)\s*.*?\s*u.?/.?l",
    "Alkaline Phosphatase": r"\s*(.*?Alkaline[^0-9\n]*|.*?Alkaline Phosphatase[^0-9\n]*|ALP[^0-9\n]*)(\d{1,7}(?:,\d{3})*(?:\.\d+)?)\s*.*?\s*u.?/.?l",
    "Total Protein": r"\s*(.*?Total Protein[^0-9\n]*|.*?Protein[^0-9\n]*|PROTEIN, TOTAL[^0-9\n]*|TP[^0-9\n]*)(\d{1,7}(?:,\d{3})*(?:\.\d+)?)\s*.*?\s*.?.?g.?.?.?/.?d.?l",
    "Albumin": r"\s*(Albumin[^0-9\n]*|ALB[^0-9\n]*)(\d{1,7}(?:,\d{3})*(?:\.\d+)?)\s*.*?\s*.?.?g.?.?.?/.?d.?l",
    "Globulin": r"\s*(.*?Globulin[^0-9\n]*)(\d{1,7}(?:,\d{3})*(?:\.\d+)?)\s*.*?\s*.?.?g.?.?.?/.?d.?l",
    "Protein A/G Ratio": r"\s*(Protein A/G Ratio|A/G Ratio)\s*[:\-]?\s*(\d{1,7}(,\d{3})*(\.\d+)?)\s*",
    "Gamma Glutamyl Transferase": r"\s*(Gamma Glutamyl Transferase[^0-9\n]*|GAMMA GLUTAMYL[^0-9\n]*|GAMMA GLUTAMYL TRANSPEPTIDASE[^0-9\n]*|G.?G.?T[^0-9\n]*)(\d{1,7}(?:,\d{3})*(?:\.\d+)?)\s*.*?\s*u.?/.?l",
    "Creatinine": r"\s*(Creatinine[^0-9\n]*|Cr[^0-9\n]*)(\d{1,7}(?:,\d{3})*(?:\.\d+)?)\s*.*?\s*.?.?g.?.?.?/.?d.?l",
    "e-GFR (Glomerular Filtration Rate)": r"\s*(\be-GFR\b.*?|.*?\beGFR\b.*?|.*?eGFR\b.*?|.*?GFR.*?|Glomerular Filtration Rate.*?)\s*[:\-]?\s*(\d{1,7}(,\d{3})*(\.\d+)?)\s*",
    "Urea": r"\s*(Urea[^0-9\n]*)(\d{1,7}(?:,\d{3})*(?:\.\d+)?)\s*.*?\s*.?.?g.?.?.?/.?d.?l",
    "Blood Urea Nitrogen": r"\s*(Blood Urea Nitrogen[^0-9\n]*|.*?UREA NITROGEN[^0-9\n]*|.*?BUN[^0-9\n]*)(\d{1,7}(?:,\d{3})*(?:\.\d+)?)\s*.*?\s*.?.?g.?.?.?/.?d.?l",
    "Uric Acid": r"\s*(Uric Acid[^0-9\n]*|UA[^0-9\n]*)(\d{1,7}(?:,\d{3})*(?:\.\d+)?)\s*.*?\s*.?.?g.?.?.?/.?d.?l",
    "T3 Total": r"\s*(.*?T.?3[^0-9\n]*|.*?T3.*?Total[^0-9\n]*|Triiodothyronine[^0-9\n]*)(\d{1,7}(?:,\d{3})*(?:\.\d+)?)\s*.*?\s*/ml",
    "T4 Total": r"\s*(.*?T.?4[^0-9\n]*|.*?T4.*?Total[^0-9\n]*|Thyroxine[^0-9\n]*)(\d{1,7}(?:,\d{3})*(?:\.\d+)?)\s*.*?\s*/dl",
    "TSH Ultrasensitive": r"\s*(THYROID STIMULATING HORMONE[^0-9\n]*|\bT.?S.?H[^0-9\n]*|Ultrasensitive TSH[^0-9\n]*|.*?T.?S.?H[^0-9\n]*)(\d{1,7}(?:,\d{3})*(?:\.\d+)?)\s*.*?\s*/ml",
    "Vitamin B12": r"\s*(Vitamin B.?12[^0-9\n]*|\bB.?12[^0-9\n]*)(\d{1,7}(?:,\d{3})*(?:\.\d+)?)\s*.*?\s*/ml",
    "Vitamin D Total (D2 + D3)": r"\s*(D2\s*\+?\s*D3[^0-9\n]*|.*?Vitamin D.?[^0-9\n]*|.*?Vitamin D\b.*?D2\s*\+?\s*D3[^0-9\n]*)(\d{1,7}(?:,\d{3})*(?:\.\d+)?)\s*.*?\s*g.?/.?ml",
    "Iron": r"\s*(Iron[^0-9\n]*)(\d{1,7}(?:,\d{3})*(?:\.\d+)?)\s*.*?\s*/dl",
    "Total Iron Binding Capacity": r"\s*(.*?Total Iron Binding Capacity[^0-9\n]*|.*?T.?I.?B.?C[^0-9\n]*)(\d{1,7}(?:,\d{3})*(?:\.\d+)?)\s*.*?\s*/dl",
    "Transferrin Saturation": r"\s*(.*?Transferrin Saturation[^0-9\n]*|.*?% OF SATURATION[^0-9\n]*|.*?Transferin[^0-9\n]*)(\d{1,7}(?:,\d{3})*(?:\.\d+)?)\s*.*?\s*%",
    }

    for test, pattern in patterns.items():
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            try:
                
                group1_value = match.group(1).replace(',', '')
                
                group2_value = match.group(2) if match.group(2) is not None else None
                if group2_value is None:
                    values[test] = float(group1_value)
                else:
                    values[test] = float(group2_value.replace(',', ''))
        
            except IndexError:
                values[test]=float(match.group(1).replace(',', ''))
            except ValueError:
                values[test] =float(match.group(1).replace(',', ''))

            finally:
                pass
    if values["Protein A/G Ratio"] == 0:
        if values["Globulin"] != 0:
            values["Protein A/G Ratio"] = round(values["Albumin"] / values["Globulin"], 2)
        else:
            values["Protein A/G Ratio"] = 0

    if values["LDL Cholesterol / HDL Cholesterol Ratio"] == 0:
        if values["HDL Cholesterol"] != 0:
            values["LDL Cholesterol / HDL Cholesterol Ratio"] = round(values["LDL Cholesterol"] / values["HDL Cholesterol"], 2)
        else:
            values["LDL Cholesterol / HDL Cholesterol Ratio"] = 0

    if values["Total Cholesterol / HDL Cholesterol Ratio"] == 0:
        if values["HDL Cholesterol"] != 0:
            values["Total Cholesterol / HDL Cholesterol Ratio"] = round(values["Total Cholesterol"] / values["HDL Cholesterol"], 2)
        else:
            values["Total Cholesterol / HDL Cholesterol Ratio"] = 0

    return values

def give_health_advice(values):
        advice = []
    # Haemoglobin (range: 13.0-17.0 g/dL)
        if values["Haemoglobin"] < 13.0:
            advice.append("""<div>
    <h2>Low Hemoglobin</h2>
    <div>
        <h3>Root Cause:</h3>
        <ul>
            <li><strong>Iron Deficiency:</strong> Lack of sufficient iron for red blood cell production.</li>
            <li><strong>Vitamin B12 or Folate Deficiency:</strong> Both are essential for red blood cell formation and maturation.</li>
            <li><strong>Blood Loss:</strong> Heavy menstruation, gastrointestinal bleeding (e.g., ulcers, hemorrhoids), or surgery.</li>
            <li><strong>Chronic Diseases:</strong> Kidney disease, chronic infections, or inflammation.</li>
            <li><strong>Genetic Conditions:</strong> Thalassemia, sickle cell disease.</li>
            <li><strong>Poor Diet:</strong> Inadequate intake of nutrients that support hemoglobin production.</li>
        </ul>
    </div>
    <div>
        <h3>Tips:</h3>
        <ul>
            <li>Increase <strong>Iron Intake:</strong> Iron is critical for hemoglobin production. Iron supplements may be prescribed, but always follow the guidance of a healthcare provider.</li>
            <li>Address <strong>Vitamin B12</strong> and <strong>Folate Deficiency:</strong> If low levels are detected, supplements or dietary changes can help.</li>
            <li>Treat Underlying Conditions: If blood loss or a chronic disease is the cause, address the root cause (e.g., treating ulcers, managing kidney disease).</li>
            <li>Avoid <strong>Tea/Coffee with Meals:</strong> Tannins in tea and coffee can inhibit iron absorption.</li>
            <li>Consult a Doctor for Diagnosis: Persistent symptoms may require additional tests to diagnose specific causes of anemia.</li>
        </ul>
    </div>
    <div>
        <h3>Foods to Eat:</h3>
        <ul>
            <li><strong>Iron-Rich Foods</strong> (heme iron from animal sources and non-heme iron from plant sources):
                <ul>
                    <li>Heme Iron: Red meat (beef, lamb), poultry (chicken, turkey), pork, fish, shellfish (clams, oysters, mussels).</li>
                    <li>Non-Heme Iron: Spinach, lentils, beans, tofu, quinoa, chickpeas, fortified cereals, pumpkin seeds, and fortified plant-based milk.</li>
                </ul>
            </li>
            <li><strong>Vitamin B12-Rich Foods:</strong> Eggs, dairy products (milk, yogurt, cheese), meat, fish (salmon, tuna), shellfish, fortified cereals.</li>
            <li><strong>Folate-Rich Foods:</strong> Leafy greens (spinach, kale), citrus fruits, avocado, beans, peas, lentils, fortified cereals, and pasta.</li>
            <li><strong>Vitamin C-Rich Foods</strong> (to enhance iron absorption): Citrus fruits (oranges, grapefruits), strawberries, bell peppers, broccoli, tomatoes, kiwi, and Brussels sprouts.</li>
        </ul>
    </div>
    <div>
        <h3>Example Meal Plan to Boost Hemoglobin:</h3>
        <ul>
            <li><strong>Breakfast:</strong> Fortified cereal with almond milk, topped with fresh strawberries (rich in vitamin C) and a boiled egg.</li>
            <li><strong>Lunch:</strong> Spinach and lentil salad with citrus dressing (for vitamin C absorption).</li>
            <li><strong>Snack:</strong> A handful of pumpkin seeds and a citrus fruit (orange or kiwi).</li>
            <li><strong>Dinner:</strong> Grilled chicken with quinoa and steamed broccoli (rich in iron and vitamin C).</li>
        </ul>
    </div>
    <p>By focusing on these dietary changes, you can support your body’s ability to increase hemoglobin levels and improve overall health. However, if symptoms persist, it’s crucial to consult with a healthcare provider for further evaluation and potential treatment.</p>
</div>
""")
        elif values["Haemoglobin"] > 17.0:
            advice.append("""<div>
    <h2>High Hemoglobin (Polycythemia)</h2>
    <div>
        <h3>Root Cause:</h3>
        <ul>
            <li><strong>Dehydration:</strong> When you're dehydrated, the plasma (liquid) component of your blood decreases, making the concentration of red blood cells appear higher.</li>
            <li><strong>Chronic Lung or Heart Disease:</strong> Conditions like chronic obstructive pulmonary disease (COPD) or congenital heart defects can cause low oxygen levels in the blood, leading the body to produce more red blood cells to compensate.</li>
            <li><strong>Living at High Altitudes:</strong> At higher altitudes, the oxygen level in the air is lower, and the body compensates by producing more red blood cells.</li>
            <li><strong>Polycythemia Vera:</strong> A rare bone marrow disorder where the body makes too many red blood cells, often without a known cause.</li>
            <li><strong>Smoking:</strong> Smoking can lead to lower oxygen levels in the blood, prompting the body to produce more red blood cells.</li>
            <li><strong>Tumors or Hormonal Imbalances:</strong> Rarely, some tumors or conditions affecting the kidneys (e.g., renal cell carcinoma) can increase erythropoietin production, leading to more red blood cells being produced.</li>
        </ul>
    </div>
    <div>
        <h3>Tips:</h3>
        <ul>
            <li><strong>Hydrate Well:</strong> Dehydration is a common cause of high hemoglobin levels. Make sure to drink plenty of water to stay hydrated and maintain proper blood volume.</li>
            <li><strong>Monitor for Underlying Conditions:</strong> If you have chronic lung or heart disease, follow your treatment plan. If polycythemia vera is suspected, your healthcare provider will guide you through diagnostic tests and treatments.</li>
            <li><strong>Quit Smoking:</strong> Quitting smoking can help reduce the body's need for extra red blood cell production and improve overall cardiovascular and lung health.</li>
            <li><strong>Regular Check-Ups:</strong> If you live at high altitudes or have chronic conditions, regular monitoring of hemoglobin and other blood parameters will help manage your health effectively.</li>
            <li><strong>Consult a Doctor:</strong> If your hemoglobin is significantly high and symptoms like headaches, dizziness, or a reddened complexion occur, see a healthcare professional to rule out polycythemia vera or other blood disorders.</li>
        </ul>
    </div>
    <div>
        <h3>Foods to Eat:</h3>
        <ul>
            <li><strong>Iron-Rich Foods:</strong> While high hemoglobin can sometimes be linked to excess iron, focus on eating a balanced diet and avoid iron-rich supplements unless advised by your doctor.</li>
            <li><strong>Foods to Support Hydration:</strong>
                <ul>
                    <li><strong>Water-Rich Foods:</strong> Cucumbers, watermelon, celery, oranges, and strawberries can help keep you hydrated.</li>
                    <li><strong>Electrolyte-Rich Foods:</strong> Include potassium-rich foods like bananas, sweet potatoes, and leafy greens to maintain fluid balance and hydration.</li>
                </ul>
            </li>
            <li><strong>Avoid Excessive Iron:</strong> Avoid excessive consumption of iron-rich foods or supplements unless prescribed, as the body may already have sufficient iron.</li>
        </ul>
    </div>
    <div>
        <h3>Example Meal Plan for High Hemoglobin (Polycythemia):</h3>
        <ul>
            <li><strong>Breakfast:</strong> Oatmeal with almond milk and fresh fruit (e.g., strawberries and blueberries) for antioxidants, paired with a glass of water.</li>
            <li><strong>Lunch:</strong> A salad with mixed greens (for hydration), cucumber, and tomato, with a light dressing. Add a source of lean protein (e.g., chicken or tofu) for balance.</li>
            <li><strong>Snack:</strong> A water-based smoothie with hydrating fruits like watermelon or cucumber and a few spinach leaves for additional hydration.</li>
            <li><strong>Dinner:</strong> Grilled salmon (rich in healthy fats but not iron-loaded) with steamed vegetables like broccoli and zucchini. Drink plenty of water during meals.</li>
        </ul>
    </div>
    <p>Note: While dietary adjustments can help manage some causes of high hemoglobin, underlying medical conditions (e.g., polycythemia vera or chronic lung disease) require specialized care and management by a healthcare provider.</p>
</div>
""")

    # Total RBC Count (range: 4.5-5.5 million cells/μL)

        if values["Total RBC Count"] < 4.5:
            advice.append("""
<div>
    <h2>Low Total RBC Count (Erythropenia)</h2>
    <div>
        <h3>Root Cause:</h3>
        <ul>
            <li><strong>Anemia:</strong> Low RBC count is often caused by anemia, which can result from iron, vitamin B12, or folate deficiencies, chronic disease, or blood loss.</li>
            <li><strong>Nutritional Deficiencies:</strong> Lack of iron, vitamin B12, or folate can impair RBC production.</li>
            <li><strong>Chronic Inflammatory Conditions:</strong> Chronic infections, autoimmune diseases, or kidney disease can suppress RBC production.</li>
            <li><strong>Bone Marrow Disorders:</strong> Conditions like aplastic anemia or leukemia affect the bone marrow’s ability to produce RBCs.</li>
            <li><strong>Excessive Blood Loss:</strong> Surgery, gastrointestinal bleeding (e.g., ulcers), or heavy menstrual periods.</li>
            <li><strong>Kidney Disease:</strong> Since the kidneys produce erythropoietin (a hormone that stimulates RBC production), kidney dysfunction can result in low RBC count.</li>
            <li><strong>Genetic Disorders:</strong> Conditions like thalassemia, sickle cell anemia, and other hereditary disorders can lead to low RBC production.</li>
        </ul>
    </div>
    <div>
        <h3>Tips:</h3>
        <ul>
            <li><strong>Increase Iron Intake:</strong> Iron is crucial for RBC production. Consider iron-rich foods or supplements as advised by your doctor.</li>
            <li><strong>Supplement with Vitamin B12 and Folate:</strong> If these deficiencies are detected, your doctor may recommend supplements to support RBC production.</li>
            <li><strong>Treat the Underlying Cause:</strong> Addressing the root cause is essential (e.g., treating ulcers, managing kidney disease).</li>
            <li><strong>Monitor for Symptoms of Anemia:</strong> Symptoms like fatigue, pale skin, shortness of breath, and dizziness should be discussed with your healthcare provider.</li>
        </ul>
    </div>
    <div>
        <h3>Foods to Eat:</h3>
        <ul>
            <li><strong>Iron-Rich Foods:</strong> Red meat, poultry, fish, liver, spinach, lentils, chickpeas, beans, quinoa, tofu, fortified cereals, pumpkin seeds.</li>
            <li><strong>Vitamin B12-Rich Foods:</strong> Eggs, dairy, meat, fish, shellfish, fortified cereals.</li>
            <li><strong>Folate-Rich Foods:</strong> Leafy greens, avocado, beans, lentils, citrus fruits, fortified cereals.</li>
            <li><strong>Vitamin C-Rich Foods:</strong> Citrus fruits, bell peppers, broccoli, strawberries, kiwi, and tomatoes.</li>
        </ul>
    </div>
    <div>
        <h3>Example Meal Plan:</h3>
        <ul>
            <li><strong>Breakfast:</strong> Fortified cereal with almond milk, fresh strawberries, and a boiled egg.</li>
            <li><strong>Lunch:</strong> Spinach and lentil salad with citrus dressing to enhance iron absorption.</li>
            <li><strong>Snack:</strong> A handful of pumpkin seeds and an orange.</li>
            <li><strong>Dinner:</strong> Grilled chicken with quinoa and steamed broccoli.</li>
        </ul>
    </div>
</div>
""")
        elif values["Total RBC Count"] > 5.5:
            advice.append("""
<div>
    <h2>High Total RBC Count (Polycythemia)</h2>
    <div>
        <h3>Root Cause:</h3>
        <ul>
            <li><strong>Dehydration:</strong> When the body is dehydrated, plasma (the liquid part of blood) decreases, making the concentration of RBCs appear higher.</li>
            <li><strong>Polycythemia Vera:</strong> A rare blood disorder in which the bone marrow produces too many RBCs, often without an identifiable cause.</li>
            <li><strong>Chronic Low Oxygen Levels:</strong> Conditions like chronic lung disease, heart disease, or living at high altitudes can cause the body to compensate by producing more RBCs.</li>
            <li><strong>Smoking:</strong> Smoking reduces oxygen levels in the blood, which may lead the body to produce more RBCs.</li>
            <li><strong>Tumors:</strong> Certain tumors, especially kidney tumors, can secrete erythropoietin, leading to an elevated RBC count.</li>
        </ul>
    </div>
    <div>
        <h3>Tips:</h3>
        <ul>
            <li><strong>Hydrate Properly:</strong> Dehydration is a common cause of high RBC counts. Drink plenty of water throughout the day.</li>
            <li><strong>Quit Smoking:</strong> Smoking can decrease oxygen levels in the blood, prompting the body to produce more RBCs.</li>
            <li><strong>Follow Up with Your Doctor:</strong> High RBC counts should be evaluated further with necessary tests and treatments.</li>
            <li><strong>Avoid Excessive Iron:</strong> If diagnosed with polycythemia, reducing iron intake may be necessary.</li>
        </ul>
    </div>
    <div>
        <h3>Foods to Eat:</h3>
        <ul>
            <li><strong>Water-Rich Foods:</strong> Cucumbers, watermelon, celery, oranges, strawberries, and bell peppers.</li>
            <li><strong>Electrolyte-Rich Foods:</strong> Bananas, sweet potatoes, spinach, and avocados.</li>
            <li><strong>Antioxidant-Rich Foods:</strong> Berries, leafy greens, tomatoes, and nuts.</li>
            <li><strong>Low-Sodium Foods:</strong> Avoid excessive salt, which can contribute to dehydration.</li>
        </ul>
    </div>
    <div>
        <h3>Example Meal Plan:</h3>
        <ul>
            <li><strong>Breakfast:</strong> Watermelon smoothie with spinach and chia seeds.</li>
            <li><strong>Lunch:</strong> Grilled chicken salad with cucumber, mixed greens, and avocado.</li>
            <li><strong>Snack:</strong> Fresh strawberries and a handful of nuts.</li>
            <li><strong>Dinner:</strong> Baked salmon with roasted sweet potatoes and steamed asparagus.</li>
        </ul>
    </div>
</div>
""")


    # Packed Cell Volume / Hematocrit (range: 40-50%)
        if values["Packed Cell Volume / Hematocrit"] < 40:
            advice.append("""
<div>
    <h2>Low Packed Cell Volume (PCV) / Hematocrit (Anemia)</h2>
    <div>
        <h3>Root Cause:</h3>
        <ul>
            <li><strong>Iron Deficiency:</strong> Inadequate iron affects the production of hemoglobin, leading to a low hematocrit.</li>
            <li><strong>Vitamin B12 or Folate Deficiency:</strong> These vitamins are essential for the production and maturation of red blood cells. A deficiency can result in a low hematocrit.</li>
            <li><strong>Blood Loss:</strong> Chronic blood loss due to heavy menstruation, gastrointestinal bleeding (e.g., ulcers), or surgery can decrease the hematocrit.</li>
            <li><strong>Chronic Diseases:</strong> Kidney disease, cancer, and chronic inflammatory conditions can impair RBC production and cause a low hematocrit.</li>
            <li><strong>Bone Marrow Disorders:</strong> Aplastic anemia, leukemia, or other disorders affecting the bone marrow’s ability to produce RBCs can lead to a low hematocrit.</li>
            <li><strong>Hemorrhage:</strong> Sudden blood loss, such as from an injury or surgery, can cause a decrease in hematocrit.</li>
            <li><strong>Hydration Status:</strong> Overhydration can dilute blood, artificially lowering hematocrit levels.</li>
        </ul>
    </div>
    <div>
        <h3>Tips:</h3>
        <ul>
            <li><strong>Increase Iron Intake:</strong> Iron is essential for RBC production. If iron deficiency is the cause, consider taking iron supplements as prescribed by your doctor.</li>
            <li><strong>Supplement with Vitamin B12 and Folate:</strong> Deficiencies in these vitamins can contribute to low hematocrit. You may need supplements if your levels are low.</li>
            <li><strong>Treat the Underlying Cause:</strong> If blood loss or a chronic disease is the cause, treat the underlying condition (e.g., managing ulcers, controlling kidney disease).</li>
            <li><strong>Avoid Excessive Fluids:</strong> If low hematocrit is due to overhydration, limit your fluid intake and consult your doctor for advice on fluid balance.</li>
            <li><strong>Monitor for Symptoms:</strong> Symptoms like fatigue, dizziness, pale skin, or shortness of breath should be reported to your healthcare provider.</li>
        </ul>
    </div>
    <div>
        <h3>Foods to Eat:</h3>
        <ul>
            <li><strong>Iron-Rich Foods:</strong> Heme iron (animal sources): Red meat, poultry, fish, shellfish, and liver. Non-heme iron (plant-based): Lentils, beans, tofu, quinoa, spinach, pumpkin seeds, and fortified cereals.</li>
            <li><strong>Vitamin B12-Rich Foods:</strong> Eggs, dairy products, fish, poultry, and fortified cereals.</li>
            <li><strong>Folate-Rich Foods:</strong> Leafy greens, citrus fruits, beans, peas, lentils, and fortified cereals.</li>
            <li><strong>Vitamin C-Rich Foods:</strong> Citrus fruits, bell peppers, broccoli, strawberries, and tomatoes to enhance iron absorption.</li>
        </ul>
    </div>
    <div>
        <h3>Example Meal Plan for Low Hematocrit:</h3>
        <ul>
            <li><strong>Breakfast:</strong> Fortified cereal with almond milk, topped with fresh strawberries and a boiled egg.</li>
            <li><strong>Lunch:</strong> Spinach and lentil salad with citrus dressing to enhance iron absorption.</li>
            <li><strong>Snack:</strong> A handful of pumpkin seeds and an orange.</li>
            <li><strong>Dinner:</strong> Grilled chicken with quinoa and steamed broccoli.</li>
        </ul>
    </div>
</div>
""")
        elif values["Packed Cell Volume / Hematocrit"] > 50:
            advice.append("""
<div>
    <h2>High Packed Cell Volume (PCV) / Hematocrit</h2>
    <div>
        <h3>Root Cause:</h3>
        <ul>
            <li><strong>Dehydration:</strong> When the body is dehydrated, the plasma (liquid part of blood) decreases, leading to a relative increase in RBC concentration.</li>
            <li><strong>Polycythemia Vera:</strong> A bone marrow disorder where the body overproduces red blood cells, resulting in a high hematocrit.</li>
            <li><strong>Chronic Lung Disease (COPD):</strong> Low oxygen levels in the blood can stimulate the bone marrow to produce more RBCs to increase oxygen transport.</li>
            <li><strong>Living at High Altitudes:</strong> The body compensates for lower oxygen levels in the air by producing more RBCs.</li>
            <li><strong>Smoking:</strong> Smoking reduces oxygen in the blood, leading to an increase in RBC production.</li>
            <li><strong>Heart Disease:</strong> Some heart conditions that result in low oxygen levels can lead to a high hematocrit as the body attempts to compensate.</li>
            <li><strong>Tumors:</strong> Certain tumors, especially kidney tumors, can secrete erythropoietin (EPO), which stimulates RBC production.</li>
        </ul>
    </div>
    <div>
        <h3>Tips:</h3>
        <ul>
            <li><strong>Hydrate Properly:</strong> Dehydration is a common cause of high hematocrit. Drinking plenty of fluids can help reduce the concentration of RBCs in the blood.</li>
            <li><strong>Avoid Smoking:</strong> Smoking reduces the amount of oxygen in the blood, stimulating the production of more RBCs. Quitting smoking can help normalize hematocrit levels.</li>
            <li><strong>Manage Underlying Conditions:</strong> If high hematocrit is due to chronic lung or heart disease, follow your treatment plan.</li>
            <li><strong>Consult Your Doctor:</strong> High hematocrit can be a sign of serious conditions like polycythemia vera or chronic lung disease. It’s important to consult your healthcare provider for proper diagnosis and management.</li>
            <li><strong>Regular Monitoring:</strong> If you live at high altitudes, regular monitoring of hematocrit levels is necessary.</li>
        </ul>
    </div>
    <div>
        <h3>Foods to Eat:</h3>
        <ul>
            <li><strong>Hydrating Foods:</strong> Water-rich foods: Cucumbers, watermelon, celery, oranges, strawberries, bell peppers, and lettuce.</li>
            <li><strong>Electrolyte-Rich Foods:</strong> Bananas, sweet potatoes, spinach, and avocados.</li>
            <li><strong>Avoid Excessive Iron:</strong> Limit your intake of iron-rich foods unless advised otherwise, as high iron can exacerbate RBC production.</li>
            <li><strong>Anti-Inflammatory Foods:</strong> Foods rich in antioxidants and omega-3 fatty acids, like berries, nuts, and fatty fish.</li>
            <li><strong>Low-Sodium Foods:</strong> Avoid excess salt to prevent fluid retention.</li>
        </ul>
    </div>
    <div>
        <h3>Example Meal Plan for High Hematocrit:</h3>
        <ul>
            <li><strong>Breakfast:</strong> Oatmeal with fresh berries and chia seeds, paired with a large glass of water.</li>
            <li><strong>Lunch:</strong> Grilled chicken salad with cucumber, avocado, mixed greens, and light vinaigrette.</li>
            <li><strong>Snack:</strong> A handful of almonds and a glass of coconut water for hydration.</li>
            <li><strong>Dinner:</strong> Grilled salmon with steamed sweet potatoes and roasted vegetables.</li>
        </ul>
    </div>
</div>
""")


    # MCV (range: 83-101 fL)
        if values["MCV"] < 83:
            advice.append("""
<div>
    <h2>Low Mean Corpuscular Volume (MCV) / Microcytic Anemia</h2>
    <div>
        <h3>Root Cause:</h3>
        <ul>
            <li><strong>Iron Deficiency Anemia:</strong> Lack of iron affects hemoglobin production, leading to low MCV.</li>
            <li><strong>Chronic Blood Loss:</strong> Conditions like heavy menstruation, gastrointestinal bleeding, or surgery can cause iron deficiency and microcytic anemia.</li>
            <li><strong>Thalassemia:</strong> A genetic disorder causing abnormal hemoglobin production, leading to smaller red blood cells.</li>
            <li><strong>Sideroblastic Anemia:</strong> Bone marrow produces ringed sideroblasts due to ineffective iron utilization.</li>
            <li><strong>Lead Poisoning:</strong> Lead toxicity interferes with heme production, causing microcytic anemia.</li>
            <li><strong>Chronic Diseases:</strong> Chronic illnesses (e.g., inflammation) may impair RBC production, leading to low MCV.</li>
        </ul>
    </div>
    <div>
        <h3>Tips:</h3>
        <ul>
            <li><strong>Increase Iron Intake:</strong> Iron-rich foods or supplements may help (consult your doctor).</li>
            <li><strong>Address Underlying Causes:</strong> Manage or treat conditions causing blood loss.</li>
            <li><strong>Monitor for Thalassemia:</strong> If genetic causes are suspected, seek medical advice.</li>
            <li><strong>Check for Lead Exposure:</strong> Address the source of exposure and seek treatment if needed.</li>
            <li><strong>Ensure Adequate Vitamin C:</strong> Vitamin C enhances iron absorption, aiding in improving MCV.</li>
        </ul>
    </div>
    <div>
        <h3>Foods to Eat:</h3>
        <ul>
            <li><strong>Iron-Rich Foods:</strong> Heme iron: Red meat, poultry, liver, and fish. Non-heme iron: Lentils, beans, tofu, spinach, and fortified cereals.</li>
            <li><strong>Vitamin C-Rich Foods:</strong> Citrus fruits, bell peppers, strawberries, and broccoli to enhance iron absorption.</li>
            <li><strong>Folate-Rich Foods:</strong> Leafy greens, avocado, beans, lentils, and fortified cereals.</li>
            <li><strong>Vitamin B12-Rich Foods:</strong> Eggs, dairy, and fortified cereals for overall blood health.</li>
        </ul>
    </div>
    <div>
        <h3>Example Meal Plan for Low MCV:</h3>
        <ul>
            <li><strong>Breakfast:</strong> Fortified cereal with almond milk, topped with strawberries and a boiled egg.</li>
            <li><strong>Lunch:</strong> Spinach and lentil salad with a citrus dressing.</li>
            <li><strong>Snack:</strong> A handful of pumpkin seeds and an orange.</li>
            <li><strong>Dinner:</strong> Grilled chicken with quinoa and steamed broccoli.</li>
        </ul>
    </div>
</div>
""")
        elif values["MCV"] > 101:
            advice.append("""
<div>
    <h2>High Mean Corpuscular Volume (MCV) / Macrocytic Anemia</h2>
    <div>
        <h3>Root Cause:</h3>
        <ul>
            <li><strong>Vitamin B12 Deficiency:</strong> Impairs red blood cell maturation, resulting in larger cells (macrocytes).</li>
            <li><strong>Folate Deficiency:</strong> Affects RBC production, leading to larger cells.</li>
            <li><strong>Alcohol Abuse:</strong> Chronic alcohol use interferes with absorption of B12 and folate, causing macrocytic anemia.</li>
            <li><strong>Liver Disease:</strong> Liver disorders can alter RBC production and metabolism, increasing MCV.</li>
            <li><strong>Hypothyroidism:</strong> An underactive thyroid slows RBC production, leading to larger cells.</li>
            <li><strong>Medications:</strong> Drugs like chemotherapy agents or anticonvulsants may affect RBC production.</li>
            <li><strong>Bone Marrow Disorders:</strong> Conditions like myelodysplastic syndromes result in abnormal RBC production.</li>
        </ul>
    </div>
    <div>
        <h3>Tips:</h3>
        <ul>
            <li><strong>Increase Vitamin B12 and Folate Intake:</strong> Supplements or dietary changes may be needed.</li>
            <li><strong>Limit Alcohol Consumption:</strong> Alcohol can impair nutrient absorption, so reducing intake is important.</li>
            <li><strong>Manage Thyroid Health:</strong> Follow your doctor’s treatment plan to normalize thyroid function.</li>
            <li><strong>Monitor Medications:</strong> Consult your doctor if medications affect MCV, and discuss alternatives.</li>
            <li><strong>Treat Underlying Conditions:</strong> Proper medical care for liver disease or bone marrow disorders is crucial.</li>
        </ul>
    </div>
    <div>
        <h3>Foods to Eat:</h3>
        <ul>
            <li><strong>Vitamin B12-Rich Foods:</strong> Eggs, dairy, fish (salmon, tuna), poultry, shellfish, and fortified cereals.</li>
            <li><strong>Folate-Rich Foods:</strong> Leafy greens, beans, lentils, citrus fruits, and fortified cereals.</li>
            <li><strong>Iron-Rich Foods:</strong> Lean meat, beans, tofu, and fortified cereals for overall blood health.</li>
            <li><strong>Healthy Fats and Proteins:</strong> Foods like salmon, eggs, nuts, seeds, and avocados support vitamin absorption.</li>
            <li><strong>Avoid Alcohol:</strong> Reducing alcohol intake is essential for managing high MCV.</li>
        </ul>
    </div>
    <div>
        <h3>Example Meal Plan for High MCV:</h3>
        <ul>
            <li><strong>Breakfast:</strong> Scrambled eggs with spinach and fortified whole-grain toast.</li>
            <li><strong>Lunch:</strong> Grilled salmon salad with avocado, mixed greens, and citrus dressing.</li>
            <li><strong>Snack:</strong> A handful of almonds and a banana.</li>
            <li><strong>Dinner:</strong> Roasted chicken with quinoa and steamed broccoli.</li>
        </ul>
    </div>
</div>
""")

    # MCH (range: 27-33 pg)
        if values["MCH"] < 27:
            advice.append("""
<div>
    <h2>Low Mean Corpuscular Hemoglobin (MCH) / Hypochromic Anemia</h2>
    <div>
        <h3>Root Cause:</h3>
        <ul>
            <li><strong>Iron Deficiency Anemia:</strong> Low iron levels reduce hemoglobin production, causing smaller RBCs with less hemoglobin.</li>
            <li><strong>Thalassemia:</strong> A genetic disorder that causes defective hemoglobin production, leading to smaller RBCs and low MCH.</li>
            <li><strong>Chronic Blood Loss:</strong> Gastrointestinal bleeding, heavy menstruation, or surgery can lead to iron loss, causing low MCH.</li>
            <li><strong>Vitamin B6 Deficiency:</strong> Impairs hemoglobin synthesis, affecting MCH levels.</li>
            <li><strong>Lead Poisoning:</strong> Lead toxicity interferes with heme production, resulting in hypochromic anemia.</li>
            <li><strong>Sideroblastic Anemia:</strong> A condition in which the bone marrow produces abnormal RBCs with insufficient hemoglobin.</li>
        </ul>
    </div>
    <div>
        <h3>Tips:</h3>
        <ul>
            <li><strong>Increase Iron Intake:</strong> Iron-rich foods or supplements can help improve low MCH.</li>
            <li><strong>Address Underlying Conditions:</strong> Treat conditions like chronic blood loss to address low MCH.</li>
            <li><strong>Increase Vitamin B6:</strong> Consume foods rich in vitamin B6 such as poultry, potatoes, and bananas.</li>
            <li><strong>Check for Lead Exposure:</strong> Seek medical treatment and eliminate exposure if lead poisoning is suspected.</li>
            <li><strong>Genetic Counseling:</strong> For suspected thalassemia, consult with a specialist for further evaluation and management.</li>
        </ul>
    </div>
    <div>
        <h3>Foods to Eat:</h3>
        <ul>
            <li><strong>Iron-Rich Foods:</strong> Heme iron: Red meat, poultry, fish, and liver. Non-heme iron: Lentils, beans, tofu, quinoa, and fortified cereals.</li>
            <li><strong>Vitamin B6-Rich Foods:</strong> Poultry, fish, potatoes, bananas, fortified cereals, and chickpeas.</li>
            <li><strong>Vitamin C-Rich Foods:</strong> Citrus fruits, bell peppers, tomatoes, broccoli, and strawberries to enhance iron absorption.</li>
            <li><strong>Folate-Rich Foods:</strong> Leafy greens, citrus fruits, beans, lentils, and fortified cereals.</li>
        </ul>
    </div>
    <div>
        <h3>Example Meal Plan for Low MCH:</h3>
        <ul>
            <li><strong>Breakfast:</strong> Fortified cereal with almond milk, strawberries, and a boiled egg.</li>
            <li><strong>Lunch:</strong> Spinach and lentil salad with a citrus dressing.</li>
            <li><strong>Snack:</strong> Pumpkin seeds and an orange.</li>
            <li><strong>Dinner:</strong> Grilled chicken with quinoa and steamed broccoli.</li>
        </ul>
    </div>
</div>
""")
        elif values["MCH"] > 32:
            advice.append("""
<div>
    <h2>High Mean Corpuscular Hemoglobin (MCH) / Hyperchromic Anemia</h2>
    <div>
        <h3>Root Cause:</h3>
        <ul>
            <li><strong>Vitamin B12 Deficiency:</strong> Causes larger, hyperchromic RBCs with more hemoglobin content.</li>
            <li><strong>Folate Deficiency:</strong> Impairs RBC production, resulting in larger RBCs with higher hemoglobin levels.</li>
            <li><strong>Alcohol Abuse:</strong> Interferes with B12 and folate absorption, leading to high MCH.</li>
            <li><strong>Liver Disease:</strong> Liver conditions may lead to macrocytic RBCs with increased hemoglobin content.</li>
            <li><strong>Hypothyroidism:</strong> An underactive thyroid can result in larger RBCs with increased hemoglobin.</li>
            <li><strong>Bone Marrow Disorders:</strong> Conditions like myelodysplastic syndromes can cause abnormal RBC characteristics, including high MCH.</li>
        </ul>
    </div>
    <div>
        <h3>Tips:</h3>
        <ul>
            <li><strong>Increase Folate and Vitamin B12 Intake:</strong> Include B12 and folate-rich foods in your diet or take supplements.</li>
            <li><strong>Limit Alcohol Consumption:</strong> Reducing or eliminating alcohol intake may help normalize MCH levels.</li>
            <li><strong>Treat Thyroid Dysfunction:</strong> Follow your doctor's treatment plan for hypothyroidism.</li>
            <li><strong>Monitor Medications:</strong> Consult your doctor if medications are contributing to high MCH.</li>
            <li><strong>Manage Liver Disease:</strong> Work with your healthcare provider to address liver conditions.</li>
        </ul>
    </div>
    <div>
        <h3>Foods to Eat:</h3>
        <ul>
            <li><strong>Vitamin B12-Rich Foods:</strong> Eggs, dairy, fish, poultry, shellfish, and fortified cereals.</li>
            <li><strong>Folate-Rich Foods:</strong> Leafy greens, citrus fruits, beans, peas, lentils, and fortified cereals.</li>
            <li><strong>Iron-Rich Foods:</strong> Lean meats, beans, tofu, and fortified cereals for overall blood health.</li>
            <li><strong>Healthy Fats:</strong> Omega-3-rich foods like salmon, flaxseeds, and walnuts to support nutrient absorption.</li>
            <li><strong>Antioxidant-Rich Foods:</strong> Berries, nuts, and leafy greens to reduce oxidative stress.</li>
        </ul>
    </div>
    <div>
        <h3>Example Meal Plan for High MCH:</h3>
        <ul>
            <li><strong>Breakfast:</strong> Scrambled eggs with spinach and fortified whole-grain toast.</li>
            <li><strong>Lunch:</strong> Grilled salmon salad with avocado, mixed greens, and citrus dressing.</li>
            <li><strong>Snack:</strong> Almonds and a banana.</li>
            <li><strong>Dinner:</strong> Roasted chicken with quinoa and steamed broccoli.</li>
        </ul>
    </div>
</div>
""")


    # MCHC (range: 320-360 g/dL)
        if values["MCHC"] < 31.5:
            advice.append("""
<div>
    <h2>Low Mean Corpuscular Hemoglobin Concentration (MCHC) / Hypochromic Anemia</h2>
    <div>
        <h3>Root Cause:</h3>
        <ul>
            <li><strong>Iron Deficiency Anemia:</strong> Essential for hemoglobin production, low iron causes reduced hemoglobin concentration.</li>
            <li><strong>Hereditary Spherocytosis:</strong> Genetic condition causing abnormally shaped RBCs with lower hemoglobin concentration.</li>
            <li><strong>Thalassemia:</strong> Defective hemoglobin production leading to reduced MCHC.</li>
            <li><strong>Chronic Blood Loss:</strong> Conditions like gastrointestinal bleeding or heavy menstruation cause iron deficiency and lower MCHC.</li>
            <li><strong>Sideroblastic Anemia:</strong> Inability to incorporate iron into hemoglobin, leading to low MCHC.</li>
            <li><strong>Lead Poisoning:</strong> Lead toxicity interferes with heme production, reducing hemoglobin concentration.</li>
        </ul>
    </div>
    <div>
        <h3>Tips:</h3>
        <ul>
            <li><strong>Increase Iron Intake:</strong> Iron supplements or iron-rich foods can help normalize MCHC.</li>
            <li><strong>Address Underlying Blood Loss:</strong> Treat the source of chronic blood loss.</li>
            <li><strong>Monitor for Genetic Conditions:</strong> Proper management for conditions like thalassemia or hereditary spherocytosis.</li>
            <li><strong>Check for Lead Exposure:</strong> Seek treatment for lead poisoning and avoid further exposure.</li>
            <li><strong>Enhance Iron Absorption:</strong> Consume vitamin C-rich foods with iron-rich meals.</li>
        </ul>
    </div>
    <div>
        <h3>Foods to Eat:</h3>
        <ul>
            <li><strong>Iron-Rich Foods:</strong> Heme iron: Red meat, poultry, fish, liver. Non-heme iron: Lentils, beans, tofu, spinach, pumpkin seeds, fortified cereals.</li>
            <li><strong>Vitamin C-Rich Foods:</strong> Citrus fruits, bell peppers, tomatoes, broccoli, and strawberries.</li>
            <li><strong>Folate-Rich Foods:</strong> Leafy greens, avocado, beans, lentils, and fortified cereals.</li>
            <li><strong>Vitamin B12-Rich Foods:</strong> Eggs, dairy products, fortified cereals, and fish.</li>
        </ul>
    </div>
    <div>
        <h3>Example Meal Plan for Low MCHC:</h3>
        <ul>
            <li><strong>Breakfast:</strong> Fortified cereal with almond milk, strawberries, and a boiled egg.</li>
            <li><strong>Lunch:</strong> Spinach and lentil salad with a citrus dressing.</li>
            <li><strong>Snack:</strong> A handful of pumpkin seeds and an orange.</li>
            <li><strong>Dinner:</strong> Grilled chicken with quinoa and steamed broccoli.</li>
        </ul>
    </div>
</div>
""")
        elif values["MCHC"] > 34.5:
            advice.append("""
<div>
    <h2>High Mean Corpuscular Hemoglobin Concentration (MCHC) / Hyperchromic Anemia</h2>
    <div>
        <h3>Root Cause:</h3>
        <ul>
            <li><strong>Hereditary Spherocytosis:</strong> Genetic condition causing spherical RBCs with higher hemoglobin concentration.</li>
            <li><strong>Dehydration:</strong> Reduces plasma volume, concentrating red blood cells and increasing MCHC.</li>
            <li><strong>Cold Agglutinin Disease:</strong> A rare condition where cold temperatures cause RBC clumping, elevating MCHC.</li>
            <li><strong>Autoimmune Hemolytic Anemia:</strong> The immune system attacks RBCs, increasing hemoglobin concentration in remaining cells.</li>
            <li><strong>Burns or Severe Trauma:</strong> Fluid loss from injuries can elevate MCHC values.</li>
        </ul>
    </div>
    <div>
        <h3>Tips:</h3>
        <ul>
            <li><strong>Hydrate Properly:</strong> Maintain adequate hydration to prevent falsely elevated MCHC.</li>
            <li><strong>Address Underlying Conditions:</strong> Work with your doctor to manage autoimmune or hemolytic disorders.</li>
            <li><strong>Monitor Genetic Conditions:</strong> Consult your doctor about hereditary spherocytosis management.</li>
            <li><strong>Treat Dehydration:</strong> Ensure proper fluid intake, especially during physical activity or illness.</li>
            <li><strong>Consult for Rare Conditions:</strong> Discuss potential diagnosis and management of cold agglutinin disease with your doctor.</li>
        </ul>
    </div>
    <div>
        <h3>Foods to Eat:</h3>
        <ul>
            <li><strong>Hydrating Foods:</strong> Cucumbers, watermelon, oranges, and bell peppers.</li>
            <li><strong>Electrolyte-Rich Foods:</strong> Bananas, sweet potatoes, spinach, and avocados.</li>
            <li><strong>Anti-inflammatory Foods:</strong> Fatty fish (salmon, mackerel), berries, and leafy greens.</li>
            <li><strong>Protein-Rich Foods:</strong> Lean meats, poultry, fish, eggs, and legumes.</li>
            <li><strong>Avoid Excess Salt:</strong> Reduce salt intake to maintain fluid balance.</li>
        </ul>
    </div>
    <div>
        <h3>Example Meal Plan for High MCHC:</h3>
        <ul>
            <li><strong>Breakfast:</strong> Oatmeal with chia seeds, blueberries, and almond butter.</li>
            <li><strong>Lunch:</strong> Grilled chicken salad with mixed greens, cucumber, avocado, and a light vinaigrette.</li>
            <li><strong>Snack:</strong> A handful of almonds and a banana.</li>
            <li><strong>Dinner:</strong> Grilled salmon with quinoa and steamed asparagus.</li>
        </ul>
    </div>
</div>
""")


    # RDW (range: 11.5-14.5%)
        if values["RDW"] < 11.6:
            advice.append("""
<div>
    <h2>Low Red Cell Distribution Width (RDW)</h2>
    <div>
        <h3>Root Cause:</h3>
        <ul>
            <li><strong>Normal Variation:</strong> Often not concerning and reflects uniformity in red blood cell (RBC) size.</li>
            <li><strong>Recent Blood Transfusion:</strong> Temporary decrease due to transfused RBCs being of similar size.</li>
            <li><strong>Bone Marrow Disorders:</strong> Certain conditions may lead to uniform RBC production.</li>
            <li><strong>Chronic Diseases:</strong> Conditions like liver diseases can lead to uniform RBC size, lowering RDW.</li>
            <li><strong>Nutritional Deficiencies (rare):</strong> Mild deficiencies that don’t significantly affect RBC production.</li>
        </ul>
    </div>
    <div>
        <h3>Tips:</h3>
        <ul>
            <li><strong>No Special Action Needed:</strong> Often not a concern unless linked to a specific condition.</li>
            <li><strong>Monitor Transfusion Effects:</strong> Low RDW after transfusion will normalize over time.</li>
            <li><strong>Maintain Adequate Nutrition:</strong> Balanced diet rich in vitamins and minerals supports RBC health.</li>
            <li><strong>Consult Your Doctor:</strong> Persistent low RDW or association with abnormal results may require further evaluation.</li>
        </ul>
    </div>
    <div>
        <h3>Foods to Eat:</h3>
        <ul>
        <li>
            <strong>Foods Rich in Iron:</strong>
            <ul>
                <li>Heme Iron: Lean red meat, poultry, fish (e.g., salmon, tuna)</li>
                <li>Non-Heme Iron: Spinach, lentils, beans, tofu, fortified cereals</li>
            </ul>
        </li>
        <li>
            <strong>Foods Rich in Vitamin B12:</strong>
            <ul>
                <li>Shellfish (clams, crab, oysters)</li>
                <li>Liver (beef or chicken)</li>
                <li>Dairy products (milk, yogurt, cheese)</li>
                <li>Eggs</li>
                <li>Fortified plant-based milk (almond, soy, oat)</li>
            </ul>
        </li>
        <li>
            <strong>Foods Rich in Folate (Vitamin B9):</strong>
            <ul>
                <li>Dark leafy greens (spinach, kale, Swiss chard)</li>
                <li>Avocado</li>
                <li>Asparagus</li>
                <li>Citrus fruits (oranges, grapefruits)</li>
                <li>Legumes (chickpeas, black-eyed peas)</li>
                <li>Fortified grains and cereals</li>
            </ul>
        </li>
        <li>
            <strong>Foods Rich in Vitamin C:</strong>
            <ul>
                <li>Citrus fruits (oranges, lemons, limes)</li>
                <li>Bell peppers</li>
                <li>Strawberries</li>
                <li>Kiwi</li>
                <li>Broccoli</li>
                <li>Tomatoes</li>
            </ul>
        </li>
        <li>
            <strong>Foods Rich in Copper:</strong>
            <ul>
                <li>Nuts and seeds (cashews, almonds, sunflower seeds)</li>
                <li>Shellfish (lobster, crab)</li>
                <li>Whole grains (quinoa, oats)</li>
                <li>Dark chocolate</li>
            </ul>
        </li>
        <li>
            <strong>Foods Rich in Vitamin E:</strong>
            <ul>
                <li>Nuts (almonds, hazelnuts)</li>
                <li>Seeds (sunflower seeds)</li>
                <li>Vegetable oils (sunflower, safflower, olive oil)</li>
                <li>Spinach</li>
                <li>Avocados</li>
            </ul>
        </li>
        <li>
            <strong>Hydration:</strong> Drink sufficient water daily to support overall blood health.
        </li>
    </ul>
    </div>
    <div>
        <h3>Example Meal Plan for Low RDW:</h3>
        <ul>
            <li><strong>Breakfast:</strong> Whole grain toast with avocado, a poached egg, and orange slices.</li>
            <li><strong>Lunch:</strong> Grilled chicken salad with mixed greens, tomatoes, carrots, and olive oil dressing.</li>
            <li><strong>Snack:</strong> A handful of almonds and a small apple.</li>
            <li><strong>Dinner:</strong> Baked salmon with quinoa and steamed broccoli.</li>
        </ul>
    </div>
</div>
""")
        elif values["RDW"] > 14:
            advice.append("""
<div>
    <h2>High Red Cell Distribution Width (RDW)</h2>
    <div>
        <h3>Root Cause:</h3>
        <ul>
            <li><strong>Iron Deficiency Anemia:</strong> Produces both small and large RBCs, increasing RDW.</li>
            <li><strong>Vitamin B12 or Folate Deficiency:</strong> Essential for RBC maturation, deficiencies cause larger RBCs.</li>
            <li><strong>Anemia of Chronic Disease:</strong> Mixed RBC sizes due to chronic conditions like kidney disease or cancer.</li>
            <li><strong>Hemolytic Anemia:</strong> Premature RBC destruction leads to new RBCs of varying sizes.</li>
            <li><strong>Liver Disease:</strong> Affects RBC production, increasing RDW.</li>
            <li><strong>Bone Marrow Disorders:</strong> Abnormal RBC production in conditions like myelodysplastic syndromes.</li>
        </ul>
    </div>
    <div>
        <h3>Tips:</h3>
        <ul>
            <li><strong>Address Nutritional Deficiencies:</strong> Correct iron, B12, or folate deficiencies through diet or supplements.</li>
            <li><strong>Manage Chronic Conditions:</strong> Properly manage chronic diseases associated with high RDW.</li>
            <li><strong>Monitor for Hemolytic or Bone Marrow Disorders:</strong> Further tests and treatments may be needed.</li>
            <li><strong>Hydration:</strong> Proper hydration can help maintain normal RDW levels.</li>
        </ul>
    </div>
    <div>
        <h3>Foods to Eat:</h3>
        <ul>
            <li><strong>Iron-Rich Foods:</strong> Heme iron: Red meat, poultry, fish, liver. Non-heme iron: Lentils, beans, tofu, spinach, fortified cereals.</li>
            <li><strong>Vitamin B12-Rich Foods:</strong> Eggs, dairy, fish, and fortified cereals.</li>
            <li><strong>Folate-Rich Foods:</strong> Leafy greens, citrus fruits, beans, peas, lentils, and fortified cereals.</li>
            <li><strong>Vitamin C-Rich Foods:</strong> Citrus fruits, bell peppers, tomatoes, broccoli, and strawberries to enhance iron absorption.</li>
            <li><strong>Healthy Fats:</strong> Fatty fish, flaxseeds, chia seeds, and walnuts to support overall health and manage inflammation.</li>
        </ul>
    </div>
    <div>
        <h3>Example Meal Plan for High RDW:</h3>
        <ul>
            <li><strong>Breakfast:</strong> Scrambled eggs with spinach and fortified whole-grain toast (providing B12 and folate).</li>
            <li><strong>Lunch:</strong> Grilled chicken salad with avocado, mixed greens, citrus dressing, and quinoa.</li>
            <li><strong>Snack:</strong> A handful of pumpkin seeds and a small orange.</li>
            <li><strong>Dinner:</strong> Baked salmon with steamed broccoli and a side of quinoa or brown rice.</li>
        </ul>
    </div>
</div>
""")

    # Total Leucocytes Count (range: 4.0-11.0 x10⁹/L)
        if values["Total Leucocytes Count"] < 4000:
            advice.append("""
<div>
    <h2>Low Total Leucocyte Count (Leukopenia)</h2>
    <div>
        <h3>Root Cause:</h3>
        <ul>
            <li><strong>Viral Infections:</strong> Infections like HIV, influenza, and hepatitis can suppress bone marrow function and reduce WBC count.</li>
            <li><strong>Autoimmune Disorders:</strong> Conditions like lupus or rheumatoid arthritis may attack the bone marrow, decreasing WBC production.</li>
            <li><strong>Bone Marrow Disorders:</strong> Disorders like aplastic anemia or myelodysplastic syndromes impair WBC production.</li>
            <li><strong>Medications:</strong> Chemotherapy, certain antibiotics, antipsychotics, and immunosuppressants can cause bone marrow suppression.</li>
            <li><strong>Severe Infections:</strong> Chronic infections may overwhelm the bone marrow, leading to decreased WBC production.</li>
            <li><strong>Nutritional Deficiencies:</strong> Lack of essential nutrients like vitamin B12, folate, and copper can reduce WBC production.</li>
            <li><strong>Radiation Exposure:</strong> High radiation levels damage bone marrow, resulting in leukopenia.</li>
        </ul>
    </div>
    <div>
        <h3>Tips:</h3>
        <ul>
            <li><strong>Increase Nutrient Intake:</strong> Ensure adequate intake of vitamin B12, folate, and zinc for healthy WBC production.</li>
            <li><strong>Review Medications:</strong> Consult your doctor if medications are causing leukopenia.</li>
            <li><strong>Treat Underlying Infections or Conditions:</strong> Manage infections or autoimmune conditions causing leukopenia.</li>
            <li><strong>Avoid Exposure to Infections:</strong> Take precautions to prevent infections due to a weakened immune system.</li>
            <li><strong>Monitor Bone Marrow Health:</strong> If disorders are suspected, further tests or treatments may be necessary.</li>
        </ul>
    </div>
    <div>
        <h3>Foods to Eat:</h3>
        <ul>
            <li><strong>Vitamin B12-Rich Foods:</strong> Meat, fish, poultry, eggs, and dairy products.</li>
            <li><strong>Folate-Rich Foods:</strong> Leafy greens (spinach, kale), citrus fruits, beans, peas, lentils, and fortified cereals.</li>
            <li><strong>Zinc-Rich Foods:</strong> Shellfish (oysters, crab), lean meats, pumpkin seeds, and beans.</li>
            <li><strong>Copper-Rich Foods:</strong> Shellfish, seeds, nuts, whole grains, and legumes.</li>
            <li><strong>Protein-Rich Foods:</strong> Chicken, turkey, lean beef, eggs, and legumes to support overall immune health.</li>
        </ul>
    </div>
    <div>
        <h3>Example Meal Plan for Low Leucocytes:</h3>
        <ul>
            <li><strong>Breakfast:</strong> Scrambled eggs with spinach and whole-grain toast (rich in folate).</li>
            <li><strong>Lunch:</strong> Grilled chicken with quinoa and a side of leafy greens like kale and avocado (rich in B12 and folate).</li>
            <li><strong>Snack:</strong> A handful of pumpkin seeds and a banana.</li>
            <li><strong>Dinner:</strong> Salmon with roasted sweet potatoes and steamed broccoli (rich in zinc and B12).</li>
        </ul>
    </div>
</div>
""")
        elif values["Total Leucocytes Count"] > 10000:
            advice.append("""
<div>
    <h2>High Total Leucocyte Count (Leukocytosis)</h2>
    <div>
        <h3>Root Cause:</h3>
        <ul>
            <li><strong>Infections:</strong> Bacterial, fungal, or viral infections trigger increased WBC production to fight infection.</li>
            <li><strong>Inflammatory Disorders:</strong> Conditions like rheumatoid arthritis or inflammatory bowel disease cause chronic inflammation and elevated WBC counts.</li>
            <li><strong>Stress Responses:</strong> Physical or emotional stress, trauma, or extreme temperatures can temporarily increase WBC counts.</li>
            <li><strong>Leukemia:</strong> Cancers of the bone marrow and blood cause overproduction of WBCs.</li>
            <li><strong>Allergic Reactions:</strong> Severe allergies can elevate WBC counts, especially eosinophils.</li>
            <li><strong>Medications:</strong> Corticosteroids, epinephrine, or lithium can increase WBC production.</li>
            <li><strong>Smoking:</strong> Smoking causes a sustained increase in WBC counts, especially neutrophils.</li>
        </ul>
    </div>
    <div>
        <h3>Tips:</h3>
        <ul>
            <li><strong>Identify and Treat Infections:</strong> Use appropriate treatments (antibiotics, antivirals, antifungals) for infections.</li>
            <li><strong>Manage Chronic Inflammatory Conditions:</strong> Medications to control inflammation may be required.</li>
            <li><strong>Reduce Stress:</strong> Practice stress-reducing techniques such as meditation, yoga, or regular physical activity.</li>
            <li><strong>Consult for Leukemia or Blood Disorders:</strong> Further diagnostic tests like bone marrow biopsy may be needed.</li>
            <li><strong>Quit Smoking:</strong> Smoking cessation is essential for reducing long-term WBC elevation and inflammation.</li>
        </ul>
    </div>
    <div>
        <h3>Foods to Eat:</h3>
        <ul>
            <li><strong>Anti-Inflammatory Foods:</strong> Fatty fish, olive oil, nuts, and turmeric to reduce chronic inflammation.</li>
            <li><strong>Vitamin C-Rich Foods:</strong> Citrus fruits, bell peppers, strawberries, and broccoli to support the immune system and reduce inflammation.</li>
            <li><strong>Antioxidant-Rich Foods:</strong> Blueberries, spinach, kale, and other berries to combat oxidative stress.</li>
            <li><strong>Whole Grains:</strong> Brown rice, quinoa, oats, and barley for fiber and immune support.</li>
            <li><strong>Lean Proteins:</strong> Chicken, turkey, tofu, and legumes to maintain immune function.</li>
        </ul>
    </div>
    <div>
        <h3>Example Meal Plan for High Leucocytes:</h3>
        <ul>
            <li><strong>Breakfast:</strong> Oatmeal with chia seeds, walnuts, and berries (rich in antioxidants and fiber).</li>
            <li><strong>Lunch:</strong> Grilled salmon with quinoa, steamed broccoli, and olive oil dressing (anti-inflammatory foods).</li>
            <li><strong>Snack:</strong> A handful of almonds and an apple.</li>
            <li><strong>Dinner:</strong> Chicken stir-fry with kale, bell peppers, and carrots (rich in vitamin C and fiber).</li>
        </ul>
    </div>
</div>
""")

    # Neutrophils (range: 40-70%)
        if values["Neutrophils"] < 40:
            advice.append("""
<div>
    <h2>Low Neutrophils (Neutropenia)</h2>
    <div>
        <h3>Root Cause:</h3>
        <ul>
            <li><strong>Infections:</strong> Viral infections like HIV, hepatitis, influenza, or Epstein-Barr virus can suppress neutrophil production.</li>
            <li><strong>Bone Marrow Disorders:</strong> Conditions like aplastic anemia, myelodysplastic syndromes, or leukemia impair neutrophil production.</li>
            <li><strong>Autoimmune Diseases:</strong> Conditions like systemic lupus erythematosus (SLE) or rheumatoid arthritis may attack neutrophils, lowering their count.</li>
            <li><strong>Medications:</strong> Drugs like chemotherapy, immunosuppressants, or certain antibiotics can reduce neutrophil production.</li>
            <li><strong>Nutritional Deficiencies:</strong> Lack of vitamin B12, folate, or copper can impair neutrophil production.</li>
            <li><strong>Severe Infections or Sepsis:</strong> Chronic or severe infections may deplete neutrophils faster than they are produced.</li>
            <li><strong>Congenital Disorders:</strong> Genetic conditions such as cyclic neutropenia or Kostmann syndrome can cause chronic low neutrophil levels.</li>
        </ul>
    </div>
    <div>
        <h3>Tips:</h3>
        <ul>
            <li><strong>Increase Nutrient Intake:</strong> Consume foods rich in vitamin B12, folate, copper, and zinc to support neutrophil production.</li>
            <li><strong>Avoid Infections:</strong> Practice good hygiene and avoid crowded areas to reduce the risk of infections.</li>
            <li><strong>Consult Your Doctor for Medication Adjustments:</strong> If medications are causing neutropenia, discuss alternatives with your doctor.</li>
            <li><strong>Monitor Bone Marrow Health:</strong> If bone marrow disorders are suspected, further diagnostic tests may be required.</li>
            <li><strong>Consider Neutrophil-Stimulating Drugs:</strong> Medications like G-CSF (granulocyte-colony stimulating factor) can help stimulate neutrophil production if needed.</li>
        </ul>
    </div>
    <div>
        <h3>Foods to Eat:</h3>
        <ul>
            <li><strong>Vitamin B12-Rich Foods:</strong> Meat, poultry, fish, eggs, and dairy products.</li>
            <li><strong>Folate-Rich Foods:</strong> Leafy greens (spinach, kale), citrus fruits, beans, peas, lentils, and fortified cereals.</li>
            <li><strong>Zinc-Rich Foods:</strong> Shellfish, lean meats, nuts, and seeds.</li>
            <li><strong>Copper-Rich Foods:</strong> Shellfish, nuts, seeds, whole grains, and legumes.</li>
            <li><strong>Protein-Rich Foods:</strong> Chicken, turkey, tofu, and legumes to maintain immune health.</li>
        </ul>
    </div>
    <div>
        <h3>Example Meal Plan for Low Neutrophils:</h3>
        <ul>
            <li><strong>Breakfast:</strong> Scrambled eggs with spinach and whole-grain toast.</li>
            <li><strong>Lunch:</strong> Grilled chicken with quinoa and a side of leafy greens.</li>
            <li><strong>Snack:</strong> A handful of pumpkin seeds and a small apple.</li>
            <li><strong>Dinner:</strong> Baked salmon with roasted sweet potatoes and steamed broccoli.</li>
        </ul>
    </div>
</div>
""")
        elif values["Neutrophils"] > 80:
            advice.append("""
<div>
    <h2>High Neutrophils (Neutrophilia)</h2>
    <div>
        <h3>Root Cause:</h3>
        <ul>
            <li><strong>Infections:</strong> Bacterial infections like pneumonia, appendicitis, or sepsis trigger an elevated neutrophil count.</li>
            <li><strong>Inflammatory Conditions:</strong> Chronic inflammation from rheumatoid arthritis, inflammatory bowel disease, or vasculitis can cause neutrophilia.</li>
            <li><strong>Stress Responses:</strong> Physical or emotional stress from surgery, trauma, or extreme conditions can temporarily elevate neutrophil levels.</li>
            <li><strong>Leukemia:</strong> Chronic myelogenous leukemia (CML) or other leukemias can lead to excessive neutrophil production.</li>
            <li><strong>Smoking:</strong> Smoking can increase neutrophil counts, especially those related to lung inflammation.</li>
            <li><strong>Medications:</strong> Corticosteroids, lithium, or epinephrine can stimulate neutrophil production.</li>
            <li><strong>Tissue Damage:</strong> Burns or major trauma can trigger neutrophil production as part of the healing process.</li>
        </ul>
    </div>
    <div>
        <h3>Tips:</h3>
        <ul>
            <li><strong>Treat Infections:</strong> Work with your doctor to manage infections with antibiotics or antivirals.</li>
            <li><strong>Control Inflammation:</strong> Medications like corticosteroids or biologics can reduce inflammation.</li>
            <li><strong>Address Stress:</strong> Practice stress-reducing techniques such as meditation or physical activity.</li>
            <li><strong>Avoid Smoking:</strong> Quitting smoking can normalize neutrophil counts and reduce inflammation.</li>
            <li><strong>Monitor for Leukemia or Blood Disorders:</strong> If blood disorders are suspected, diagnostic tests such as bone marrow biopsies may be needed.</li>
        </ul>
    </div>
    <div>
        <h3>Foods to Eat:</h3>
        <ul>
            <li><strong>Anti-Inflammatory Foods:</strong> Fatty fish, olive oil, walnuts, and flaxseeds help reduce chronic inflammation.</li>
            <li><strong>Antioxidant-Rich Foods:</strong> Blueberries, spinach, kale, and strawberries combat oxidative stress.</li>
            <li><strong>Fiber-Rich Foods:</strong> Whole grains, vegetables, and legumes regulate the immune system and reduce inflammation.</li>
            <li><strong>Vitamin C-Rich Foods:</strong> Citrus fruits, bell peppers, and broccoli support immune function.</li>
            <li><strong>Lean Proteins:</strong> Chicken, turkey, tofu, and legumes support overall health without adding inflammation.</li>
        </ul>
    </div>
    <div>
        <h3>Example Meal Plan for High Neutrophils:</h3>
        <ul>
            <li><strong>Breakfast:</strong> Oatmeal with chia seeds, walnuts, and blueberries.</li>
            <li><strong>Lunch:</strong> Grilled salmon with quinoa, steamed broccoli, and a salad with olive oil dressing.</li>
            <li><strong>Snack:</strong> A handful of almonds and an orange.</li>
            <li><strong>Dinner:</strong> Grilled chicken stir-fry with spinach, bell peppers, and carrots.</li>
        </ul>
    </div>
</div>
""")

    # Lymphocytes (range: 20-40%)
        if values["Lymphocytes"] < 20:
            advice.append("""
<div>
    <h2>Low Lymphocytes (Lymphocytopenia)</h2>
    <div>
        <h3>Root Cause:</h3>
        <ul>
            <li><strong>Viral Infections:</strong> Certain viral infections like HIV, hepatitis, influenza, and measles can reduce lymphocyte count by directly affecting the immune system.</li>
            <li><strong>Autoimmune Diseases:</strong> Conditions such as systemic lupus erythematosus (SLE) or rheumatoid arthritis can lower lymphocytes due to the immune system attacking its own tissues.</li>
            <li><strong>Bone Marrow Disorders:</strong> Diseases like aplastic anemia, leukemia, or myelodysplastic syndromes impair lymphocyte production.</li>
            <li><strong>Medications:</strong> Immunosuppressive drugs, chemotherapy, or corticosteroids can suppress immune function, reducing lymphocyte count.</li>
            <li><strong>Malnutrition:</strong> Deficiencies in protein, zinc, vitamin B12, and folate can impair lymphocyte production.</li>
            <li><strong>Radiation Exposure:</strong> High levels of radiation can damage lymphocytes, resulting in a low count.</li>
            <li><strong>Chronic Illnesses:</strong> Conditions such as chronic kidney or liver disease can contribute to lymphocyte reduction.</li>
        </ul>
    </div>
    <div>
        <h3>Tips:</h3>
        <ul>
            <li><strong>Boost Immune System with Nutrition:</strong> Consume sufficient vitamins and minerals like B12, zinc, folate, and protein to support lymphocyte production.</li>
            <li><strong>Consult Your Doctor about Medications:</strong> Discuss dosage adjustments or alternatives for drugs affecting lymphocyte levels.</li>
            <li><strong>Treat Underlying Conditions:</strong> Effective management of autoimmune diseases, infections, or bone marrow disorders can improve lymphocyte counts.</li>
            <li><strong>Improve Lifestyle:</strong> Ensure adequate sleep, regular exercise, and reduced stress for better immune health.</li>
            <li><strong>Prevent Infections:</strong> Practice good hygiene and avoid crowded places to reduce exposure to illness.</li>
        </ul>
    </div>
    <div>
        <h3>Foods to Eat:</h3>
        <ul>
            <li><strong>Protein-Rich Foods:</strong> Chicken, turkey, tofu, fish, and legumes.</li>
            <li><strong>Vitamin B12 and Folate:</strong> Meat, eggs, dairy, leafy greens (spinach, kale), beans, and lentils.</li>
            <li><strong>Zinc-Rich Foods:</strong> Shellfish, lean meats, seeds (pumpkin, sunflower), and nuts (cashews).</li>
            <li><strong>Vitamin C-Rich Foods:</strong> Citrus fruits, strawberries, bell peppers, and broccoli.</li>
        </ul>
    </div>
    <div>
        <h3>Example Meal Plan for Low Lymphocytes:</h3>
        <ul>
            <li><strong>Breakfast:</strong> Scrambled eggs with spinach and whole-grain toast (rich in folate and B12).</li>
            <li><strong>Lunch:</strong> Grilled chicken with quinoa and a side of leafy greens.</li>
            <li><strong>Snack:</strong> A handful of almonds and an orange (rich in vitamin C).</li>
            <li><strong>Dinner:</strong> Baked salmon with roasted sweet potatoes and steamed broccoli.</li>
        </ul>
    </div>
</div>
""")
        elif values["Lymphocytes"] > 40:
            advice.append("""
<div>
    <h2>High Lymphocytes (Lymphocytosis)</h2>
    <div>
        <h3>Root Cause:</h3>
        <ul>
            <li><strong>Viral Infections:</strong> Infections like mononucleosis, cytomegalovirus (CMV), and hepatitis often cause lymphocytosis as the immune system fights the virus.</li>
            <li><strong>Chronic Inflammatory Conditions:</strong> Autoimmune diseases such as rheumatoid arthritis or Crohn's disease may increase lymphocytes due to prolonged immune activation.</li>
            <li><strong>Leukemia or Lymphoma:</strong> Certain cancers, including chronic lymphocytic leukemia (CLL) or lymphoma, can lead to uncontrolled lymphocyte production.</li>
            <li><strong>Stress Responses:</strong> Physical or emotional stress, such as after surgery or trauma, can temporarily elevate lymphocyte levels.</li>
            <li><strong>Smoking:</strong> Smoking may increase lymphocyte count due to inflammation or the body's response to tobacco chemicals.</li>
            <li><strong>Medications:</strong> Drugs such as corticosteroids, lithium, or theophylline can occasionally cause lymphocytosis.</li>
        </ul>
    </div>
    <div>
        <h3>Tips:</h3>
        <ul>
            <li><strong>Treat Infections:</strong> Manage infections with appropriate antiviral or antibiotic treatments.</li>
            <li><strong>Control Inflammation:</strong> For autoimmune diseases or chronic inflammatory conditions, medications like immunosuppressants or corticosteroids may be prescribed.</li>
            <li><strong>Monitor for Leukemia or Blood Disorders:</strong> If suspected, further tests such as bone marrow biopsy or flow cytometry may be recommended.</li>
            <li><strong>Manage Stress:</strong> Engage in stress-reduction techniques like meditation or yoga.</li>
            <li><strong>Quit Smoking:</strong> Smoking cessation can help normalize lymphocyte counts and reduce inflammation.</li>
        </ul>
    </div>
    <div>
        <h3>Foods to Eat:</h3>
        <ul>
            <li><strong>Anti-Inflammatory Foods:</strong> Fatty fish, olive oil, walnuts, and flaxseeds.</li>
            <li><strong>Vitamin C-Rich Foods:</strong> Citrus fruits, bell peppers, broccoli, and strawberries.</li>
            <li><strong>Fiber-Rich Foods:</strong> Whole grains (brown rice, oats, quinoa) and vegetables like spinach and kale.</li>
            <li><strong>Lean Proteins:</strong> Chicken, turkey, tofu, and legumes.</li>
            <li><strong>Antioxidant-Rich Foods:</strong> Berries, green tea, and dark chocolate.</li>
        </ul>
    </div>
    <div>
        <h3>Example Meal Plan for High Lymphocytes:</h3>
        <ul>
            <li><strong>Breakfast:</strong> Oatmeal with chia seeds, walnuts, and blueberries.</li>
            <li><strong>Lunch:</strong> Grilled salmon with quinoa, steamed broccoli, and a salad with olive oil dressing.</li>
            <li><strong>Snack:</strong> A handful of almonds and an orange.</li>
            <li><strong>Dinner:</strong> Grilled chicken stir-fry with spinach, bell peppers, and carrots.</li>
        </ul>
    </div>
</div>
""")

        # Eosinophils (range: 1-4%)
        if values["Eosinophils"] < 1:
            advice.append("""
<div>
    <h2>Low Eosinophils (Eosinopenia)</h2>
    <div>
        <h3>Root Cause:</h3>
        <ul>
            <li><strong>Acute Infections:</strong> The immune system may redirect resources to fight bacterial or viral infections, leading to reduced eosinophils.</li>
            <li><strong>Corticosteroid Medications:</strong> These drugs suppress the immune response, reducing eosinophil counts.</li>
            <li><strong>Cushing’s Syndrome:</strong> High cortisol levels suppress immune functions, including eosinophil production.</li>
            <li><strong>Stress Responses:</strong> Both physical and emotional stress lower eosinophils due to the effects of cortisol.</li>
            <li><strong>Bone Marrow Disorders:</strong> Conditions like aplastic anemia affect blood cell production, including eosinophils.</li>
            <li><strong>Hematologic Diseases:</strong> Disorders such as leukemia or myelodysplastic syndromes can suppress eosinophil production.</li>
            <li><strong>Hypercortisolism:</strong> Excess cortisol, including adrenal gland tumors, can lead to eosinopenia.</li>
        </ul>
    </div>
    <div>
        <h3>Tips:</h3>
        <ul>
            <li><strong>Review Medications:</strong> Consult with your doctor about alternative treatments if corticosteroids are causing eosinopenia.</li>
            <li><strong>Manage Stress:</strong> Practice relaxation techniques like meditation, yoga, or deep breathing exercises.</li>
            <li><strong>Treat Underlying Conditions:</strong> Hormonal imbalances or bone marrow issues should be addressed by a healthcare provider.</li>
            <li><strong>Avoid Infections:</strong> Strengthen your immune defenses to prevent illness when eosinophils are low.</li>
        </ul>
    </div>
    <div>
        <h3>Foods to Eat:</h3>
        <ul>
            <li><strong>Protein-Rich Foods:</strong> Lean meats, poultry, tofu, and legumes to support immune function.</li>
            <li><strong>Vitamin C-Rich Foods:</strong> Citrus fruits, bell peppers, strawberries, and broccoli to boost immunity.</li>
            <li><strong>Magnesium-Rich Foods:</strong> Nuts, seeds, spinach, and whole grains to reduce stress and support cellular health.</li>
            <li><strong>Zinc-Rich Foods:</strong> Shellfish, lean meats, seeds, and legumes to enhance immune response.</li>
        </ul>
    </div>
    <div>
        <h3>Example Meal Plan for Low Eosinophils:</h3>
        <ul>
            <li><strong>Breakfast:</strong> Scrambled eggs with spinach and whole-grain toast.</li>
            <li><strong>Lunch:</strong> Grilled chicken with quinoa and a side of leafy greens.</li>
            <li><strong>Snack:</strong> A handful of almonds and an orange.</li>
            <li><strong>Dinner:</strong> Grilled salmon with roasted sweet potatoes and steamed broccoli.</li>
        </ul>
    </div>
</div>
""")
        elif values["Eosinophils"] > 6:
            advice.append("""
<div>
    <h2>High Eosinophils (Eosinophilia)</h2>
    <div>
        <h3>Root Cause:</h3>
        <ul>
            <li><strong>Allergic Reactions:</strong> Eosinophils are involved in allergic responses like asthma, hay fever, or rhinitis.</li>
            <li><strong>Parasitic Infections:</strong> Eosinophils increase in response to parasitic infections such as hookworm or roundworm.</li>
            <li><strong>Autoimmune Disorders:</strong> Conditions like eosinophilic esophagitis or granulomatosis can elevate eosinophil levels.</li>
            <li><strong>Skin Disorders:</strong> Diseases like eczema or dermatitis often involve eosinophil-driven inflammation.</li>
            <li><strong>Drug Reactions:</strong> Certain medications, such as antibiotics or NSAIDs, can induce eosinophilia.</li>
            <li><strong>Hematologic Diseases:</strong> Disorders like chronic eosinophilic leukemia can increase eosinophil counts due to abnormal production.</li>
            <li><strong>Chronic Inflammatory Conditions:</strong> Conditions like vasculitis or inflammatory bowel disease can elevate eosinophil levels.</li>
        </ul>
    </div>
    <div>
        <h3>Tips:</h3>
        <ul>
            <li><strong>Identify and Treat Allergies:</strong> Use antihistamines or other medications to manage allergic reactions.</li>
            <li><strong>Treat Parasitic Infections:</strong> Anti-parasitic treatments can address the root cause of eosinophilia.</li>
            <li><strong>Control Inflammation:</strong> Corticosteroids or biologic therapies may be needed for autoimmune or inflammatory conditions.</li>
            <li><strong>Monitor Drug Reactions:</strong> Discuss medication adjustments with your doctor if drug-induced eosinophilia is suspected.</li>
            <li><strong>Manage Underlying Conditions:</strong> Specialized treatments may be required for blood disorders like chronic eosinophilic leukemia.</li>
        </ul>
    </div>
    <div>
        <h3>Foods to Eat:</h3>
        <ul>
            <li><strong>Anti-Inflammatory Foods:</strong> Fatty fish, walnuts, flaxseeds, and olive oil to reduce inflammation.</li>
            <li><strong>Vitamin C-Rich Foods:</strong> Citrus fruits, bell peppers, strawberries, and broccoli to support immunity.</li>
            <li><strong>Antioxidant-Rich Foods:</strong> Berries, leafy greens, and nuts to combat oxidative stress.</li>
            <li><strong>Fiber-Rich Foods:</strong> Whole grains, vegetables, and legumes to improve gut health and reduce inflammation.</li>
            <li><strong>Probiotics:</strong> Yogurt, kefir, and kimchi to balance gut bacteria and influence immune responses.</li>
        </ul>
    </div>
    <div>
        <h3>Example Meal Plan for High Eosinophils:</h3>
        <ul>
            <li><strong>Breakfast:</strong> Oatmeal with chia seeds, walnuts, and blueberries.</li>
            <li><strong>Lunch:</strong> Grilled salmon with quinoa, steamed broccoli, and a side salad with olive oil dressing.</li>
            <li><strong>Snack:</strong> A handful of almonds and an orange.</li>
            <li><strong>Dinner:</strong> Grilled chicken stir-fry with spinach, bell peppers, and carrots.</li>
        </ul>
    </div>
</div>
""")

    # Monocytes (range: 2-8%)
        if values["Monocytes"] < 2:
            advice.append("""
<div>
    <h2>Low Monocytes (Monocytopenia)</h2>
    <div>
        <h3>Root Cause:</h3>
        <ul>
            <li><strong>Bone Marrow Disorders:</strong> Conditions like aplastic anemia, myelodysplastic syndromes, or leukemia affect monocyte production.</li>
            <li><strong>Acute Infections:</strong> Viral infections (e.g., HIV, influenza, hepatitis) can decrease monocytes as the immune system redirects resources.</li>
            <li><strong>Immunosuppressive Drugs:</strong> Medications like corticosteroids, chemotherapy, or immunosuppressive drugs reduce monocyte production.</li>
            <li><strong>Corticosteroid Use:</strong> Long-term corticosteroid use decreases monocyte levels.</li>
            <li><strong>Nutritional Deficiencies:</strong> Deficiencies in folate, vitamin B12, or iron can result in low monocyte counts.</li>
            <li><strong>Severe Stress:</strong> Physical or emotional stress may suppress monocyte production.</li>
            <li><strong>Genetic Disorders:</strong> Rare genetic conditions like congenital neutropenia affect monocyte production.</li>
        </ul>
    </div>
    <div>
        <h3>Tips:</h3>
        <ul>
            <li><strong>Consult with Your Doctor:</strong> Adjust medication dosages or consider alternatives if medications cause monocytopenia.</li>
            <li><strong>Address Nutritional Deficiencies:</strong> Ensure adequate intake of vitamin B12, folate, and iron to support monocyte production.</li>
            <li><strong>Treat Underlying Conditions:</strong> Address bone marrow disorders or infections to improve monocyte levels.</li>
            <li><strong>Reduce Stress:</strong> Engage in relaxation techniques like yoga, meditation, or regular exercise.</li>
        </ul>
    </div>
    <div>
        <h3>Foods to Eat:</h3>
        <ul>
            <li><strong>Iron-Rich Foods:</strong> Lean meats, liver, spinach, beans, lentils, and fortified cereals.</li>
            <li><strong>Vitamin B12-Rich Foods:</strong> Meat, poultry, fish, eggs, and dairy.</li>
            <li><strong>Folate-Rich Foods:</strong> Leafy greens, citrus fruits, beans, peas, lentils, and fortified cereals.</li>
            <li><strong>Zinc-Rich Foods:</strong> Shellfish, lean meats, seeds, nuts, and legumes.</li>
            <li><strong>Protein-Rich Foods:</strong> Chicken, fish, tofu, and legumes.</li>
        </ul>
    </div>
    <div>
        <h3>Example Meal Plan for Low Monocytes:</h3>
        <ul>
            <li><strong>Breakfast:</strong> Scrambled eggs with spinach and whole-grain toast.</li>
            <li><strong>Lunch:</strong> Grilled chicken with quinoa and leafy greens.</li>
            <li><strong>Snack:</strong> A handful of almonds and an orange.</li>
            <li><strong>Dinner:</strong> Baked salmon with roasted sweet potatoes and steamed broccoli.</li>
        </ul>
    </div>
</div>
""")
        elif values["Monocytes"] > 10:
            advice.append("""
<div>
    <h2>High Monocytes (Monocytosis)</h2>
    <div>
        <h3>Root Cause:</h3>
        <ul>
            <li><strong>Chronic Infections:</strong> Infections like tuberculosis, endocarditis, or brucellosis can increase monocytes.</li>
            <li><strong>Autoimmune Disorders:</strong> Conditions like rheumatoid arthritis, lupus, or IBD cause chronic inflammation, leading to monocytosis.</li>
            <li><strong>Hematological Disorders:</strong> Disorders like chronic myelomonocytic leukemia or monocytic leukemia increase monocyte production.</li>
            <li><strong>Cancer:</strong> Some cancers, like lymphoma and leukemia, elevate monocyte levels.</li>
            <li><strong>Inflammatory Conditions:</strong> Conditions like vasculitis or sarcoidosis can raise monocyte levels.</li>
            <li><strong>Recovery from Acute Infections:</strong> Monocyte levels may increase temporarily during recovery.</li>
            <li><strong>Stress or Trauma:</strong> Major surgeries or trauma can elevate monocyte counts as part of the immune response.</li>
        </ul>
    </div>
    <div>
        <h3>Tips:</h3>
        <ul>
            <li><strong>Identify and Treat Chronic Infections:</strong> Use antibiotics or appropriate treatments for infections.</li>
            <li><strong>Control Autoimmune Diseases:</strong> Corticosteroids or immunosuppressive drugs can reduce inflammation and normalize monocyte levels.</li>
            <li><strong>Address Cancer or Blood Disorders:</strong> Specialized treatments like chemotherapy or targeted therapy may be required.</li>
            <li><strong>Manage Inflammation:</strong> Anti-inflammatory drugs or biologics can help for conditions like IBD or vasculitis.</li>
            <li><strong>Monitor for Recovery from Infections:</strong> Regularly check blood counts during recovery.</li>
        </ul>
    </div>
    <div>
        <h3>Foods to Eat:</h3>
        <ul>
            <li><strong>Anti-Inflammatory Foods:</strong> Fatty fish, olive oil, flaxseeds, and walnuts.</li>
            <li><strong>Antioxidant-Rich Foods:</strong> Berries, leafy greens, and nuts.</li>
            <li><strong>Fiber-Rich Foods:</strong> Whole grains, vegetables, and legumes.</li>
            <li><strong>Vitamin C-Rich Foods:</strong> Citrus fruits, bell peppers, and broccoli.</li>
            <li><strong>Lean Proteins:</strong> Chicken, turkey, tofu, and legumes.</li>
        </ul>
    </div>
    <div>
        <h3>Example Meal Plan for High Monocytes:</h3>
        <ul>
            <li><strong>Breakfast:</strong> Oatmeal with chia seeds, walnuts, and blueberries.</li>
            <li><strong>Lunch:</strong> Grilled salmon with quinoa, steamed broccoli, and a salad with olive oil dressing.</li>
            <li><strong>Snack:</strong> A handful of almonds and an orange.</li>
            <li><strong>Dinner:</strong> Grilled chicken stir-fry with spinach, bell peppers, and carrots.</li>
        </ul>
    </div>
</div>
""")

    # Basophils (range: 0.5-1%)
        if values["Basophils"] < 0.5:
            advice.append("""
<div>
    <h2>Low Basophils (Basopenia)</h2>
    <div>
        <h3>Root Cause:</h3>
        <ul>
            <li><strong>Acute Infections:</strong> Bacterial or viral infections like influenza can temporarily decrease basophils.</li>
            <li><strong>Corticosteroid Use:</strong> Immunosuppressive medications suppress basophil production.</li>
            <li><strong>Allergic Reactions:</strong> Basophils migrate to sites of inflammation, temporarily lowering circulation levels.</li>
            <li><strong>Severe Stress:</strong> Stress increases cortisol, which can reduce basophil counts.</li>
            <li><strong>Hyperthyroidism:</strong> An overactive thyroid alters immune system function, reducing basophil levels.</li>
            <li><strong>Bone Marrow Disorders:</strong> Conditions like aplastic anemia or leukemia affect basophil production.</li>
            <li><strong>Pregnancy:</strong> Hormonal changes in later pregnancy stages may decrease basophil counts.</li>
        </ul>
    </div>
    <div>
        <h3>Tips:</h3>
        <ul>
            <li><strong>Review Medications:</strong> Consult your doctor about adjusting corticosteroids or immunosuppressants.</li>
            <li><strong>Manage Stress:</strong> Practice relaxation techniques such as yoga, meditation, or deep breathing exercises.</li>
            <li><strong>Address Thyroid Disorders:</strong> Treat hyperthyroidism to restore normal basophil levels.</li>
            <li><strong>Monitor for Infections:</strong> Properly treat active infections to help restore basophil levels.</li>
            <li><strong>Nutritional Support:</strong> Consume a balanced diet rich in vitamins and minerals to support immune function.</li>
        </ul>
    </div>
    <div>
        <h3>Foods to Eat:</h3>
        <ul>
            <li><strong>Vitamin C-Rich Foods:</strong> Citrus fruits, strawberries, bell peppers, and broccoli.</li>
            <li><strong>Protein-Rich Foods:</strong> Lean meats, fish, tofu, and legumes.</li>
            <li><strong>Zinc-Rich Foods:</strong> Shellfish, nuts, seeds, and lean meats.</li>
            <li><strong>Magnesium-Rich Foods:</strong> Nuts, seeds, spinach, and whole grains.</li>
        </ul>
    </div>
    <div>
        <h3>Example Meal Plan for Low Basophils:</h3>
        <ul>
            <li><strong>Breakfast:</strong> Scrambled eggs with spinach and whole-grain toast.</li>
            <li><strong>Lunch:</strong> Grilled chicken with quinoa and steamed broccoli.</li>
            <li><strong>Snack:</strong> A handful of almonds and an orange.</li>
            <li><strong>Dinner:</strong> Grilled salmon with roasted sweet potatoes and steamed broccoli.</li>
        </ul>
    </div>
</div>
""")
        elif values["Basophils"] > 2:
            advice.append("""
<div>
    <h2>High Basophils (Basophilia)</h2>
    <div>
        <h3>Root Cause:</h3>
        <ul>
            <li><strong>Allergic Reactions:</strong> Conditions like asthma, hay fever, or food allergies can elevate basophils.</li>
            <li><strong>Chronic Inflammatory Diseases:</strong> Rheumatoid arthritis, ulcerative colitis, or Crohn's disease can cause chronic inflammation.</li>
            <li><strong>Myeloproliferative Disorders:</strong> Conditions like chronic myelogenous leukemia (CML) increase basophil production.</li>
            <li><strong>Hypothyroidism:</strong> An underactive thyroid can elevate basophils as part of immune response dysregulation.</li>
            <li><strong>Infections:</strong> Chronic infections like tuberculosis may cause elevated basophils.</li>
            <li><strong>Chronic Urticaria:</strong> Persistent hives elevate basophils due to ongoing allergic reactions.</li>
            <li><strong>Pregnancy:</strong> Hormonal changes may lead to slightly elevated basophils.</li>
        </ul>
    </div>
    <div>
        <h3>Tips:</h3>
        <ul>
            <li><strong>Identify and Treat Allergies:</strong> Manage allergies with antihistamines or corticosteroids.</li>
            <li><strong>Treat Chronic Inflammatory Diseases:</strong> Use immunosuppressants, corticosteroids, or biologics as recommended by your doctor.</li>
            <li><strong>Monitor for Myeloproliferative Disorders:</strong> If suspected, further tests and targeted therapies are necessary.</li>
            <li><strong>Thyroid Management:</strong> Thyroid hormone replacement therapy can normalize basophil levels.</li>
            <li><strong>Manage Infections:</strong> Treat chronic infections like tuberculosis with appropriate antimicrobial therapy.</li>
        </ul>
    </div>
    <div>
        <h3>Foods to Eat:</h3>
        <ul>
            <li><strong>Anti-Inflammatory Foods:</strong> Fatty fish, olive oil, flaxseeds, and walnuts.</li>
            <li><strong>Antioxidant-Rich Foods:</strong> Berries, leafy greens, and nuts.</li>
            <li><strong>Fiber-Rich Foods:</strong> Whole grains, vegetables, and legumes.</li>
            <li><strong>Vitamin C-Rich Foods:</strong> Citrus fruits, bell peppers, and broccoli.</li>
            <li><strong>Lean Proteins:</strong> Chicken, turkey, tofu, and legumes.</li>
        </ul>
    </div>
    <div>
        <h3>Example Meal Plan for High Basophils:</h3>
        <ul>
            <li><strong>Breakfast:</strong> Oatmeal with chia seeds, walnuts, and blueberries.</li>
            <li><strong>Lunch:</strong> Grilled salmon with quinoa, steamed broccoli, and a salad with olive oil dressing.</li>
            <li><strong>Snack:</strong> A handful of almonds and an orange.</li>
            <li><strong>Dinner:</strong> Grilled chicken stir-fry with spinach, bell peppers, and carrots.</li>
        </ul>
    </div>
</div>
""")


    # Absolute Neutrophil Count (range: 1.5-8.0 x10⁹/L) cells/cumm
        if values["Absolute Neutrophil Count"] < 2000:
            advice.append("""
<div>
    <h2>Low Absolute Neutrophil Count (Neutropenia)</h2>
    <div>
        <h3>Root Cause:</h3>
        <ul>
            <li><strong>Bone Marrow Disorders:</strong> Aplastic anemia, myelodysplastic syndromes, leukemia, or other conditions affecting bone marrow production.</li>
            <li><strong>Autoimmune Disorders:</strong> Diseases like lupus or rheumatoid arthritis where the immune system attacks neutrophils.</li>
            <li><strong>Infections:</strong> Viral infections like HIV, hepatitis, or influenza suppress neutrophil production.</li>
            <li><strong>Chemotherapy or Radiation:</strong> Cancer treatments suppress bone marrow function.</li>
            <li><strong>Medications:</strong> Drugs like antibiotics, antipsychotics, anticonvulsants, or immunosuppressants may lower neutrophil levels.</li>
            <li><strong>Vitamin Deficiencies:</strong> Deficiencies in folate, vitamin B12, or copper impair neutrophil production.</li>
            <li><strong>Severe Infections or Sepsis:</strong> Infections can rapidly deplete neutrophils.</li>
            <li><strong>Congenital Conditions:</strong> Conditions like cyclic or congenital neutropenia result in low counts.</li>
        </ul>
    </div>
    <div>
        <h3>Tips:</h3>
        <ul>
            <li><strong>Infection Precautions:</strong> Practice frequent hand washing, avoid sick individuals, and wear masks if needed.</li>
            <li><strong>Monitor for Infections:</strong> Seek immediate medical attention for symptoms of infection like fever or sore throat.</li>
            <li><strong>Avoid Certain Medications:</strong> If drugs are causing neutropenia, consult your doctor about alternatives.</li>
            <li><strong>Support Bone Marrow Health:</strong> Consume a diet rich in folate, vitamin B12, and copper.</li>
            <li><strong>Use of Growth Factors:</strong> In some cases, granulocyte-colony stimulating factors (G-CSF) may be prescribed to boost neutrophil production.</li>
        </ul>
    </div>
    <div>
        <h3>Foods to Eat:</h3>
        <ul>
            <li><strong>Folate-Rich Foods:</strong> Leafy greens, citrus fruits, beans, peas, lentils, and fortified cereals.</li>
            <li><strong>Vitamin B12-Rich Foods:</strong> Meat, poultry, fish, eggs, and dairy.</li>
            <li><strong>Copper-Rich Foods:</strong> Shellfish, nuts, seeds, whole grains, and legumes.</li>
            <li><strong>Protein-Rich Foods:</strong> Lean meats, fish, tofu, and legumes to support immune health.</li>
        </ul>
    </div>
    <div>
        <h3>Example Meal Plan for Low ANC:</h3>
        <ul>
            <li><strong>Breakfast:</strong> Scrambled eggs with spinach and whole-grain toast (rich in vitamin B12 and folate).</li>
            <li><strong>Lunch:</strong> Grilled chicken with quinoa and leafy greens (rich in protein, vitamin B12, and folate).</li>
            <li><strong>Snack:</strong> A handful of almonds and an orange (rich in vitamin C).</li>
            <li><strong>Dinner:</strong> Baked salmon with roasted sweet potatoes and steamed broccoli (rich in vitamin B12, copper, and protein).</li>
        </ul>
    </div>
</div>
""")
        elif values["Absolute Neutrophil Count"] > 7000:
            advice.append("""
<div>
    <h2>High Absolute Neutrophil Count (Neutrophilia)</h2>
    <div>
        <h3>Root Cause:</h3>
        <ul>
            <li><strong>Infections:</strong> Acute bacterial infections like pneumonia, appendicitis, or urinary tract infections can elevate neutrophil counts.</li>
            <li><strong>Inflammatory Conditions:</strong> Chronic diseases like rheumatoid arthritis or inflammatory bowel disease (IBD).</li>
            <li><strong>Stress or Trauma:</strong> Physical or emotional stress, surgery, or trauma can elevate neutrophils via cortisol release.</li>
            <li><strong>Medications:</strong> Drugs like corticosteroids, epinephrine, or lithium can stimulate neutrophil production.</li>
            <li><strong>Smoking:</strong> Chronic smoking induces an inflammatory response, raising neutrophil counts.</li>
            <li><strong>Leukemia or Myeloproliferative Disorders:</strong> Disorders like chronic myelogenous leukemia (CML) cause excessive neutrophil production.</li>
            <li><strong>Tissue Damage:</strong> Burns, heart attacks, or trauma can cause elevated neutrophils as part of healing.</li>
        </ul>
    </div>
    <div>
        <h3>Tips:</h3>
        <ul>
            <li><strong>Identify and Treat Infections:</strong> Use antibiotics or antivirals as needed to treat infections.</li>
            <li><strong>Manage Inflammatory Conditions:</strong> Use corticosteroids, immunosuppressants, or biologics to reduce inflammation.</li>
            <li><strong>Minimize Stress:</strong> Practice stress-reduction techniques like yoga, meditation, or relaxation exercises.</li>
            <li><strong>Avoid Smoking:</strong> Quitting smoking reduces inflammation and normalizes neutrophil levels.</li>
            <li><strong>Monitor for Hematologic Conditions:</strong> Suspected blood disorders may require diagnostic tests and targeted therapies.</li>
        </ul>
    </div>
    <div>
        <h3>Foods to Eat:</h3>
        <ul>
            <li><strong>Anti-Inflammatory Foods:</strong> Fatty fish, olive oil, walnuts, and flaxseeds to reduce inflammation.</li>
            <li><strong>Antioxidant-Rich Foods:</strong> Berries, leafy greens, and nuts to combat oxidative stress.</li>
            <li><strong>Fiber-Rich Foods:</strong> Whole grains, vegetables, and legumes to support gut health.</li>
            <li><strong>Vitamin C-Rich Foods:</strong> Citrus fruits, bell peppers, and broccoli to boost immunity.</li>
        </ul>
    </div>
    <div>
        <h3>Example Meal Plan for High ANC:</h3>
        <ul>
            <li><strong>Breakfast:</strong> Oatmeal with chia seeds, walnuts, and blueberries (rich in antioxidants and fiber).</li>
            <li><strong>Lunch:</strong> Grilled salmon with quinoa, steamed broccoli, and a side salad with olive oil dressing (anti-inflammatory foods).</li>
            <li><strong>Snack:</strong> A handful of almonds and an orange (rich in vitamin C).</li>
            <li><strong>Dinner:</strong> Grilled chicken stir-fry with spinach, bell peppers, and carrots (rich in vitamin C and fiber).</li>
        </ul>
    </div>
</div>
""")

    # Absolute Lymphocyte Count (range: 1.0-4.0 x10⁹/L)
        if values["Absolute Lymphocyte Count"] < 1000:
            advice.append("""
<div>
    <h2>Low Absolute Lymphocyte Count (Lymphocytopenia)</h2>
    <div>
        <h3>Root Cause:</h3>
        <ul>
            <li><strong>Infections:</strong> Viral infections like HIV, hepatitis, influenza, and measles can cause low lymphocyte counts.</li>
            <li><strong>Autoimmune Disorders:</strong> Conditions such as lupus, rheumatoid arthritis, or Sjogren's syndrome can lead to lymphocyte destruction.</li>
            <li><strong>Bone Marrow Disorders:</strong> Aplastic anemia, leukemia, or myelodysplastic syndromes can impair lymphocyte production.</li>
            <li><strong>Immunosuppressive Medications:</strong> Drugs such as corticosteroids, chemotherapy, or immunosuppressants can reduce lymphocyte production.</li>
            <li><strong>Malnutrition:</strong> Severe deficiencies in protein, zinc, folate, or vitamin B12 impair immune function.</li>
            <li><strong>Radiation Therapy:</strong> Radiation exposure reduces lymphocyte production in the bone marrow.</li>
            <li><strong>Chronic Stress:</strong> Prolonged stress elevates cortisol, suppressing lymphocyte production.</li>
            <li><strong>Congenital Immunodeficiencies:</strong> Genetic disorders, such as DiGeorge syndrome, can cause lymphocytopenia.</li>
        </ul>
    </div>
    <div>
        <h3>Tips:</h3>
        <ul>
            <li><strong>Monitor for Infections:</strong> Avoid exposure to sick individuals and seek prompt treatment for infections.</li>
            <li><strong>Boost Immune Function:</strong> Support the immune system by addressing underlying conditions and avoiding immunosuppressive drugs if possible.</li>
            <li><strong>Address Nutritional Deficiencies:</strong> Maintain a diet rich in zinc, folate, and vitamin B12.</li>
            <li><strong>Stress Management:</strong> Use relaxation techniques such as yoga, meditation, or deep breathing exercises.</li>
            <li><strong>Regular Monitoring:</strong> Periodic blood tests can help track lymphocyte levels and guide treatment adjustments.</li>
        </ul>
    </div>
    <div>
        <h3>Foods to Eat:</h3>
        <ul>
            <li><strong>Vitamin C-Rich Foods:</strong> Citrus fruits, strawberries, bell peppers, and broccoli.</li>
            <li><strong>Zinc-Rich Foods:</strong> Shellfish, lean meats, legumes, nuts, and seeds.</li>
            <li><strong>Folate-Rich Foods:</strong> Leafy greens, citrus fruits, beans, peas, and lentils.</li>
            <li><strong>Protein-Rich Foods:</strong> Lean meats, poultry, fish, tofu, and legumes.</li>
            <li><strong>Vitamin B12-Rich Foods:</strong> Meat, poultry, fish, eggs, and dairy.</li>
        </ul>
    </div>
    <div>
        <h3>Example Meal Plan for Low Absolute Lymphocyte Count:</h3>
        <ul>
            <li><strong>Breakfast:</strong> Scrambled eggs with spinach and whole-grain toast (rich in vitamin B12 and folate).</li>
            <li><strong>Lunch:</strong> Grilled chicken with quinoa and leafy greens (rich in protein, vitamin B12, and folate).</li>
            <li><strong>Snack:</strong> A handful of almonds and an orange (rich in vitamin C).</li>
            <li><strong>Dinner:</strong> Baked salmon with roasted sweet potatoes and steamed broccoli (rich in vitamin B12, protein, and zinc).</li>
        </ul>
    </div>
</div>
""")
        elif values["Absolute Lymphocyte Count"] > 3000:
            advice.append("""
<div>
    <h2>High Absolute Lymphocyte Count (Lymphocytosis)</h2>
    <div>
        <h3>Root Cause:</h3>
        <ul>
            <li><strong>Infections:</strong> Viral infections like mononucleosis, hepatitis, or cytomegalovirus, or bacterial infections like tuberculosis.</li>
            <li><strong>Autoimmune Disorders:</strong> Chronic conditions such as multiple sclerosis or rheumatoid arthritis can increase lymphocytes.</li>
            <li><strong>Chronic Lymphocytic Leukemia (CLL):</strong> Malignant overproduction of lymphocytes in leukemia.</li>
            <li><strong>Lymphoma:</strong> Certain types of lymphoma can elevate lymphocyte counts.</li>
            <li><strong>Stress:</strong> Physical or emotional stress can cause temporary lymphocyte elevation.</li>
            <li><strong>Smoking:</strong> Chronic smoking induces inflammation and lymphocyte elevation.</li>
            <li><strong>Medication Response:</strong> Immune-stimulating drugs can increase lymphocyte counts.</li>
        </ul>
    </div>
    <div>
        <h3>Tips:</h3>
        <ul>
            <li><strong>Identify the Underlying Cause:</strong> Seek medical evaluation to determine and address the cause of lymphocytosis.</li>
            <li><strong>Manage Chronic Conditions:</strong> Treat infections or chronic inflammatory diseases to normalize lymphocyte levels.</li>
            <li><strong>Monitor for Blood Disorders:</strong> Diagnostic tests may be necessary for conditions like leukemia or lymphoma.</li>
            <li><strong>Avoid Smoking:</strong> Quitting smoking reduces chronic inflammation.</li>
            <li><strong>Stress Management:</strong> Incorporate relaxation techniques to manage stress-related lymphocytosis.</li>
        </ul>
    </div>
    <div>
        <h3>Foods to Eat:</h3>
        <ul>
            <li><strong>Anti-Inflammatory Foods:</strong> Fatty fish, olive oil, walnuts, and flaxseeds.</li>
            <li><strong>Antioxidant-Rich Foods:</strong> Berries, leafy greens, and nuts.</li>
            <li><strong>Fiber-Rich Foods:</strong> Whole grains, vegetables, and legumes.</li>
            <li><strong>Vitamin C-Rich Foods:</strong> Citrus fruits, bell peppers, and broccoli.</li>
            <li><strong>Probiotic-Rich Foods:</strong> Yogurt, kefir, and fermented foods.</li>
        </ul>
    </div>
    <div>
        <h3>Example Meal Plan for High Absolute Lymphocyte Count:</h3>
        <ul>
            <li><strong>Breakfast:</strong> Oatmeal with chia seeds, walnuts, and blueberries (rich in antioxidants and fiber).</li>
            <li><strong>Lunch:</strong> Grilled salmon with quinoa, steamed broccoli, and a salad with olive oil dressing.</li>
            <li><strong>Snack:</strong> A handful of almonds and an orange (rich in vitamin C).</li>
            <li><strong>Dinner:</strong> Grilled chicken stir-fry with spinach, bell peppers, and carrots (rich in vitamin C and fiber).</li>
        </ul>
    </div>
</div>
""")

    # Absolute Eosinophil Count (range: 0.02-0.5 x10⁹/L)
        if values["Absolute Eosinophil Count"] < 20:
            advice.append("""
<div>
    <h2>Low Absolute Eosinophil Count (Eosinopenia)</h2>
    <div>
        <h3>Root Cause:</h3>
        <ul>
            <li><strong>Acute Infections:</strong> Severe bacterial infections like sepsis can reduce eosinophil levels.</li>
            <li><strong>Corticosteroid Use:</strong> Medications like prednisone suppress eosinophil production.</li>
            <li><strong>Cushing's Syndrome:</strong> Excess cortisol in the body suppresses eosinophil counts.</li>
            <li><strong>Stress:</strong> Prolonged physical or emotional stress elevates cortisol, reducing eosinophil levels.</li>
            <li><strong>Bone Marrow Suppression:</strong> Disorders like aplastic anemia or leukemia impair eosinophil production.</li>
            <li><strong>Acute Inflammatory Disorders:</strong> Conditions like trauma, infections, or shock can deplete eosinophils.</li>
            <li><strong>Severe Protein Malnutrition:</strong> Nutritional deficiencies can suppress immune function.</li>
        </ul>
    </div>
    <div>
        <h3>Tips:</h3>
        <ul>
            <li><strong>Infection Management:</strong> Address infections promptly to reduce immune system strain.</li>
            <li><strong>Medication Adjustment:</strong> Discuss alternatives with your doctor if corticosteroids are causing low eosinophils.</li>
            <li><strong>Bone Marrow Monitoring:</strong> Regular testing for bone marrow disorders may be necessary.</li>
            <li><strong>Stress Reduction:</strong> Practice yoga, meditation, or relaxation techniques to lower stress levels.</li>
            <li><strong>Nutritional Support:</strong> Consume a balanced diet rich in protein, vitamins, and minerals.</li>
        </ul>
    </div>
    <div>
        <h3>Foods to Eat:</h3>
        <ul>
            <li><strong>Protein-Rich Foods:</strong> Lean meats, poultry, fish, tofu, and legumes.</li>
            <li><strong>Vitamin B12 and Folate-Rich Foods:</strong> Eggs, dairy, spinach, kale, beans, and lentils.</li>
            <li><strong>Zinc-Rich Foods:</strong> Shellfish, red meat, beans, nuts, and seeds.</li>
            <li><strong>Healthy Fats:</strong> Olive oil, avocados, and fatty fish like salmon.</li>
        </ul>
    </div>
    <div>
        <h3>Example Meal Plan for Low Absolute Eosinophil Count:</h3>
        <ul>
            <li><strong>Breakfast:</strong> Scrambled eggs with spinach and whole-grain toast (rich in vitamin B12 and folate).</li>
            <li><strong>Lunch:</strong> Grilled chicken with quinoa and leafy greens (rich in protein, folate, and zinc).</li>
            <li><strong>Snack:</strong> A handful of almonds and a boiled egg (rich in protein and zinc).</li>
            <li><strong>Dinner:</strong> Baked salmon with roasted sweet potatoes and steamed broccoli (rich in protein, zinc, and healthy fats).</li>
        </ul>
    </div>
</div>
""")
        elif values["Absolute Eosinophil Count"] > 500:
            advice.append("""
<div>
    <h2>High Absolute Eosinophil Count (Eosinophilia)</h2>
    <div>
        <h3>Root Cause:</h3>
        <ul>
            <li><strong>Allergic Reactions:</strong> Asthma, hay fever, eczema, or rhinitis can increase eosinophils.</li>
            <li><strong>Parasitic Infections:</strong> Parasites like hookworms, roundworms, and malaria trigger eosinophilia.</li>
            <li><strong>Autoimmune Diseases:</strong> Conditions like rheumatoid arthritis or inflammatory bowel disease can elevate eosinophils.</li>
            <li><strong>Eosinophilic Disorders:</strong> Rare conditions like eosinophilic esophagitis or pneumonia.</li>
            <li><strong>Chronic Infections:</strong> Long-term fungal infections, tuberculosis, or certain viral infections.</li>
            <li><strong>Drug Reactions:</strong> Medications like NSAIDs or antibiotics can induce eosinophilia.</li>
            <li><strong>Cancer:</strong> Lymphomas or certain leukemias may cause high eosinophil levels.</li>
            <li><strong>Hypereosinophilic Syndrome:</strong> Persistently high eosinophil levels affecting organs.</li>
        </ul>
    </div>
    <div>
        <h3>Tips:</h3>
        <ul>
            <li><strong>Manage Allergies:</strong> Antihistamines, corticosteroids, or allergy shots may help control symptoms.</li>
            <li><strong>Treat Parasitic Infections:</strong> Use antiparasitic medications to resolve infections and normalize eosinophils.</li>
            <li><strong>Monitor Autoimmune Disorders:</strong> Use immunosuppressive medications or biologics as advised by your doctor.</li>
            <li><strong>Medication Adjustment:</strong> Discuss alternatives with your doctor if medications are causing eosinophilia.</li>
            <li><strong>Avoid Environmental Triggers:</strong> Minimize exposure to allergens like pollen, dust, or pet dander.</li>
        </ul>
    </div>
    <div>
        <h3>Foods to Eat:</h3>
        <ul>
            <li><strong>Anti-Inflammatory Foods:</strong> Fatty fish, olive oil, walnuts, and flaxseeds.</li>
            <li><strong>Antioxidant-Rich Foods:</strong> Berries, leafy greens, and nuts.</li>
            <li><strong>Fiber-Rich Foods:</strong> Whole grains, vegetables, and legumes.</li>
            <li><strong>Probiotic-Rich Foods:</strong> Yogurt, kefir, and fermented foods.</li>
            <li><strong>Vitamin C-Rich Foods:</strong> Citrus fruits, bell peppers, and broccoli.</li>
        </ul>
    </div>
    <div>
        <h3>Example Meal Plan for High Absolute Eosinophil Count:</h3>
        <ul>
            <li><strong>Breakfast:</strong> Oatmeal with chia seeds, walnuts, and blueberries (rich in antioxidants and fiber).</li>
            <li><strong>Lunch:</strong> Grilled salmon with quinoa, steamed broccoli, and a salad with olive oil dressing.</li>
            <li><strong>Snack:</strong> A handful of almonds and an orange (rich in vitamin C).</li>
            <li><strong>Dinner:</strong> Grilled chicken stir-fry with spinach, bell peppers, and carrots (rich in vitamin C and fiber).</li>
        </ul>
    </div>
</div>
""")

    # Absolute Monocyte Count (range: 0.1-1.0 x10⁹/L)
        if values["Absolute Monocyte Count"] < 200:
            advice.append("""
<div>
    <h2>Low Absolute Monocyte Count (Monocytopenia)</h2>
    <div>
        <h3>Root Cause:</h3>
        <ul>
            <li><strong>Acute Infections:</strong> Initial stages of viral infections (e.g., HIV, hepatitis) can cause a temporary decrease in monocyte count.</li>
            <li><strong>Bone Marrow Disorders:</strong> Conditions like aplastic anemia or leukemia can impair monocyte production.</li>
            <li><strong>Corticosteroid Use:</strong> Medications such as prednisone suppress monocyte production.</li>
            <li><strong>Chemotherapy or Radiation Therapy:</strong> These treatments may impair bone marrow function.</li>
            <li><strong>Severe Malnutrition:</strong> Deficiencies in protein, vitamin B12, folate, and minerals can reduce monocyte production.</li>
            <li><strong>Autoimmune Diseases:</strong> Disorders like lupus or rheumatoid arthritis can cause immune dysregulation and low monocyte counts.</li>
            <li><strong>Congenital or Genetic Disorders:</strong> Rare genetic conditions such as hereditary neutropenia can lead to monocytopenia.</li>
        </ul>
    </div>
    <div>
        <h3>Tips:</h3>
        <ul>
            <li><strong>Monitor for Infections:</strong> Stay vigilant for signs of infections as low monocyte levels increase vulnerability.</li>
            <li><strong>Review Medications:</strong> Consult your doctor if corticosteroids or chemotherapy are affecting your monocyte levels.</li>
            <li><strong>Boost Nutritional Intake:</strong> Include essential nutrients like protein, vitamin B12, folate, and iron in your diet.</li>
            <li><strong>Bone Marrow Monitoring:</strong> Conduct regular medical follow-ups to assess bone marrow health if disorders are suspected.</li>
            <li><strong>Stress Management:</strong> Engage in stress-reduction techniques like meditation, yoga, or exercise.</li>
        </ul>
    </div>
    <div>
        <h3>Foods to Eat:</h3>
        <ul>
            <li><strong>Protein-Rich Foods:</strong> Lean meats, poultry, fish, eggs, tofu, and legumes.</li>
            <li><strong>Vitamin B12 and Folate-Rich Foods:</strong> Meat, dairy, spinach, kale, beans, and lentils.</li>
            <li><strong>Iron-Rich Foods:</strong> Red meat, lentils, spinach, and poultry.</li>
            <li><strong>Zinc-Rich Foods:</strong> Shellfish, lean meats, nuts, and seeds.</li>
            <li><strong>Healthy Fats:</strong> Olive oil, avocados, and fatty fish like salmon.</li>
        </ul>
    </div>
    <div>
        <h3>Example Meal Plan for Low Absolute Monocyte Count:</h3>
        <ul>
            <li><strong>Breakfast:</strong> Scrambled eggs with spinach and whole-grain toast (rich in protein, vitamin B12, and folate).</li>
            <li><strong>Lunch:</strong> Grilled chicken with quinoa and leafy greens (rich in protein, folate, and zinc).</li>
            <li><strong>Snack:</strong> A handful of almonds and a boiled egg (rich in protein and zinc).</li>
            <li><strong>Dinner:</strong> Baked salmon with roasted sweet potatoes and steamed broccoli (rich in protein, zinc, and healthy fats).</li>
        </ul>
    </div>
</div>
""")
        elif values["Absolute Monocyte Count"] > 1000:
            advice.append("""
<div>
    <h2>High Absolute Monocyte Count (Monocytosis)</h2>
    <div>
        <h3>Root Cause:</h3>
        <ul>
            <li><strong>Chronic Infections:</strong> Tuberculosis, brucellosis, or fungal infections can chronically elevate monocytes.</li>
            <li><strong>Inflammatory Diseases:</strong> Conditions like IBD, lupus, or rheumatoid arthritis cause chronic inflammation and high monocyte counts.</li>
            <li><strong>Leukemia and Lymphoma:</strong> Certain cancers result in marked increases in monocyte levels.</li>
            <li><strong>Recovery from Acute Infection:</strong> Monocytes can remain elevated during recovery phases.</li>
            <li><strong>Autoimmune Diseases:</strong> Disorders like sarcoidosis or vasculitis can increase monocyte production.</li>
            <li><strong>Myeloproliferative Disorders:</strong> Conditions like chronic myelomonocytic leukemia (CMML).</li>
            <li><strong>Stress:</strong> Physical or emotional stress triggers higher monocyte production.</li>
            <li><strong>Tissue Damage or Inflammation:</strong> Monocyte levels rise during healing processes.</li>
        </ul>
    </div>
    <div>
        <h3>Tips:</h3>
        <ul>
            <li><strong>Identify the Underlying Cause:</strong> Work with your doctor to diagnose and treat the root cause.</li>
            <li><strong>Treat Chronic Infections:</strong> Use appropriate antimicrobial or antifungal treatments.</li>
            <li><strong>Manage Inflammatory Diseases:</strong> Medications like immunosuppressants or biologics can help.</li>
            <li><strong>Monitor for Blood Cancers:</strong> Perform diagnostic tests if blood cancers are suspected.</li>
            <li><strong>Reduce Stress:</strong> Practice relaxation techniques to lower inflammation and monocyte counts.</li>
        </ul>
    </div>
    <div>
        <h3>Foods to Eat:</h3>
        <ul>
            <li><strong>Anti-Inflammatory Foods:</strong> Fatty fish, olive oil, walnuts, and flaxseeds.</li>
            <li><strong>Antioxidant-Rich Foods:</strong> Berries, leafy greens, and nuts.</li>
            <li><strong>Fiber-Rich Foods:</strong> Whole grains, broccoli, cauliflower, and legumes.</li>
            <li><strong>Probiotic-Rich Foods:</strong> Yogurt, kefir, and fermented foods.</li>
            <li><strong>Vitamin C-Rich Foods:</strong> Citrus fruits, bell peppers, and broccoli.</li>
        </ul>
    </div>
    <div>
        <h3>Example Meal Plan for High Absolute Monocyte Count:</h3>
        <ul>
            <li><strong>Breakfast:</strong> Oatmeal with chia seeds, walnuts, and blueberries (rich in antioxidants and fiber).</li>
            <li><strong>Lunch:</strong> Grilled salmon with quinoa, steamed broccoli, and a salad with olive oil dressing.</li>
            <li><strong>Snack:</strong> A handful of almonds and an orange (rich in vitamin C).</li>
            <li><strong>Dinner:</strong> Grilled chicken stir-fry with spinach, bell peppers, and carrots (rich in vitamin C and fiber).</li>
        </ul>
    </div>
</div>
""")

    # Platelet Count (range: 150,000-410,000 cells/μL)
        if values["Platelet Count"] < 150000:
            advice.append("""
<h2>Low Platelet Count (Thrombocytopenia)</h2>
<div>
    <h3>Root Cause:</h3>
    <ul>
        <li><b>Bone Marrow Disorders:</b> Conditions such as aplastic anemia, leukemia, or myelodysplastic syndromes can impair platelet production.</li>
        <li><b>Autoimmune Diseases:</b> Diseases like lupus, rheumatoid arthritis, or idiopathic thrombocytopenic purpura (ITP) can cause immune destruction of platelets.</li>
        <li><b>Viral Infections:</b> Infections such as dengue, HIV, hepatitis C, or Epstein-Barr virus (EBV) can reduce platelet counts.</li>
        <li><b>Medications:</b> Certain drugs (e.g., chemotherapy agents, heparin, some antibiotics) may decrease platelet production or cause platelet destruction.</li>
        <li><b>Nutritional Deficiencies:</b> Deficiencies in vitamin B12, folate, or iron can impair platelet production.</li>
        <li><b>Alcohol Consumption:</b> Chronic alcohol use can suppress bone marrow activity, leading to lower platelet counts.</li>
        <li><b>Sepsis or Infections:</b> Severe systemic infections can lead to disseminated intravascular coagulation (DIC), consuming platelets.</li>
        <li><b>Pregnancy:</b> Some pregnant women may experience mild decreases in platelet count, especially in the third trimester.</li>
        <li><b>Hypersplenism:</b> An enlarged spleen can sequester platelets, leading to low levels in the bloodstream.</li>
    </ul>
</div>
<div>
    <h3>Tips:</h3>
    <ul>
        <li>Monitor for unusual bleeding or bruising and avoid activities that could result in injuries.</li>
        <li>Review medications with a healthcare provider to check for drugs that may lower platelet counts.</li>
        <li>Address infections with appropriate treatments, such as antivirals or antibiotics.</li>
        <li>Consume a balanced diet rich in vitamin B12, folate, and iron to support platelet production.</li>
        <li>Avoid alcohol, as it suppresses bone marrow activity.</li>
        <li>If a bone marrow disorder is suspected, follow up with regular tests and check-ups.</li>
    </ul>
</div>
<div>
    <h3>Foods to Eat:</h3>
    <ul>
        <li><b>Iron-Rich Foods:</b> Red meat, poultry, fish, beans, lentils, and spinach.</li>
        <li><b>Folate-Rich Foods:</b> Leafy greens (kale, spinach), citrus fruits, avocados, and legumes.</li>
        <li><b>Vitamin B12-Rich Foods:</b> Meat, eggs, dairy, and fortified cereals.</li>
        <li><b>Vitamin C-Rich Foods:</b> Citrus fruits (oranges, lemons), strawberries, and bell peppers.</li>
        <li><b>Healthy Fats:</b> Olive oil, avocado, and nuts to reduce inflammation and support health.</li>
    </ul>
</div>
<div>
    <h3>Example Meal Plan for Low Platelet Count:</h3>
    <ul>
        <li><b>Breakfast:</b> Scrambled eggs with spinach, whole-grain toast, and a glass of orange juice (rich in vitamin B12, folate, and vitamin C).</li>
        <li><b>Lunch:</b> Grilled chicken with quinoa, steamed broccoli, and a side salad with avocado (rich in protein, iron, and healthy fats).</li>
        <li><b>Snack:</b> A handful of almonds and a boiled egg (rich in protein and healthy fats).</li>
        <li><b>Dinner:</b> Baked salmon with roasted sweet potatoes and steamed kale (rich in vitamin B12, folate, and healthy fats).</li>
    </ul>
</div>
""")
        elif values["Platelet Count"] > 410000:
            advice.append("""
<h2>High Platelet Count (Thrombocytosis)</h2>
<div>
    <h3>Root Cause:</h3>
    <ul>
        <li><b>Reactive (Secondary) Thrombocytosis:</b> Response to conditions like infections, inflammatory disorders, or trauma.</li>
        <li><b>Iron Deficiency Anemia:</b> Iron deficiency can increase platelet count as a compensatory mechanism.</li>
        <li><b>Myeloproliferative Disorders:</b> Disorders such as essential thrombocythemia or polycythemia vera can cause persistently high platelet counts.</li>
        <li><b>Cancer:</b> Certain cancers (lung, gastrointestinal, ovarian) can lead to thrombocytosis.</li>
        <li><b>Splenectomy:</b> Removal of the spleen can cause prolonged increases in platelet levels.</li>
    </ul>
</div>
<div>
    <h3>Tips:</h3>
    <ul>
        <li>Identify and treat underlying conditions like infections or iron deficiency.</li>
        <li>Monitor for clotting risks, as high platelet counts increase the likelihood of clots.</li>
        <li>Avoid smoking, which can raise the risk of clot formation.</li>
        <li>Exercise regularly to improve circulation under medical guidance.</li>
        <li>In cases of primary thrombocytosis, medications like low-dose aspirin or hydroxyurea may be prescribed.</li>
    </ul>
</div>
<div>
    <h3>Foods to Eat:</h3>
    <ul>
        <li><b>Anti-Inflammatory Foods:</b> Fatty fish, flaxseeds, walnuts, and olive oil to reduce inflammation.</li>
        <li><b>Vitamin E-Rich Foods:</b> Nuts (almonds, hazelnuts), spinach, and avocados to improve circulation.</li>
        <li><b>Ginger and Turmeric:</b> These have natural anti-inflammatory and blood-thinning properties.</li>
        <li><b>Fruits and Vegetables:</b> Berries, citrus fruits, broccoli, and kale to promote vascular health.</li>
        <li><b>Whole Grains:</b> Oats, brown rice, and quinoa to support cardiovascular health.</li>
    </ul>
</div>
<div>
    <h3>Example Meal Plan for High Platelet Count:</h3>
    <ul>
        <li><b>Breakfast:</b> Oatmeal with chia seeds, walnuts, and blueberries (rich in omega-3s and antioxidants).</li>
        <li><b>Lunch:</b> Grilled salmon with quinoa, steamed broccoli, and a side salad with olive oil and turmeric dressing.</li>
        <li><b>Snack:</b> A handful of almonds and avocado slices (rich in vitamin E and healthy fats).</li>
        <li><b>Dinner:</b> Stir-fried tofu with spinach, bell peppers, and ginger (rich in anti-inflammatory compounds).</li>
    </ul>
</div>
""")

    # Erythrocyte Sedimentation Rate (range: 0-20 mm/hr)
        if values["Erythrocyte Sedimentation Rate"] < 0:
            advice.append("""
<h2>Low Erythrocyte Sedimentation Rate (ESR)</h2>
<div>
    <h3>Root Cause:</h3>
    <ul>
        <li><b>Normal Variation:</b> A low ESR can sometimes be a normal finding, especially in healthy individuals, as the rate is influenced by various factors such as age, sex, and individual health status.</li>
        <li><b>Polycythemia Vera:</b> This is a condition where there is an overproduction of red blood cells, which increases blood viscosity and can lead to a lower ESR.</li>
        <li><b>Hyperviscosity Syndromes:</b> Conditions that cause thickened blood, such as Waldenström macroglobulinemia or multiple myeloma, can reduce the ESR.</li>
        <li><b>Low Fibrinogen Levels:</b> ESR is affected by proteins in the blood, particularly fibrinogen. Low fibrinogen levels, due to liver disease or certain genetic conditions, may result in a lower ESR.</li>
        <li><b>Leukocytosis:</b> A very high white blood cell count, such as in leukemia or other blood cancers, can reduce the ESR.</li>
        <li><b>Severe Anemia:</b> Certain types of severe anemia, particularly in the presence of low fibrinogen levels, may lead to a low ESR.</li>
        <li><b>Extremely Elevated Blood Sugar:</b> Hyperglycemia (very high blood sugar levels), which may be seen in uncontrolled diabetes, can lower the ESR.</li>
    </ul>
</div>
<div>
    <h3>Tips:</h3>
    <ul>
        <li>Monitor for symptoms related to potential underlying conditions, like polycythemia vera or hyperviscosity syndromes. Consult your doctor if you have symptoms of these disorders.</li>
        <li>If you have conditions known to increase blood viscosity, ensure proper treatment and management to prevent complications.</li>
        <li>Check liver function if low fibrinogen levels are suspected, as treatment may be needed to address liver abnormalities.</li>
        <li>Manage blood sugar levels through diet, exercise, and medication if hyperglycemia is suspected as the cause.</li>
        <li>Regular monitoring of blood tests and check-ups for individuals with blood disorders, anemia, or other conditions.</li>
    </ul>
</div>
<div>
    <h3>Foods to Eat:</h3>
    <ul>
        <li><b>Iron-Rich Foods:</b> Red meat, poultry, beans, lentils, and spinach to help with anemia and support overall blood health.</li>
        <li><b>Healthy Fats:</b> Olive oil, avocados, and fatty fish (salmon, mackerel) to reduce inflammation.</li>
        <li><b>Fiber-Rich Foods:</b> Whole grains, vegetables, and fruits to support overall health and help control blood sugar levels.</li>
        <li><b>Vitamin B12 and Folate-Rich Foods:</b> Animal products like meat, eggs, and dairy, as well as leafy greens, beans, and fortified cereals to help support red blood cell production and healthy blood viscosity.</li>
        <li><b>Antioxidant-Rich Foods:</b> Berries, citrus fruits, and leafy greens to support immune function and reduce inflammation.</li>
    </ul>
</div>
<div>
    <h3>Example Meal Plan for Low ESR:</h3>
    <ul>
        <li><b>Breakfast:</b> Scrambled eggs with spinach, whole-grain toast, and a glass of orange juice (rich in vitamin B12, folate, and vitamin C).</li>
        <li><b>Lunch:</b> Grilled chicken with quinoa, roasted sweet potatoes, and a side salad with avocado (rich in iron, vitamin B12, and healthy fats).</li>
        <li><b>Snack:</b> A handful of almonds and a boiled egg (rich in protein and healthy fats).</li>
        <li><b>Dinner:</b> Baked salmon with roasted broccoli and quinoa (rich in healthy fats, iron, and fiber).</li>
    </ul>
</div>
""")
        elif values["Erythrocyte Sedimentation Rate"] > 15:
            advice.append("""
<h2>High Erythrocyte Sedimentation Rate (ESR)</h2>
<div>
    <h3>Root Cause:</h3>
    <ul>
        <li><b>Chronic Inflammatory Diseases:</b> Conditions such as rheumatoid arthritis, lupus, inflammatory bowel disease (IBD), or vasculitis are commonly associated with an elevated ESR due to the body's ongoing inflammatory response.</li>
        <li><b>Infections:</b> Bacterial infections (e.g., tuberculosis, osteomyelitis) and some viral infections can cause a significant rise in ESR as part of the body's acute-phase response.</li>
        <li><b>Cancer:</b> Certain cancers, especially lymphomas, leukemia, and solid tumors, can cause an elevated ESR as the body responds to tumor activity and inflammation.</li>
        <li><b>Kidney Disease:</b> Chronic kidney disease, especially in its later stages, can lead to an elevated ESR due to inflammation and other systemic effects.</li>
        <li><b>Anemia:</b> Particularly in cases of iron-deficiency anemia or anemia of chronic disease, ESR can be elevated as the body responds to decreased red blood cells and tissue hypoxia.</li>
        <li><b>Pregnancy:</b> ESR is naturally elevated during pregnancy, particularly in the second and third trimesters, due to changes in the immune system and hormone levels.</li>
        <li><b>Temporal Arteritis:</b> A condition affecting the large arteries, particularly the temporal arteries, often causes a significantly high ESR, which is used as a diagnostic marker.</li>
        <li><b>Tissue Injury:</b> Severe trauma, surgery, or burns can cause an increase in ESR as part of the inflammatory healing process.</li>
    </ul>
</div>
<div>
    <h3>Tips:</h3>
    <ul>
        <li>Investigate the underlying cause with further diagnostic tests, such as imaging, biopsy, or blood cultures.</li>
        <li>Manage autoimmune or inflammatory conditions with medications like corticosteroids or disease-modifying antirheumatic drugs (DMARDs).</li>
        <li>Treat infections with appropriate antibiotics or antivirals.</li>
        <li>Follow targeted treatment plans for cancers causing elevated ESR, including chemotherapy, radiation, or immunotherapy.</li>
        <li>Monitor kidney function and manage chronic kidney disease through regular tests and blood pressure control.</li>
        <li>Treat the underlying cause of anemia to reduce ESR over time.</li>
        <li>Monitor ESR during pregnancy and discuss any abnormal increases with a doctor.</li>
    </ul>
</div>
<div>
    <h3>Foods to Eat:</h3>
    <ul>
        <li><b>Anti-Inflammatory Foods:</b> Omega-3-rich foods like fatty fish (salmon, sardines), flaxseeds, chia seeds, walnuts, and olive oil to help reduce inflammation.</li>
        <li><b>Fiber-Rich Foods:</b> Whole grains (oats, quinoa, brown rice), vegetables (spinach, kale, broccoli), and fruits (berries, apples) to support overall health and reduce inflammation.</li>
        <li><b>Antioxidant-Rich Foods:</b> Berries, citrus fruits, tomatoes, and leafy greens to combat oxidative stress and support immune health.</li>
        <li><b>Lean Protein:</b> Skinless poultry, lean beef, tofu, and legumes to support immune function without exacerbating inflammation.</li>
        <li><b>Spices with Anti-Inflammatory Properties:</b> Turmeric, ginger, and garlic can be added to meals to reduce inflammation.</li>
    </ul>
</div>
<div>
    <h3>Example Meal Plan for High ESR:</h3>
    <ul>
        <li><b>Breakfast:</b> Oatmeal with chia seeds, flaxseeds, and fresh blueberries (rich in omega-3s, fiber, and antioxidants).</li>
        <li><b>Lunch:</b> Grilled salmon with quinoa, spinach salad with olive oil, and a side of roasted sweet potatoes (anti-inflammatory foods and healthy fats).</li>
        <li><b>Snack:</b> A handful of walnuts and a green smoothie with spinach, ginger, and lemon (rich in anti-inflammatory compounds).</li>
        <li><b>Dinner:</b> Stir-fried tofu with broccoli, bell peppers, and turmeric (anti-inflammatory and antioxidant-rich).</li>
    </ul>
</div>
""")


    # Fasting Plasma Glucose (range: 70-100 mg/dL)
        if values["Fasting Plasma Glucose"] < 70:
            advice.append("""
<h2>Low Fasting Plasma Glucose (Hypoglycemia)</h2>
<div>
    <h3>Root Cause:</h3>
    <ul>
        <li><b>Insulin Overdose:</b> In people with diabetes, too much insulin or oral hypoglycemic medication can cause blood glucose levels to drop below normal levels.</li>
        <li><b>Prolonged Fasting or Starvation:</b> Extended periods without eating can lead to a significant drop in blood glucose, as the body runs out of readily available energy from food.</li>
        <li><b>Alcohol Consumption:</b> Excessive drinking, especially without eating, can impair the liver's ability to release glucose into the bloodstream, leading to hypoglycemia.</li>
        <li><b>Hormonal Imbalances:</b> Conditions like adrenal insufficiency, hypothyroidism, or growth hormone deficiencies can result in low blood sugar levels.</li>
        <li><b>Insulinoma:</b> A rare tumor of the pancreas that produces excessive insulin, leading to low blood sugar levels.</li>
        <li><b>Severe Liver Disease:</b> Liver disease, such as cirrhosis or hepatitis, can impair the liver’s ability to produce glucose, leading to low blood sugar levels.</li>
        <li><b>Malnutrition:</b> Lack of sufficient calories, particularly carbohydrates, can lead to hypoglycemia, especially in individuals with eating disorders or poor nutrition.</li>
        <li><b>Certain Medications:</b> Medications such as sulfonylureas (used in type 2 diabetes) and other drugs can increase the risk of low blood sugar.</li>
    </ul>
</div>
<div>
    <h3>Tips:</h3>
    <ul>
        <li>Eat Regular, Balanced Meals: Ensure regular meals and snacks throughout the day, especially those containing complex carbohydrates, protein, and healthy fats to stabilize blood sugar levels.</li>
        <li>Monitor Medication: If taking insulin or oral hypoglycemics, adjust the dosage with guidance from a healthcare provider to prevent hypoglycemia.</li>
        <li>Avoid Excessive Alcohol: Limit alcohol consumption, particularly on an empty stomach, to avoid hypoglycemia.</li>
        <li>Identify and Treat Underlying Conditions: Conditions like insulinoma, adrenal insufficiency, or liver disease may require specific treatment and monitoring.</li>
        <li>Carry Glucose: Always have a source of fast-acting carbohydrates, such as glucose tablets or sugary drinks, in case of an emergency hypoglycemic episode.</li>
    </ul>
</div>
<div>
    <h3>Foods to Eat:</h3>
    <ul>
        <li><b>Complex Carbohydrates:</b> Whole grains (brown rice, oats), sweet potatoes, and legumes (lentils, beans) to provide a steady source of glucose.</li>
        <li><b>Lean Protein:</b> Chicken, turkey, eggs, and tofu to stabilize blood sugar and prevent rapid drops.</li>
        <li><b>Healthy Fats:</b> Avocados, olive oil, and nuts to provide energy and slow down glucose absorption.</li>
        <li><b>Fibrous Vegetables:</b> Leafy greens (spinach, kale), bell peppers, and broccoli to provide essential nutrients without causing rapid blood sugar spikes.</li>
        <li><b>Fruits:</b> Berries, apples, and pears for natural sugars that can be combined with fiber to stabilize blood sugar levels.</li>
    </ul>
</div>
<div>
    <h3>Example Meal Plan for Low Fasting Plasma Glucose:</h3>
    <ul>
        <li><b>Breakfast:</b> Oatmeal with chia seeds, sliced almonds, and a handful of blueberries (complex carbs, fiber, and protein).</li>
        <li><b>Lunch:</b> Grilled chicken with quinoa and a side of roasted vegetables (balanced meal with protein and fiber).</li>
        <li><b>Snack:</b> A boiled egg with an apple (protein and natural sugars).</li>
        <li><b>Dinner:</b> Baked salmon with steamed broccoli and a small baked sweet potato (healthy fats, protein, and complex carbs).</li>
    </ul>
</div>
""")
        elif values["Fasting Plasma Glucose"] > 100:
            advice.append("""
<h2>High Fasting Plasma Glucose (Hyperglycemia)</h2>
<div>
    <h3>Root Cause:</h3>
    <ul>
        <li><b>Diabetes Mellitus:</b> The most common cause of high fasting plasma glucose is diabetes, particularly when blood glucose is not well controlled. This can happen in both Type 1 and Type 2 diabetes.</li>
        <li><b>Insulin Resistance:</b> In conditions like obesity or metabolic syndrome, the body’s cells become less responsive to insulin, causing elevated blood glucose levels.</li>
        <li><b>Stress or Illness:</b> Physical or emotional stress, as well as infections or other illnesses, can cause blood glucose levels to rise due to the release of stress hormones like cortisol.</li>
        <li><b>Medications:</b> Certain medications, such as corticosteroids, thiazide diuretics, or beta-blockers, can increase blood glucose levels.</li>
        <li><b>Endocrine Disorders:</b> Conditions like Cushing’s syndrome (excess cortisol), pheochromocytoma (tumors that release adrenaline), or acromegaly (growth hormone excess) can result in elevated blood sugar.</li>
        <li><b>Pregnancy (Gestational Diabetes):</b> High blood glucose levels during pregnancy, due to insulin resistance, is known as gestational diabetes.</li>
        <li><b>Pancreatic Disorders:</b> Diseases like pancreatitis, pancreatic cancer, or removal of part of the pancreas can reduce insulin production, leading to high blood sugar levels.</li>
        <li><b>Chronic Stress:</b> Prolonged emotional or physical stress can raise cortisol levels, which in turn raises blood sugar levels.</li>
    </ul>
</div>
<div>
    <h3>Tips:</h3>
    <ul>
        <li>Monitor Blood Sugar: Regular monitoring of blood glucose levels is crucial for individuals with diabetes or those at risk of developing diabetes.</li>
        <li>Follow a Diabetes Management Plan: If diagnosed with diabetes, work with your healthcare provider to create and stick to a blood sugar management plan, including medication, diet, and exercise.</li>
        <li>Stay Active: Regular physical activity can help increase insulin sensitivity and reduce blood sugar levels.</li>
        <li>Manage Stress: Practice stress management techniques like yoga, meditation, or deep breathing to lower cortisol levels and improve blood sugar control.</li>
        <li>Watch Your Diet: Avoid processed foods, sugary snacks, and beverages that cause rapid spikes in blood glucose. Focus on a balanced diet with whole foods.</li>
        <li>Weight Management: Achieving and maintaining a healthy weight through diet and exercise can help manage insulin resistance and lower blood sugar levels.</li>
    </ul>
</div>
<div>
    <h3>Foods to Eat:</h3>
    <ul>
        <li><b>Whole Grains:</b> Brown rice, quinoa, barley, and oats to provide fiber and help regulate blood sugar levels.</li>
        <li><b>Leafy Greens and Non-Starchy Vegetables:</b> Spinach, kale, broccoli, cauliflower, and bell peppers to help manage glucose levels.</li>
        <li><b>Lean Proteins:</b> Skinless poultry, fish, beans, and legumes for steady energy and to help manage hunger.</li>
        <li><b>Healthy Fats:</b> Avocados, nuts, seeds, and olive oil to support blood sugar control and promote satiety.</li>
        <li><b>Cinnamon and Apple Cider Vinegar:</b> Both have been shown to help in reducing blood sugar levels and improving insulin sensitivity.</li>
    </ul>
</div>
<div>
    <h3>Example Meal Plan for High Fasting Plasma Glucose:</h3>
    <ul>
        <li><b>Breakfast:</b> Scrambled eggs with spinach, a slice of whole-grain toast, and a side of fresh berries (protein, fiber, and healthy fats).</li>
        <li><b>Lunch:</b> Grilled chicken with a quinoa salad, mixed vegetables (leafy greens, cucumber, tomatoes), and a drizzle of olive oil (balanced meal with complex carbs, lean protein, and healthy fats).</li>
        <li><b>Snack:</b> A small handful of almonds and an apple (protein and fiber).</li>
        <li><b>Dinner:</b> Baked salmon with roasted Brussels sprouts and cauliflower (healthy fats and non-starchy vegetables).</li>
    </ul>
</div>
""")

    # Glycated Hemoglobin (HbA1C) (range: 4.0-5.6%)
        if values["Glycated Hemoglobin"] < 5.7:
            advice.append("""
<h2>Low Glycated Hemoglobin (HbA1c)</h2>
<div>
    <h3>Root Cause:</h3>
    <ul>
        <li><b>Good Blood Sugar Control:</b> A low HbA1c usually indicates good control of blood glucose over the past 2-3 months. In individuals with diabetes, a low HbA1c can signify effective management through medication, lifestyle changes (diet and exercise), or both.</li>
        <li><b>Recent Hypoglycemia:</b> If someone with diabetes experienced significant hypoglycemia (low blood sugar) recently, it can lower their HbA1c, but this is not typically a healthy sign, as it may indicate that blood sugar control has been unstable.</li>
        <li><b>Anemia:</b> Certain types of anemia, such as iron-deficiency anemia or hemolytic anemia, can cause falsely low HbA1c readings. The shortened lifespan of red blood cells in these conditions leads to a reduced time for glucose to attach to hemoglobin.</li>
        <li><b>Chronic Blood Loss:</b> Conditions such as gastrointestinal bleeding or other chronic blood loss can lead to lower HbA1c levels as new red blood cells are formed and have less time to become glycated.</li>
        <li><b>Pregnancy:</b> Pregnancy, especially in the first trimester, can lower HbA1c levels due to changes in red blood cell turnover and increased blood volume.</li>
    </ul>
</div>
<div>
    <h3>Tips:</h3>
    <ul>
        <li>Monitor Overall Blood Sugar Control: While a low HbA1c can be a positive indicator of good control, ensure it is not the result of frequent hypoglycemic episodes. If you have diabetes, it is essential to aim for a balance, avoiding both high and low extremes.</li>
        <li>Ensure Adequate Nutrition: Make sure you're getting enough essential nutrients, particularly iron, vitamin B12, and folic acid, as deficiencies in these can contribute to anemia, which might lower HbA1c readings.</li>
        <li>Avoid Hypoglycemia: If you're on diabetes medication, be cautious of taking too much insulin or other glucose-lowering medications. Regular monitoring of blood glucose levels can help avoid dangerous low blood sugar episodes.</li>
        <li>Regular Monitoring: Continue regular testing of blood glucose levels and HbA1c, especially if you have diabetes, to stay on top of your long-term blood sugar control.</li>
    </ul>
</div>
<div>
    <h3>Foods to Eat:</h3>
    <ul>
        <li><b>Iron-Rich Foods:</b> Red meat, poultry, beans, lentils, spinach, and fortified cereals to prevent or address anemia.</li>
        <li><b>Vitamin B12 and Folate-Rich Foods:</b> Eggs, dairy, fortified cereals, leafy greens, beans, and lentils to prevent deficiencies that might affect red blood cell production.</li>
        <li><b>Complex Carbohydrates:</b> Whole grains (oats, quinoa, brown rice) for stable glucose control and overall energy.</li>
        <li><b>Healthy Fats:</b> Avocados, olive oil, and nuts for heart health and blood sugar stabilization.</li>
    </ul>
</div>
<div>
    <h3>Example Meal Plan for Low HbA1c:</h3>
    <ul>
        <li><b>Breakfast:</b> Oatmeal with chia seeds, almond butter, and sliced strawberries (iron and fiber).</li>
        <li><b>Lunch:</b> Grilled chicken salad with spinach, quinoa, avocado, and olive oil dressing (iron, protein, healthy fats).</li>
        <li><b>Snack:</b> A boiled egg and a small handful of almonds (protein and healthy fats).</li>
        <li><b>Dinner:</b> Baked salmon with roasted sweet potatoes and broccoli (omega-3s, complex carbs, and fiber).</li>
    </ul>
</div>
""")
        elif values["Glycated Hemoglobin"] >= 5.7:
            advice.append("""
<h2>High Glycated Hemoglobin (HbA1c)</h2>
<div>
    <h3>Root Cause:</h3>
    <ul>
        <li><b>Poor Blood Sugar Control:</b> A high HbA1c level is typically seen in individuals with poorly controlled diabetes, where blood glucose levels remain elevated over an extended period (usually 2-3 months).</li>
        <li><b>Diabetes:</b> Most commonly associated with uncontrolled Type 1 and Type 2 diabetes. When blood sugar levels remain high, glucose binds to hemoglobin in red blood cells, raising HbA1c levels.</li>
        <li><b>Increased Red Blood Cell Turnover:</b> Conditions that cause the destruction of red blood cells, such as hemolytic anemia, may lead to falsely high HbA1c levels. This is because the new red blood cells formed from this increased turnover have less time to be glycated.</li>
        <li><b>Kidney Disease:</b> Chronic kidney disease can lead to impaired clearance of glucose from the blood, causing high blood sugar levels and, consequently, high HbA1c levels.</li>
        <li><b>Stress:</b> Physical or emotional stress can lead to an increase in blood sugar levels due to the release of stress hormones (like cortisol), which raise glucose levels.</li>
        <li><b>Poor Diet:</b> A diet high in refined carbohydrates and sugars can contribute to consistently high blood glucose, increasing HbA1c levels.</li>
        <li><b>Medications:</b> Certain medications, such as corticosteroids, can raise blood glucose levels and increase HbA1c.</li>
    </ul>
</div>
<div>
    <h3>Tips:</h3>
    <ul>
        <li>Improve Blood Sugar Control: If you have diabetes, work with your healthcare provider to adjust your medication (insulin, oral hypoglycemics) and improve blood sugar monitoring.</li>
        <li>Exercise Regularly: Physical activity helps to increase insulin sensitivity, lower blood glucose, and improve HbA1c.</li>
        <li>Dietary Modifications: Adopt a balanced diet rich in whole grains, vegetables, lean proteins, and healthy fats to stabilize blood sugar levels.</li>
        <li>Monitor for Complications: Elevated HbA1c levels over time can increase the risk of diabetes complications (e.g., neuropathy, kidney disease, cardiovascular issues). Regular check-ups are important to prevent or manage these issues.</li>
        <li>Manage Stress: Stress can worsen blood sugar control. Consider incorporating relaxation techniques, such as meditation, deep breathing exercises, and yoga.</li>
        <li>Track Your Progress: Keep a food journal, monitor blood glucose regularly, and work with your healthcare provider to adjust treatment plans as necessary.</li>
    </ul>
</div>
<div>
    <h3>Foods to Eat:</h3>
    <ul>
        <li><b>Complex Carbohydrates:</b> Whole grains like quinoa, barley, and brown rice to provide steady energy without spiking blood glucose.</li>
        <li><b>Non-Starchy Vegetables:</b> Leafy greens (spinach, kale), broccoli, cauliflower, and bell peppers for fiber and low glycemic index (GI) options.</li>
        <li><b>Lean Protein:</b> Skinless poultry, fish, beans, and legumes to stabilize blood sugar and support muscle repair.</li>
        <li><b>Healthy Fats:</b> Avocados, olive oil, chia seeds, and walnuts to support heart health and prevent blood sugar spikes.</li>
        <li><b>Cinnamon and Turmeric:</b> Both spices are believed to help with blood sugar regulation. Add them to meals or beverages for flavor and health benefits.</li>
    </ul>
</div>
<div>
    <h3>Example Meal Plan for High HbA1c:</h3>
    <ul>
        <li><b>Breakfast:</b> Scrambled eggs with spinach and a side of whole-grain toast (protein and complex carbs).</li>
        <li><b>Lunch:</b> Grilled salmon with quinoa, a spinach salad, and olive oil dressing (lean protein, complex carbs, and healthy fats).</li>
        <li><b>Snack:</b> A handful of almonds and an apple (healthy fats and fiber).</li>
        <li><b>Dinner:</b> Grilled chicken with roasted Brussels sprouts and sweet potato (lean protein, non-starchy vegetables, and complex carbs).</li>
    </ul>
</div>
""")

    # Triglycerides (range: 150 mg/dL)
        if values["Triglycerides"] > 150:
            advice.append("""
        <div>
            <h2>High Triglycerides (Hypertriglyceridemia)</h2>
            
            <div>
                <h3>Root Cause:</h3>
                <ul>
                    <li><strong>Obesity or Overweight:</strong> Excess body fat increases triglyceride production and reduces clearance.</li>
                    <li><strong>Poor Diet:</strong> Diets high in refined carbohydrates, sugars, trans fats, and saturated fats elevate triglycerides.</li>
                    <li><strong>Diabetes:</strong> Insulin resistance from poorly controlled diabetes contributes to high triglyceride levels.</li>
                    <li><strong>Excessive Alcohol:</strong> Alcohol is converted into triglycerides in the liver.</li>
                    <li><strong>Hypothyroidism:</strong> An underactive thyroid reduces fat breakdown, leading to elevated triglycerides.</li>
                    <li><strong>Genetic Factors:</strong> Familial hypertriglyceridemia is a genetic disorder causing high triglyceride levels.</li>
                    <li><strong>Medications:</strong> Certain drugs like corticosteroids, diuretics, and beta-blockers may increase triglycerides.</li>
                </ul>
            </div>

            <div>
                <h3>Tips:</h3>
                <ul>
                    <li>Adopt a <strong>Low-Carb, Low-Sugar Diet:</strong> Reducing sugar and refined carbs can help lower triglycerides.</li>
                    <li><strong>Exercise Regularly:</strong> Aerobic exercises like walking, swimming, or cycling are effective.</li>
                    <li><strong>Lose Weight:</strong> Losing just 5-10% of body weight can significantly reduce triglycerides.</li>
                    <li><strong>Avoid Alcohol:</strong> Minimize or eliminate alcohol consumption.</li>
                    <li><strong>Increase Omega-3 Fatty Acids:</strong> Eat fatty fish (salmon, mackerel), flaxseeds, chia seeds, and walnuts.</li>
                    <li><strong>Control Blood Sugar:</strong> Properly managing diabetes can lower triglyceride levels.</li>
                    <li><strong>Consider Medications:</strong> Consult a doctor about fibrates, omega-3 supplements, or statins if necessary.</li>
                </ul>
            </div>

            <div>
                <h3>Foods to Eat:</h3>
                <ul>
                    <li><strong>Omega-3 Fatty Acids:</strong> Fatty fish (salmon, mackerel), flaxseeds, chia seeds, and walnuts.</li>
                    <li><strong>Fiber-Rich Foods:</strong> Oats, barley, lentils, beans, and vegetables.</li>
                    <li><strong>Healthy Fats:</strong> Olive oil, avocado, and nuts (almonds, walnuts).</li>
                    <li><strong>Leafy Greens and Vegetables:</strong> Spinach, kale, broccoli, and cauliflower.</li>
                    <li><strong>Whole Grains:</strong> Brown rice, quinoa, and whole wheat for more fiber and nutrients.</li>
                </ul>
            </div>

            <div>
                <h3>Example Meal Plan:</h3>
                <ul>
                    <li><strong>Breakfast:</strong> Oatmeal with chia seeds, flaxseeds, and fresh berries (fiber, omega-3s, antioxidants).</li>
                    <li><strong>Lunch:</strong> Grilled salmon with quinoa salad, avocado, and mixed greens with olive oil dressing.</li>
                    <li><strong>Snack:</strong> A handful of walnuts and a pear.</li>
                    <li><strong>Dinner:</strong> Baked chicken with roasted Brussels sprouts and sweet potatoes.</li>
                </ul>
            </div>
        </div>
        """)

        if values["Total Cholesterol"] < 125:
            advice.append("""
            <div>
                <h2>Low Total Cholesterol (Hypocholesterolemia)</h2>
                
                <div>
                    <h3>Root Cause:</h3>
                    <ul>
                        <li><strong>Good Diet and Lifestyle:</strong> A balanced diet and physical activity contribute to healthy cholesterol levels.</li>
                        <li><strong>Hyperthyroidism:</strong> An overactive thyroid gland speeds up metabolism, lowering cholesterol.</li>
                        <li><strong>Liver Disease:</strong> Impaired liver function can reduce cholesterol production.</li>
                        <li><strong>Malnutrition or Starvation:</strong> Inadequate nutrient intake can cause low cholesterol.</li>
                        <li><strong>Genetic Factors:</strong> Rare genetic conditions can result in low cholesterol levels.</li>
                        <li><strong>Chronic Infections or Inflammatory Diseases:</strong> Severe systemic inflammation can decrease cholesterol production.</li>
                        <li><strong>Medications:</strong> Cholesterol-lowering drugs may sometimes reduce cholesterol too much.</li>
                    </ul>
                </div>

                <div>
                    <h3>Tips:</h3>
                    <ul>
                        <li>Ensure adequate <strong>caloric intake</strong> with a balanced diet.</li>
                        <li>Include <strong>healthy fats</strong> from avocados, olive oil, nuts, and seeds.</li>
                        <li>Monitor <strong>thyroid function</strong> to rule out hyperthyroidism.</li>
                        <li>Avoid <strong>extreme diets</strong> that excessively limit fat intake.</li>
                        <li>Get <strong>regular check-ups</strong> for medical conditions affecting cholesterol.</li>
                    </ul>
                </div>

                <div>
                    <h3>Foods to Eat:</h3>
                    <ul>
                        <li><strong>Healthy Fats:</strong> Avocados, olive oil, nuts, and seeds.</li>
                        <li><strong>Lean Proteins:</strong> Poultry, fatty fish, tofu, and legumes.</li>
                        <li><strong>Whole Grains:</strong> Brown rice, quinoa, oats, and barley.</li>
                        <li><strong>Fruits and Vegetables:</strong> Dark leafy greens, cruciferous vegetables, and antioxidant-rich fruits.</li>
                    </ul>
                </div>

                <div>
                    <h3>Example Meal Plan:</h3>
                    <ul>
                        <li><strong>Breakfast:</strong> Oatmeal with chia seeds, ground flaxseeds, walnuts, and fresh berries.</li>
                        <li><strong>Lunch:</strong> Grilled salmon salad with avocado, mixed greens, quinoa, and olive oil dressing.</li>
                        <li><strong>Snack:</strong> A handful of almonds and a banana.</li>
                        <li><strong>Dinner:</strong> Baked chicken with roasted sweet potatoes and steamed broccoli.</li>
                    </ul>
                </div>
            </div>
            """)

    # LDL Cholesterol (range: < 100 mg/dL)
    # LDL Cholesterol (range: < 100 mg/dL)
        if values["LDL Cholesterol"] > 130:
            advice.append("""
        <h2>High LDL Cholesterol (Low-Density Lipoprotein Cholesterol)</h2>
        <h3>Root Cause:</h3>
        <ul>
            <li><strong>Unhealthy Diet:</strong> A diet rich in saturated fats (e.g., red meat, butter, cheese, full-fat dairy) and trans fats (processed foods, baked goods, fried foods).</li>
            <li><strong>Obesity:</strong> Excess weight, especially abdominal fat, leads to higher LDL cholesterol levels.</li>
            <li><strong>Sedentary Lifestyle:</strong> Lack of physical activity reduces the body’s ability to balance LDL and HDL cholesterol.</li>
            <li><strong>Genetic Factors:</strong> Familial hypercholesterolemia, a genetic disorder causing high LDL cholesterol levels.</li>
            <li><strong>Diabetes:</strong> Insulin resistance and high blood sugar can raise LDL cholesterol.</li>
            <li><strong>Hypothyroidism:</strong> An underactive thyroid slows cholesterol metabolism.</li>
            <li><strong>Kidney Disease:</strong> Chronic kidney disease can impair lipid metabolism.</li>
            <li><strong>Medications:</strong> Drugs like corticosteroids, beta-blockers, and diuretics may increase LDL cholesterol.</li>
        </ul>
        <h3>Health Risks:</h3>
        <ul>
            <li>Atherosclerosis: Plaque buildup in arteries leading to narrowing and increased cardiovascular risk.</li>
            <li>Heart Disease: Significant risk for coronary artery disease (CAD) and heart attacks.</li>
            <li>Stroke: Blocked blood vessels in the brain raise stroke risk.</li>
        </ul>
        <h3>Tips to Lower LDL Cholesterol:</h3>
        <ul>
            <li><strong>Heart-Healthy Diet:</strong> Reduce saturated and trans fats; increase fiber and healthy fats.</li>
            <li><strong>Exercise Regularly:</strong> 30 minutes of moderate-intensity aerobic activity most days.</li>
            <li><strong>Maintain a Healthy Weight:</strong> Losing excess weight improves cholesterol levels.</li>
            <li><strong>Quit Smoking:</strong> Improves cholesterol balance and reduces cardiovascular risk.</li>
            <li><strong>Limit Alcohol:</strong> Reducing excessive alcohol intake helps manage cholesterol.</li>
            <li><strong>Consider Medications:</strong> Statins or other cholesterol-lowering drugs if necessary.</li>
        </ul>
        <h3>Foods to Include:</h3>
        <ul>
            <li><strong>Omega-3 Fatty Acids:</strong> Fatty fish (salmon, mackerel), flaxseeds, walnuts.</li>
            <li><strong>Fiber-Rich Foods:</strong> Oats, barley, beans, lentils, apples, carrots.</li>
            <li><strong>Healthy Fats:</strong> Olive oil, avocado, nuts, seeds.</li>
            <li><strong>Plant Sterols:</strong> Found in fortified foods like margarine, orange juice, yogurt drinks.</li>
            <li><strong>Whole Grains:</strong> Quinoa, brown rice, whole wheat bread.</li>
            <li><strong>Fruits and Vegetables:</strong> Berries, citrus fruits, leafy greens, cruciferous vegetables.</li>
        </ul>
        <h3>Example Meal Plan:</h3>
        <ul>
            <li><strong>Breakfast:</strong> Oatmeal with chia seeds, flaxseeds, fresh berries.</li>
            <li><strong>Lunch:</strong> Grilled salmon with quinoa salad, mixed greens, olive oil dressing.</li>
            <li><strong>Snack:</strong> Handful of almonds and an apple.</li>
            <li><strong>Dinner:</strong> Baked chicken breast with roasted Brussels sprouts, sweet potatoes, and mixed greens.</li>
        </ul>
        """)

    # HDL Cholesterol (range: > 40 mg/dL for men, > 50 mg/dL for women)
    # HDL Cholesterol (range: > 40 mg/dL)
        if values["HDL Cholesterol"] < 40:
            advice.append("""
        <h2>Low HDL Cholesterol (High-Density Lipoprotein Cholesterol)</h2>
        <h3>Root Cause:</h3>
        <ul>
            <li><strong>Unhealthy Diet:</strong> High intake of refined sugars, trans fats, and unhealthy fats (saturated fats in red meat, processed foods, and fried foods).</li>
            <li><strong>Obesity:</strong> Excess body weight, particularly abdominal fat, is linked to low HDL levels and increased LDL and triglycerides.</li>
            <li><strong>Physical Inactivity:</strong> Lack of exercise reduces HDL cholesterol.</li>
            <li><strong>Smoking:</strong> Smoking damages blood vessels, reduces HDL cholesterol, and increases cardiovascular risk.</li>
            <li><strong>Genetics:</strong> Genetic predisposition to low HDL levels may run in families.</li>
            <li><strong>Type 2 Diabetes:</strong> Insulin resistance and metabolic imbalances can lower HDL cholesterol.</li>
            <li><strong>Chronic Inflammation:</strong> Conditions like rheumatoid arthritis or chronic infections may reduce HDL levels.</li>
            <li><strong>Alcohol:</strong> While moderate consumption can raise HDL, excessive drinking lowers HDL and harms health.</li>
            <li><strong>Medications:</strong> Certain medications (e.g., anabolic steroids, beta-blockers) can lower HDL levels.</li>
        </ul>
        <h3>Health Risks of Low HDL Cholesterol:</h3>
        <ul>
            <li><strong>Cardiovascular Disease:</strong> Low HDL is a major risk factor for heart disease and prevents effective cholesterol removal.</li>
            <li><strong>Atherosclerosis:</strong> Increased risk of plaque buildup in arteries, leading to heart attack and stroke.</li>
            <li><strong>Metabolic Syndrome:</strong> Low HDL is a marker for metabolic syndrome, increasing risk of diabetes and heart disease.</li>
        </ul>
        <h3>Tips to Raise HDL Cholesterol:</h3>
        <ul>
            <li><strong>Adopt a Heart-Healthy Diet:</strong> Include monounsaturated and polyunsaturated fats, and avoid trans and saturated fats.</li>
            <li><strong>Exercise Regularly:</strong> Engage in aerobic activities (walking, jogging, cycling, swimming) for at least 30 minutes most days.</li>
            <li><strong>Lose Excess Weight:</strong> Reducing abdominal fat can improve HDL and overall lipid profile.</li>
            <li><strong>Quit Smoking:</strong> Improves HDL levels and overall cardiovascular health.</li>
            <li><strong>Limit Alcohol:</strong> Moderate intake may help, but avoid excessive consumption.</li>
            <li><strong>Manage Underlying Conditions:</strong> Treat conditions like diabetes and hypothyroidism to improve HDL levels.</li>
        </ul>
        <h3>Foods to Eat:</h3>
        <ul>
            <li><strong>Healthy Fats:</strong> Olive oil, avocado, fatty fish (salmon, mackerel), walnuts, flaxseeds, chia seeds.</li>
            <li><strong>Nuts and Seeds:</strong> Almonds, walnuts, sunflower seeds, flaxseeds.</li>
            <li><strong>Fatty Fish:</strong> Salmon, mackerel, sardines, and herring.</li>
            <li><strong>Olive Oil:</strong> Rich in monounsaturated fats and antioxidants.</li>
            <li><strong>Fiber-Rich Foods:</strong> Oats, barley, beans, lentils, whole grains.</li>
            <li><strong>Fruits and Vegetables:</strong> Berries, citrus fruits, dark leafy greens, cruciferous vegetables.</li>
        </ul>
        """)

# VLDL Cholesterol (range: 2-30 mg/dL)
        if values["VLDL Cholesterol"] < 2:
            advice.append("""
        <h2>Low VLDL Cholesterol</h2>
        <h3>Root Cause:</h3>
        <ul>
            <li><strong>Very Low Fat Diet:</strong> Extremely low-fat diets may lower VLDL cholesterol production.</li>
            <li><strong>Malnutrition or Starvation:</strong> Prolonged fasting or malnutrition reduces fat intake, lowering VLDL.</li>
            <li><strong>Hyperthyroidism:</strong> Overactive thyroid accelerates metabolism, reducing lipid levels.</li>
            <li><strong>Genetic Factors:</strong> Rare genetic conditions like familial hypolipidemia.</li>
            <li><strong>Medications:</strong> Statins and fibrates can lower VLDL as part of their effect.</li>
            <li><strong>Liver Disease:</strong> Severe liver dysfunction impairs lipoprotein production.</li>
        </ul>
        <h3>Health Considerations:</h3>
        <ul>
            <li><strong>Nutrient Deficiency:</strong> Inadequate fats may impair absorption of fat-soluble vitamins (A, D, E, K).</li>
            <li><strong>Hormonal Imbalance:</strong> Cholesterol is essential for hormone production.</li>
            <li><strong>Impaired Fat Metabolism:</strong> Indicates improper fat metabolism and nutrient deficiencies.</li>
        </ul>
        <h3>Tips to Raise Low VLDL Cholesterol:</h3>
        <ul>
            <li><strong>Increase Healthy Fats:</strong> Include olive oil, avocados, nuts, and seeds in the diet.</li>
            <li><strong>Ensure Adequate Caloric Intake:</strong> Increase calorie intake with nutrient-dense foods.</li>
            <li><strong>Incorporate Healthy Carbohydrates:</strong> Whole grains like quinoa, oats, and brown rice.</li>
            <li><strong>Avoid Very Low-Fat Diets:</strong> Balance fat intake to ensure essential lipid levels.</li>
        </ul>
        <h3>Foods to Eat:</h3>
        <ul>
            <li><strong>Healthy Fats:</strong> Olive oil, avocado, fatty fish, nuts, and seeds.</li>
            <li><strong>Lean Proteins:</strong> Chicken, turkey, legumes, tofu, and low-fat dairy.</li>
            <li><strong>Whole Grains:</strong> Quinoa, oats, barley, brown rice.</li>
            <li><strong>Fruits and Vegetables:</strong> Bananas, avocados, sweet potatoes, carrots.</li>
        </ul>
        """)
        elif values["VLDL Cholesterol"] > 11:
            advice.append("""
        <h2>High VLDL Cholesterol</h2>
        <h3>Root Cause:</h3>
        <ul>
            <li><strong>Unhealthy Diet:</strong> High intake of refined carbs, sugars, and unhealthy fats.</li>
            <li><strong>Obesity:</strong> Abdominal fat increases VLDL levels.</li>
            <li><strong>Diabetes and Insulin Resistance:</strong> Leads to increased triglycerides and VLDL production.</li>
            <li><strong>Alcohol Consumption:</strong> Excessive alcohol increases liver triglyceride production.</li>
            <li><strong>Genetics:</strong> Conditions like familial hypertriglyceridemia.</li>
            <li><strong>Kidney Disease:</strong> Impaired lipid metabolism in chronic kidney disease.</li>
            <li><strong>Hypothyroidism:</strong> Slows metabolism and increases VLDL production.</li>
        </ul>
        <h3>Health Risks:</h3>
        <ul>
            <li><strong>Atherosclerosis:</strong> Contributes to plaque formation and artery narrowing.</li>
            <li><strong>Heart Disease:</strong> Increases risk of coronary artery disease and heart attack.</li>
            <li><strong>Metabolic Syndrome:</strong> Cluster of conditions raising the risk of heart disease and diabetes.</li>
        </ul>
        <h3>Tips to Lower High VLDL Cholesterol:</h3>
        <ul>
            <li><strong>Limit Refined Carbs and Sugars:</strong> Avoid sugary beverages, white bread, and pastries.</li>
            <li><strong>Reduce Saturated and Trans Fats:</strong> Avoid fatty meats, full-fat dairy, and processed foods.</li>
            <li><strong>Increase Fiber Intake:</strong> Include oats, beans, lentils, and fruits.</li>
            <li><strong>Exercise Regularly:</strong> Engage in aerobic activities like walking, swimming, and jogging.</li>
            <li><strong>Lose Excess Weight:</strong> Focus on reducing abdominal fat.</li>
            <li><strong>Limit Alcohol Intake:</strong> Excessive drinking contributes to high VLDL levels.</li>
            <li><strong>Control Blood Sugar:</strong> Manage diabetes with diet, exercise, and medication.</li>
        </ul>
        <h3>Foods to Eat:</h3>
        <ul>
            <li><strong>Omega-3 Fatty Acids:</strong> Salmon, mackerel, flaxseeds, and walnuts.</li>
            <li><strong>Soluble Fiber:</strong> Oats, barley, apples, and carrots.</li>
            <li><strong>Healthy Fats:</strong> Avocado, olive oil, almonds, and walnuts.</li>
            <li><strong>Antioxidant-Rich Vegetables and Fruits:</strong> Berries, citrus fruits, broccoli, spinach.</li>
            <li><strong>Whole Grains:</strong> Quinoa, brown rice, whole wheat bread.</li>
        </ul>
        """)

    # Total Cholesterol / HDL Cholesterol Ratio (range: 3.5-5.0)
        if values["Total Cholesterol / HDL Cholesterol Ratio"] > 4.5:
            advice.append("""
        <h2>High Total Cholesterol / HDL Cholesterol Ratio</h2>
        <h3>Root Cause:</h3>
        <ul>
            <li><strong>Unhealthy Diet:</strong> A diet high in saturated fats, trans fats, and cholesterol-rich foods can elevate total cholesterol levels while reducing HDL cholesterol.</li>
            <li><strong>Obesity:</strong> Excess body weight, particularly abdominal fat, increases total cholesterol levels and reduces HDL cholesterol.</li>
            <li><strong>Physical Inactivity:</strong> Lack of exercise can lead to high levels of total cholesterol and low levels of HDL cholesterol.</li>
            <li><strong>Smoking:</strong> Smoking damages blood vessels and lowers HDL cholesterol, increasing the ratio.</li>
            <li><strong>Genetics:</strong> Conditions like familial hypercholesterolemia can contribute to a higher ratio.</li>
            <li><strong>Diabetes and Insulin Resistance:</strong> Poorly controlled diabetes can worsen the cholesterol balance.</li>
            <li><strong>Chronic Stress:</strong> Long-term stress may increase total cholesterol while lowering HDL cholesterol.</li>
            <li><strong>Hypothyroidism:</strong> An underactive thyroid can elevate total cholesterol levels and lower HDL cholesterol.</li>
        </ul>
        <h3>Health Risks:</h3>
        <ul>
            <li><strong>Cardiovascular Disease:</strong> A higher ratio increases the risk of atherosclerosis, heart disease, and stroke.</li>
            <li><strong>Metabolic Syndrome:</strong> A high ratio is a marker for metabolic syndrome, linked to heart disease and type 2 diabetes.</li>
        </ul>
        <h3>Tips to Lower the Ratio:</h3>
        <ul>
            <li>Adopt a heart-healthy diet, focusing on healthy fats, fiber, and whole foods.</li>
            <li>Engage in regular physical activity.</li>
            <li>Lose excess weight, especially abdominal fat.</li>
            <li>Quit smoking and limit alcohol intake.</li>
            <li>Control diabetes and insulin resistance.</li>
            <li>Consult a healthcare provider about medications if needed.</li>
        </ul>
        <h3>Foods to Eat:</h3>
        <ul>
            <li>Healthy fats: Olive oil, avocados, nuts, and seeds.</li>
            <li>Omega-3 fatty acids: Fatty fish, flaxseeds, and walnuts.</li>
            <li>Soluble fiber: Oats, beans, lentils, and fruits like apples and pears.</li>
            <li>Whole grains: Quinoa, brown rice, and whole wheat bread.</li>
            <li>Antioxidant-rich vegetables and fruits: Leafy greens, berries, and citrus fruits.</li>
        </ul>
        <h3>Example Meal Plan:</h3>
        <ul>
            <li><strong>Breakfast:</strong> Oatmeal with chia seeds, walnuts, and berries.</li>
            <li><strong>Lunch:</strong> Grilled salmon with quinoa and mixed greens.</li>
            <li><strong>Snack:</strong> A handful of almonds and an apple.</li>
            <li><strong>Dinner:</strong> Grilled chicken with roasted Brussels sprouts and sweet potatoes.</li>
        </ul>
        """)

        if values["LDL Cholesterol / HDL Cholesterol Ratio"] > 3:
            advice.append("""
        <h2>High LDL Cholesterol / HDL Cholesterol Ratio</h2>
        <h3>Root Cause:</h3>
        <ul>
            <li><strong>Unhealthy Diet:</strong> High intake of saturated and trans fats raises LDL and lowers HDL cholesterol.</li>
            <li><strong>Obesity:</strong> Excess body weight contributes to higher LDL and lower HDL cholesterol levels.</li>
            <li><strong>Physical Inactivity:</strong> Lack of exercise worsens the LDL/HDL ratio.</li>
            <li><strong>Smoking:</strong> Smoking lowers HDL cholesterol, raising the LDL/HDL ratio.</li>
            <li><strong>Genetics:</strong> Genetic conditions like familial hypercholesterolemia elevate LDL cholesterol levels.</li>
            <li><strong>Diabetes and Insulin Resistance:</strong> Poorly controlled blood sugar can affect the LDL/HDL ratio.</li>
            <li><strong>Chronic Stress:</strong> Stress may increase LDL and lower HDL cholesterol.</li>
            <li><strong>Hypothyroidism:</strong> An underactive thyroid slows lipid metabolism, leading to imbalance.</li>
        </ul>
        <h3>Health Risks:</h3>
        <ul>
            <li><strong>Cardiovascular Disease:</strong> High LDL contributes to plaque buildup and atherosclerosis.</li>
            <li><strong>Metabolic Syndrome:</strong> An elevated LDL/HDL ratio is a key marker for this condition.</li>
        </ul>
        <h3>Tips to Lower the Ratio:</h3>
        <ul>
            <li>Focus on a heart-healthy diet, low in saturated and trans fats.</li>
            <li>Exercise regularly to raise HDL and lower LDL cholesterol.</li>
            <li>Lose excess weight to improve cholesterol balance.</li>
            <li>Quit smoking and limit alcohol consumption.</li>
            <li>Manage diabetes and insulin resistance effectively.</li>
            <li>Consider medications like statins if prescribed by a doctor.</li>
        </ul>
        <h3>Foods to Eat:</h3>
        <ul>
            <li>Healthy fats: Olive oil, fatty fish, nuts, and seeds.</li>
            <li>Fiber-rich foods: Oats, beans, lentils, and fruits.</li>
            <li>Omega-3 fatty acids: Fatty fish, flaxseeds, and walnuts.</li>
            <li>Whole grains: Quinoa, brown rice, and whole wheat bread.</li>
            <li>Antioxidant-rich vegetables and fruits: Leafy greens and berries.</li>
        </ul>
        <h3>Example Meal Plan:</h3>
        <ul>
            <li><strong>Breakfast:</strong> Oatmeal with chia seeds and berries.</li>
            <li><strong>Lunch:</strong> Grilled salmon with quinoa and avocado.</li>
            <li><strong>Snack:</strong> A handful of almonds and an apple.</li>
            <li><strong>Dinner:</strong> Grilled chicken with roasted vegetables.</li>
        </ul>
        """)

    # Total Bilirubin (range: 0.1-1.2 mg/dL)
        if values["Total Bilirubin"] > 1.2:
            advice.append("""<h2>High Total Bilirubin</h2>
<p><strong>Root Cause:</strong></p>
<ul>
    <li><strong>Liver Disease:</strong> Elevated total bilirubin levels can indicate liver dysfunction. Conditions such as hepatitis (inflammation of the liver), cirrhosis (scarring of the liver tissue), and liver tumors can impair the liver’s ability to process and excrete bilirubin.</li>
    <li><strong>Hemolysis (Increased Red Blood Cell Breakdown):</strong> Excessive breakdown of red blood cells can overwhelm the liver's capacity to process the bilirubin released from hemoglobin. This can occur due to hemolytic anemia, certain genetic conditions, or blood disorders.</li>
    <li><strong>Gallbladder Disease:</strong> Blockages in the bile ducts or gallbladder issues (such as gallstones) can prevent bilirubin from being excreted, leading to increased bilirubin levels in the blood.</li>
    <li><strong>Gilbert’s Syndrome:</strong> A genetic disorder where the liver has a reduced ability to process bilirubin efficiently, leading to temporary mild elevations in bilirubin, especially during times of stress, illness, or fasting.</li>
    <li><strong>Biliary Obstruction:</strong> Any condition that obstructs the bile ducts, such as tumors or gallstones, can prevent bilirubin from being properly excreted, causing a buildup in the bloodstream.</li>
    <li><strong>Alcoholism:</strong> Chronic alcohol consumption can lead to liver damage, which can impair bilirubin processing, resulting in higher bilirubin levels.</li>
    <li><strong>Infections:</strong> Certain infections affecting the liver, such as viral hepatitis, malaria, or sepsis, can cause elevated bilirubin due to liver inflammation or cell destruction.</li>
    <li><strong>Medications:</strong> Some medications (such as acetaminophen in large doses, certain antibiotics, and chemotherapy drugs) can cause liver toxicity and interfere with bilirubin metabolism.</li>
</ul>

<p><strong>Health Risks of High Total Bilirubin:</strong></p>
<ul>
    <li><strong>Jaundice:</strong> The most noticeable sign of high bilirubin levels is jaundice, a yellowing of the skin and eyes. This occurs because bilirubin, when accumulated in excess, starts to deposit in tissues, particularly in the skin.</li>
    <li><strong>Liver Dysfunction:</strong> Persistently high levels of bilirubin may indicate an ongoing issue with liver function, which can lead to chronic liver disease or failure if not addressed.</li>
    <li><strong>Gallbladder Issues:</strong> High bilirubin can be a sign of gallstones or bile duct obstruction, which may require surgical intervention.</li>
    <li><strong>Anemia:</strong> If high bilirubin is due to hemolysis (destruction of red blood cells), it may lead to anemia, causing fatigue, weakness, and shortness of breath.</li>
    <li><strong>Severe Complications:</strong> If not treated, persistently high bilirubin levels can result in further liver damage, bile duct injury, or complications in blood flow to and from the liver, all of which can be life-threatening.</li>
</ul>

<p><strong>Tips to Lower High Total Bilirubin Levels:</strong></p>
<ul>
    <li><strong>Seek Medical Attention:</strong> If elevated bilirubin levels are due to liver disease, bile duct obstructions, or hemolysis, it's essential to identify and treat the underlying cause. Consult with a healthcare provider to assess liver function and determine the appropriate course of treatment.</li>
    <li><strong>Avoid Alcohol:</strong> If high bilirubin levels are due to liver dysfunction caused by alcohol consumption, it is critical to stop drinking to prevent further liver damage.</li>
    <li><strong>Manage Infections:</strong> If bilirubin levels are elevated due to infection (such as hepatitis), proper medical treatment, including antiviral medications and supportive care, is essential.</li>
    <li><strong>Consider Gallbladder Health:</strong> If a gallbladder or bile duct blockage is the cause, addressing the issue through procedures such as surgery or medication may be necessary.</li>
    <li><strong>Stay Hydrated:</strong> Adequate water intake helps the liver flush out toxins and process waste products like bilirubin more efficiently.</li>
    <li><strong>Limit Medication Use:</strong> If medications are contributing to liver damage and elevated bilirubin, discuss alternatives with your doctor. Avoid self-medicating and follow the prescribed dosage and treatment plan.</li>
    <li><strong>Monitor Blood Cell Health:</strong> If hemolysis (red blood cell destruction) is the cause of high bilirubin, managing underlying conditions (like autoimmune diseases or blood disorders) and preventing infections can help reduce hemolysis.</li>
</ul>

<p><strong>Foods to Eat for High Total Bilirubin:</strong></p>
<ul>
    <li><strong>Liver-Friendly Foods:</strong> The liver plays a central role in processing bilirubin, so eating foods that support liver function can help. These include:
        <ul>
            <li><strong>Leafy Greens:</strong> Kale, spinach, and other dark leafy vegetables are rich in antioxidants and chlorophyll, which help detoxify the liver and improve its function.</li>
            <li><strong>Cruciferous Vegetables:</strong> Broccoli, Brussels sprouts, and cabbage contain compounds that support liver detoxification pathways and reduce liver inflammation.</li>
            <li><strong>Berries:</strong> Blueberries, strawberries, and raspberries are rich in antioxidants that protect liver cells from damage.</li>
            <li><strong>Turmeric:</strong> This spice contains curcumin, which has anti-inflammatory properties and supports liver detoxification.</li>
            <li><strong>Beets:</strong> Beets are rich in antioxidants and fiber, which help cleanse the liver and improve its ability to process bilirubin.</li>
            <li><strong>Garlic:</strong> Garlic has sulfur compounds that support liver detoxification and may help reduce inflammation in liver tissue.</li>
            <li><strong>Green Tea:</strong> Rich in antioxidants, particularly catechins, green tea has been shown to support liver function and detoxification.</li>
            <li><strong>Lemon and Lime:</strong> These citrus fruits are rich in vitamin C and antioxidants that support liver health and enhance the liver’s detoxifying abilities.</li>
            <li><strong>High-Fiber Foods:</strong> Foods rich in fiber (such as whole grains, oats, beans, and legumes) support overall digestion and bile flow, aiding in the processing and elimination of waste products like bilirubin.</li>
            <li><strong>Healthy Fats:</strong> Include healthy fats like olive oil, nuts, seeds, and fatty fish (salmon, mackerel) in your diet. These fats support liver function and have anti-inflammatory effects.</li>
        </ul>
    </li>
</ul>

<p><strong>Example Meal Plan for High Total Bilirubin:</strong></p>
<ul>
    <li><strong>Breakfast:</strong> Oatmeal with chia seeds, blueberries, and a drizzle of honey (fiber, antioxidants, and liver-supporting compounds).</li>
    <li><strong>Lunch:</strong> Grilled salmon with quinoa, steamed broccoli, and a side of mixed greens with olive oil and lemon dressing (omega-3s, antioxidants, and fiber).</li>
    <li><strong>Snack:</strong> A handful of walnuts and a small apple (healthy fats and fiber).</li>
    <li><strong>Dinner:</strong> Grilled chicken breast with roasted beets, sautéed spinach with garlic, and a side of brown rice (protein, antioxidants, and liver-supporting vegetables).</li>
</ul>
""")

        if values["Direct Bilirubin"] > 0.2:
            advice.append("""
       
            <h2>High Direct Bilirubin (Conjugated Bilirubin)</h2>
            <h3>Root Cause:</h3>
            <ul>
                <li><strong>Liver Disease:</strong> Direct bilirubin is produced when unconjugated (indirect) bilirubin is processed in the liver and conjugated with glucuronic acid. If the liver is unable to properly conjugate bilirubin or if there is liver damage, direct bilirubin levels can rise.</li>
                <ul>
                    <li>Hepatitis: Inflammation of the liver can impair its ability to conjugate and excrete bilirubin.</li>
                    <li>Cirrhosis: Scarring of the liver tissue can obstruct bile flow and hinder bilirubin processing.</li>
                    <li>Liver Cancer: Tumors or malignancy in the liver can disrupt the normal metabolic process, leading to elevated direct bilirubin levels.</li>
                </ul>
                <li><strong>Biliary Obstruction:</strong> Blockage in the bile ducts (from gallstones, bile duct tumors, or strictures) can prevent conjugated bilirubin from being excreted into the intestine, leading to a buildup of direct bilirubin in the blood.</li>
                <li><strong>Cholestasis:</strong> A condition where bile flow is impaired due to intrahepatic (within the liver) or extrahepatic (outside the liver) causes. This can be seen in diseases like primary biliary cirrhosis or primary sclerosing cholangitis.</li>
                <li><strong>Gallstones:</strong> When gallstones obstruct the bile ducts, it prevents bile from flowing properly, causing the buildup of bilirubin in the bloodstream.</li>
                <li><strong>Rare Genetic Disorders:</strong>
                    <ul>
                        <li>Dubin-Johnson Syndrome</li>
                        <li>Rotor Syndrome</li>
                    </ul>
                </li>
                <li><strong>Liver Toxicity from Medications:</strong> Certain medications, such as anabolic steroids or acetaminophen in high doses, can cause liver damage, impairing bilirubin metabolism.</li>
            </ul>

            <h3>Health Risks of High Direct Bilirubin:</h3>
            <ul>
                <li><strong>Jaundice:</strong> Causes the skin and eyes to turn yellow due to bilirubin accumulation.</li>
                <li><strong>Liver Dysfunction:</strong> Persistent high levels often point to liver dysfunction or bile duct obstruction.</li>
                <li><strong>Cholestasis:</strong> Results in bile buildup, causing itching, fatigue, and digestive issues.</li>
                <li><strong>Gallbladder or Bile Duct Issues:</strong> May require surgical intervention.</li>
            </ul>

            <h3>Tips to Lower High Direct Bilirubin Levels:</h3>
            <ul>
                <li><strong>Treat Underlying Conditions:</strong> Addressing the root cause can help lower direct bilirubin.</li>
                <li><strong>Avoid Alcohol:</strong> Essential if high bilirubin levels are due to liver disease.</li>
                <li><strong>Control Infections:</strong> Treat conditions like hepatitis with antiviral or antibacterial medications.</li>
                <li><strong>Manage Medications:</strong> Consult a healthcare provider about alternative drugs that do not harm the liver.</li>
            </ul>

            <h3>Foods to Eat for High Direct Bilirubin:</h3>
            <ul>
                <li>Leafy Greens: Spinach, kale, and Swiss chard provide antioxidants and help detoxify the liver.</li>
                <li>Cruciferous Vegetables: Broccoli, Brussels sprouts, and cauliflower promote liver detoxification and bile flow.</li>
                <li>Beets: Rich in antioxidants and support liver detoxification.</li>
                <li>Garlic and Onions: Contain sulfur compounds that support liver detoxification.</li>
                <li>Turmeric: Contains curcumin, which has anti-inflammatory properties and supports liver function.</li>
                <li>Green Tea: Packed with antioxidants that aid in detoxification.</li>
            </ul>

            <h3>Example Meal Plan for High Direct Bilirubin:</h3>
            <ul>
                <li>Breakfast: Oatmeal with chia seeds, blueberries, and a handful of walnuts.</li>
                <li>Lunch: Grilled salmon with quinoa, steamed broccoli, and a side of kale salad with olive oil and lemon dressing.</li>
                <li>Snack: A small handful of almonds and green tea.</li>
                <li>Dinner: Grilled chicken breast with roasted beets, sautéed spinach with garlic, and a side of brown rice.</li>
            </ul>
        """)

        if values["Indirect Bilirubin"] > 1:
            advice.append("""
            <h2>High Indirect Bilirubin (Unconjugated Bilirubin)</h2>
            <h3>Root Cause:</h3>
            <ul>
                <li><strong>Hemolysis (Increased Red Blood Cell Breakdown):</strong> The most common cause of elevated indirect bilirubin is the accelerated breakdown of red blood cells. Causes include:
                    <ul>
                        <li><strong>Hemolytic Anemia:</strong> Conditions like sickle cell anemia, thalassemia, autoimmune hemolytic anemia, or infections.</li>
                        <li><strong>Infections:</strong> Malaria and other infections leading to the destruction of red blood cells.</li>
                        <li><strong>Transfusion Reactions:</strong> Incompatible blood transfusions can cause hemolysis and raise indirect bilirubin levels.</li>
                    </ul>
                </li>
                <li><strong>Liver Dysfunction:</strong> Severe liver damage can impair the liver’s ability to process and clear indirect bilirubin.</li>
                <li><strong>Genetic Disorders:</strong>
                    <ul>
                        <li><strong>Gilbert’s Syndrome:</strong> A common genetic disorder with mild elevations during stress, illness, or fasting.</li>
                        <li><strong>Crigler-Najjar Syndrome:</strong> A rare inherited disorder with a deficiency in the enzyme UDP-glucuronosyltransferase.</li>
                    </ul>
                </li>
                <li><strong>Neonatal Jaundice:</strong> Occurs in newborns due to the immature liver's inability to process bilirubin effectively.</li>
                <li><strong>Sepsis or Other Systemic Infections:</strong> Can lead to hemolysis, liver dysfunction, or both.</li>
                <li><strong>Medications:</strong> Certain drugs like chemotherapy agents, some antibiotics, and anti-inflammatory drugs can cause hemolysis or liver damage.</li>
            </ul>

            <h3>Health Risks of High Indirect Bilirubin:</h3>
            <ul>
                <li><strong>Jaundice:</strong> Yellowing of the skin and eyes due to excess bilirubin.</li>
                <li><strong>Anemia:</strong> Excessive red blood cell breakdown leads to symptoms like fatigue, weakness, and shortness of breath.</li>
                <li><strong>Liver Dysfunction:</strong> Symptoms include nausea, loss of appetite, and abdominal pain.</li>
                <li><strong>Neurotoxicity in Neonates:</strong> Extremely high levels in newborns can cause brain damage (kernicterus).</li>
                <li><strong>Fatigue and Weakness:</strong> Often caused by anemia linked to hemolysis.</li>
            </ul>

            <h3>Tips to Lower High Indirect Bilirubin Levels:</h3>
            <ul>
                <li><strong>Treat Underlying Causes:</strong> Address hemolytic anemia, liver dysfunction, or infections.</li>
                <li><strong>Manage Hemolysis:</strong>
                    <ul>
                        <li>Blood Transfusions for severe anemia.</li>
                        <li>Immunosuppressive therapy for autoimmune hemolytic anemia.</li>
                        <li>Iron supplementation to restore red blood cell production.</li>
                    </ul>
                </li>
                <li><strong>Manage Liver Disease:</strong> Treatments include antiviral medications for hepatitis or alcohol cessation for alcoholic liver disease.</li>
                <li><strong>Avoid Stress and Fasting:</strong> Particularly important for Gilbert’s Syndrome patients.</li>
                <li><strong>Monitor Bilirubin Levels in Newborns:</strong> Regular monitoring and treatments like phototherapy or exchange transfusion may be required.</li>
                <li><strong>Adjust Medications:</strong> Consult healthcare providers to switch medications causing bilirubin elevation.</li>
            </ul>

            <h3>Foods to Eat for High Indirect Bilirubin:</h3>
            <ul>
                <li><strong>Liver-Supporting Foods:</strong>
                    <ul>
                        <li>Leafy Greens: Spinach, kale, and other dark green vegetables.</li>
                        <li>Cruciferous Vegetables: Broccoli, cauliflower, and Brussels sprouts.</li>
                        <li>Garlic and Onions: Contain sulfur compounds that support liver detoxification.</li>
                        <li>Beets: Rich in antioxidants and fiber.</li>
                        <li>Turmeric: Contains curcumin, which reduces inflammation and supports detoxification.</li>
                        <li>Green Tea: Packed with antioxidants to support liver function.</li>
                        <li>Berries: High in antioxidants to protect liver cells.</li>
                    </ul>
                </li>
                <li><strong>Foods Rich in Vitamin C:</strong> Citrus fruits, strawberries, and kiwi.</li>
                <li><strong>Iron-Rich Foods:</strong> If hemolysis contributes to anemia, include red meat, lentils, and spinach.</li>
                <li><strong>High-Fiber Foods:</strong> Whole grains, oats, and legumes aid digestion and detoxification.</li>
                <li><strong>Healthy Fats:</strong> Avocados, olive oil, and fatty fish reduce inflammation and support liver health.</li>
            </ul>

            <h3>Example Meal Plan for High Indirect Bilirubin:</h3>
            <ul>
                <li>Breakfast: Oatmeal with chia seeds, fresh berries, and a sprinkle of flaxseeds.</li>
                <li>Lunch: Grilled salmon with steamed broccoli, quinoa, and a spinach salad with olive oil and lemon.</li>
                <li>Snack: A handful of almonds and an orange.</li>
                <li>Dinner: Grilled chicken breast with roasted beets, sautéed kale with garlic, and a side of brown rice.</li>
            </ul>
        """)


    # SGPT/ALT (range: 7-56 U/L)
        if values["SGPT/ALT"] > 50:
            advice.append("""
      
            <h2>High SGPT/ALT (Serum Glutamic Pyruvic Transaminase / Alanine Aminotransferase)</h2>
            <h3>Root Cause:</h3>
            <ul>
                <li><strong>Liver Damage or Disease:</strong> SGPT/ALT is an enzyme found mainly in the liver. Elevated levels typically indicate liver injury or disease. Common causes include:
                    <ul>
                        <li><strong>Hepatitis:</strong> Both viral (Hepatitis B, C, A) and non-viral (autoimmune hepatitis) can lead to liver inflammation and elevated SGPT levels.</li>
                        <li><strong>Fatty Liver Disease:</strong> Fat accumulation in liver cells causing non-alcoholic fatty liver disease (NAFLD).</li>
                        <li><strong>Cirrhosis:</strong> Advanced liver scarring due to chronic liver conditions or excessive alcohol use.</li>
                        <li><strong>Liver Toxicity from Medications:</strong> Drugs like acetaminophen, statins, some antibiotics, and antifungals.</li>
                        <li><strong>Alcoholic Liver Disease:</strong> Excessive alcohol consumption leading to liver inflammation and cell damage.</li>
                        <li><strong>Liver Cancer:</strong> Cancer causing liver cell breakdown.</li>
                        <li><strong>Hemochromatosis:</strong> Excess iron accumulation leading to liver damage.</li>
                        <li><strong>Wilson’s Disease:</strong> A genetic disorder causing copper buildup in the liver.</li>
                        <li><strong>Mononucleosis (Infectious Mono):</strong> Viral infections causing liver inflammation.</li>
                        <li><strong>Cholestasis (Bile Flow Blockage):</strong> Gallstones or bile duct obstructions causing liver stress.</li>
                    </ul>
                </li>
            </ul>

            <h3>Health Risks of High SGPT/ALT:</h3>
            <ul>
                <li><strong>Liver Dysfunction:</strong> Ongoing liver damage leading to complications like cirrhosis or liver failure.</li>
                <li><strong>Jaundice:</strong> Yellowing of the skin and eyes due to bilirubin buildup.</li>
                <li><strong>Fatigue and Weakness:</strong> Difficulty processing nutrients and toxins.</li>
                <li><strong>Ascites:</strong> Fluid accumulation in the abdomen from advanced liver disease.</li>
                <li><strong>Abdominal Pain:</strong> Discomfort in the upper right side of the abdomen.</li>
            </ul>

            <h3>Tips to Lower High SGPT/ALT Levels:</h3>
            <ul>
                <li><strong>Treat Underlying Liver Conditions:</strong> Address the root cause, such as hepatitis, fatty liver disease, or alcohol use.</li>
                <li><strong>Antiviral Medications:</strong> For hepatitis, medications like interferons or nucleoside analogs.</li>
                <li><strong>Weight Loss:</strong> Gradual weight loss (5-10% of body weight) for NAFLD.</li>
                <li><strong>Control Blood Sugar:</strong> For diabetes or insulin resistance, use diet and medications like metformin.</li>
                <li><strong>Avoid Alcohol:</strong> Reduce liver damage by abstaining from alcohol.</li>
                <li><strong>Discontinue Harmful Medications:</strong> Consult your doctor to adjust treatments.</li>
                <li><strong>Manage Iron Overload:</strong> Therapeutic phlebotomy or iron chelation therapy for hemochromatosis.</li>
                <li><strong>Reduce Liver Inflammation:</strong> Use corticosteroids or immunosuppressive drugs for autoimmune hepatitis.</li>
                <li><strong>Follow a Liver-Friendly Diet:</strong> Support liver function with specific foods.</li>
            </ul>

            <h3>Foods to Eat for High SGPT/ALT:</h3>
            <ul>
                <li><strong>Antioxidant-Rich Foods:</strong>
                    <ul>
                        <li>Leafy Greens: Spinach, kale, and collard greens.</li>
                        <li>Berries: Blueberries, strawberries, and raspberries.</li>
                        <li>Beets: High in antioxidants and fiber.</li>
                        <li>Green Tea: Rich in catechins.</li>
                    </ul>
                </li>
                <li><strong>Healthy Fats:</strong> Fatty fish (salmon, mackerel), olive oil, flaxseeds.</li>
                <li><strong>Cruciferous Vegetables:</strong> Broccoli, Brussels sprouts, cauliflower.</li>
                <li><strong>Garlic and Onion:</strong> Rich in sulfur compounds.</li>
                <li><strong>Turmeric:</strong> Contains anti-inflammatory curcumin.</li>
                <li><strong>Fiber-Rich Foods:</strong> Oats, legumes, whole grains.</li>
                <li><strong>Vitamin C-Rich Foods:</strong> Oranges, lemons, grapefruits, kiwi.</li>
                <li><strong>Fresh Ginger:</strong> Anti-inflammatory properties supporting digestion.</li>
            </ul>

            <h3>Example Meal Plan for High SGPT/ALT:</h3>
            <ul>
                <li><strong>Breakfast:</strong> Oatmeal with chia seeds, a handful of mixed berries, and a teaspoon of ground flaxseeds.</li>
                <li><strong>Lunch:</strong> Grilled salmon with steamed broccoli, quinoa, and a spinach salad with olive oil and lemon dressing.</li>
                <li><strong>Snack:</strong> A handful of almonds and a cup of green tea.</li>
                <li><strong>Dinner:</strong> Stir-fried vegetables (beets, kale, and cauliflower) with garlic and turmeric, served with brown rice and roasted chicken.</li>
            </ul>
        """)

    # SGOT/AST (range: 5-40 U/L)
        if values["SGOT/AST"] > 50:
            advice.append("""
    
        
            <h2>High SGOT/AST (Serum Glutamic Oxaloacetic Transaminase / Aspartate Aminotransferase)</h2>
            <h3>Root Cause:</h3>
            <ul>
                <li><strong>Liver Damage or Disease:</strong> SGOT/AST is an enzyme found in the liver and other tissues, such as the heart, muscles, kidneys, and brain. Elevated AST levels indicate damage to these tissues, with the liver being the most common source.</li>
                <li><strong>Hepatitis:</strong> Both viral (e.g., Hepatitis B, C, A) and non-viral (e.g., autoimmune hepatitis) can cause liver inflammation, leading to increased AST levels.</li>
                <li><strong>Fatty Liver Disease (NAFLD):</strong> Non-alcoholic fatty liver disease is caused by fat buildup in the liver, which may lead to liver inflammation and elevated AST.</li>
                <li><strong>Cirrhosis:</strong> Advanced liver scarring (from chronic conditions such as alcohol use or hepatitis) can cause a significant increase in AST levels.</li>
                <li><strong>Alcoholic Liver Disease:</strong> Chronic alcohol consumption can damage liver cells, resulting in increased AST.</li>
                <li><strong>Liver Cancer:</strong> Liver malignancy (either primary or metastasized) can damage liver cells, releasing AST into the bloodstream.</li>
                <li><strong>Muscle Injury or Damage:</strong> AST is also present in muscles. Muscle injuries, trauma, or conditions like rhabdomyolysis (severe muscle breakdown) can cause AST to increase.</li>
                <li><strong>Heart Conditions:</strong> AST is found in high concentrations in the heart, so conditions like myocardial infarction (heart attack) or heart failure can lead to elevated AST levels.</li>
                <li><strong>Hemochromatosis:</strong> A condition characterized by excessive iron buildup in the body, leading to liver damage and higher AST levels.</li>
                <li><strong>Wilson’s Disease:</strong> Genetic disorder leading to copper accumulation in the liver, which can cause AST to rise.</li>
                <li><strong>Mononucleosis (Infectious Mono):</strong> Viral infections can lead to liver inflammation, causing elevated AST.</li>
                <li><strong>Cholestasis:</strong> Obstruction in the bile ducts or gallstones can impair bile flow, stress the liver, and cause an increase in AST levels.</li>
                <li><strong>Medications and Toxins:</strong> Drugs like acetaminophen (in overdose), statins, antibiotics, and antifungals can cause liver damage, raising AST levels.</li>
            </ul>

            <h3>Health Risks of High SGOT/AST:</h3>
            <ul>
                <li><strong>Liver Dysfunction:</strong> High AST levels often suggest liver injury, which can lead to further liver damage if the underlying cause is not addressed.</li>
                <li><strong>Muscle Damage:</strong> If elevated AST is due to muscle injury (e.g., rhabdomyolysis), it can lead to muscle weakness, pain, and potentially kidney failure.</li>
                <li><strong>Heart Damage:</strong> Elevated AST levels due to heart-related issues (e.g., myocardial infarction) can indicate a heart attack or heart failure, requiring urgent medical attention.</li>
                <li><strong>Fatigue and Weakness:</strong> Elevated AST levels associated with liver or muscle damage often lead to fatigue, muscle weakness, and overall reduced energy.</li>
                <li><strong>Jaundice:</strong> Liver dysfunction associated with high AST levels can lead to jaundice, where the skin and eyes turn yellow due to an accumulation of bilirubin.</li>
                <li><strong>Abdominal Pain:</strong> In liver diseases or gallbladder problems, high AST levels can be accompanied by abdominal pain or discomfort, especially in the upper right side.</li>
            </ul>

            <h3>Tips to Lower High SGOT/AST Levels:</h3>
            <ul>
                <li><strong>Treat Underlying Liver Conditions:</strong> Address the root cause of liver dysfunction.</li>
                <li><strong>Antiviral Treatments:</strong> For hepatitis, antiviral medications (such as interferons or nucleoside analogs) may help reduce inflammation.</li>
                <li><strong>Fatty Liver Management:</strong> Gradual weight loss (5-10% of body weight) can reduce liver fat and inflammation, lowering AST levels.</li>
                <li><strong>Alcohol Cessation:</strong> Stopping alcohol consumption is critical if alcohol-related liver disease or cirrhosis is present.</li>
                <li><strong>Managing Iron Overload:</strong> Treatment through phlebotomy (blood removal) or iron chelation therapy may help reduce iron buildup and lower AST.</li>
                <li><strong>Medications Adjustment:</strong> Discontinuing or switching medications causing liver toxicity can prevent further elevation in AST.</li>
                <li><strong>Heart Treatment:</strong> Treatments for heart disease, such as medications or interventions for myocardial infarction, may be needed.</li>
                <li><strong>Muscle Injury Treatment:</strong> Rest, hydration, and care for conditions like rhabdomyolysis are necessary to prevent further damage.</li>
                <li><strong>Avoid Toxins:</strong> Limit exposure to substances that harm the liver, like alcohol and certain drugs.</li>
            </ul>

            <h3>Foods to Eat for High SGOT/AST:</h3>
            <ul>
                <li><strong>Liver-Supporting Foods:</strong>
                    <ul>
                        <li>Leafy Greens: Spinach, kale, and other greens rich in nutrients for liver detoxification.</li>
                        <li>Cruciferous Vegetables: Broccoli, cauliflower, and Brussels sprouts to reduce fat buildup.</li>
                        <li>Beets: High in antioxidants to cleanse the liver and reduce oxidative stress.</li>
                        <li>Turmeric: Anti-inflammatory properties to reduce liver inflammation.</li>
                        <li>Green Tea: Rich in antioxidants that detoxify the body.</li>
                        <li>Berries: Blueberries, strawberries, and raspberries protect liver cells.</li>
                        <li>Omega-3 Fatty Acids: Fatty fish, walnuts, and flaxseeds reduce liver inflammation.</li>
                        <li>Garlic and Onion: Enhance liver detoxification and bile production.</li>
                        <li>Fiber-Rich Foods: Oats, quinoa, and legumes to support digestion and detoxification.</li>
                        <li>Vitamin C-Rich Foods: Citrus fruits, bell peppers, and kiwi for liver function support.</li>
                        <li>Healthy Fats: Olive oil, avocados, and nuts to reduce inflammation.</li>
                    </ul>
                </li>
            </ul>

            <h3>Example Meal Plan for High SGOT/AST:</h3>
            <ul>
                <li><strong>Breakfast:</strong> Oatmeal with chia seeds, mixed berries, and flaxseeds.</li>
                <li><strong>Lunch:</strong> Grilled salmon with steamed broccoli, quinoa, and a spinach salad with olive oil and lemon.</li>
                <li><strong>Snack:</strong> A handful of almonds and a cup of green tea.</li>
                <li><strong>Dinner:</strong> Stir-fried vegetables (beets, kale, Brussels sprouts) with garlic and turmeric, served with brown rice and grilled chicken.</li>
            </ul>
        
        
        """)
    # Alkaline Phosphatase (range: 44-147 U/L)
        if values["Alkaline Phosphatase"] > 115:
            advice.append("""
    
        
            <h2>High Alkaline Phosphatase (ALP)</h2>
            <h3>Root Cause:</h3>
            <ul>
                <li><strong>Liver Conditions:</strong>
                    <ul>
                        <li><strong>Bile Duct Obstruction (Cholestasis):</strong> Blockages in the bile ducts, such as from gallstones, tumors, or strictures, can cause elevated ALP due to its role in bile secretion. Conditions like primary biliary cirrhosis or primary sclerosing cholangitis may also raise ALP levels.</li>
                        <li><strong>Hepatitis:</strong> Liver inflammation caused by viral or autoimmune hepatitis can elevate ALP.</li>
                        <li><strong>Liver Tumors:</strong> Primary or metastatic liver cancer can lead to high ALP levels due to liver cell damage.</li>
                        <li><strong>Fatty Liver Disease:</strong> Non-alcoholic fatty liver disease (NAFLD) can cause mild elevation in ALP levels due to liver inflammation.</li>
                    </ul>
                </li>
                <li><strong>Bone Conditions:</strong>
                    <ul>
                        <li><strong>Osteomalacia and Rickets:</strong> Bone diseases caused by vitamin D deficiency, leading to abnormal bone mineralization and elevated ALP levels.</li>
                        <li><strong>Paget’s Disease of Bone:</strong> A disorder involving abnormal bone remodeling, which can cause elevated ALP.</li>
                        <li><strong>Bone Fractures or Healing:</strong> Temporary rise in ALP due to increased bone activity during healing.</li>
                        <li><strong>Osteoporosis:</strong> In severe cases of bone loss, ALP may be elevated.</li>
                        <li><strong>Bone Cancer or Metastasis:</strong> If cancer has spread to the bones, it can increase ALP production.</li>
                    </ul>
                </li>
                <li><strong>Other Causes:</strong>
                    <ul>
                        <li><strong>Hyperparathyroidism:</strong> Overactivity of the parathyroid glands leading to increased calcium and ALP levels due to bone resorption.</li>
                        <li><strong>Pregnancy:</strong> ALP levels often rise during the third trimester due to placental production.</li>
                        <li><strong>Infections:</strong> Conditions like osteomyelitis (bone infection) or infectious mononucleosis can elevate ALP levels.</li>
                    </ul>
                </li>
            </ul>

            <h3>Health Risks of High ALP:</h3>
            <ul>
                <li><strong>Liver Dysfunction:</strong> Persistently high ALP may indicate liver damage or bile duct obstruction, leading to jaundice, abdominal pain, or severe liver conditions.</li>
                <li><strong>Bone Weakness or Pain:</strong> High ALP related to bone disease can cause deformities, fractures, or pain.</li>
                <li><strong>Hypercalcemia:</strong> Conditions like hyperparathyroidism or osteolytic bone disease can lead to elevated calcium levels, causing symptoms like nausea, fatigue, kidney stones, and bone pain.</li>
            </ul>

            <h3>Tips to Lower High ALP:</h3>
            <ul>
                <li><strong>Treat Underlying Liver Diseases:</strong> Address liver conditions such as viral hepatitis, cirrhosis, or fatty liver disease to restore normal ALP levels.</li>
                <li><strong>Manage Bone Conditions:</strong> Correct vitamin D deficiency and manage diseases like Paget’s disease or osteomalacia with medications, supplements (like calcium or vitamin D), and lifestyle changes.</li>
                <li><strong>Surgical Intervention for Blockages:</strong> Remove bile duct obstructions (e.g., gallstones or tumors) through surgical or non-surgical methods to lower ALP levels.</li>
                <li><strong>Avoid Alcohol:</strong> Reducing alcohol consumption supports liver health and prevents further elevation of ALP.</li>
                <li><strong>Calcium Regulation:</strong> Normalize calcium levels through treatment for hyperparathyroidism or bone loss with appropriate interventions.</li>
            </ul>

            <h3>Foods to Eat for High ALP:</h3>
            <ul>
                <li><strong>Liver-Supportive Foods:</strong>
                    <ul>
                        <li><strong>Leafy Greens:</strong> Spinach, kale, and other dark leafy greens support liver health.</li>
                        <li><strong>Berries:</strong> Blueberries and strawberries are rich in antioxidants that protect the liver and reduce inflammation.</li>
                        <li><strong>Garlic and Turmeric:</strong> Anti-inflammatory properties improve liver detoxification.</li>
                        <li><strong>Fatty Fish:</strong> Omega-3-rich fish like salmon, mackerel, and sardines help reduce inflammation in the liver and bones.</li>
                    </ul>
                </li>
                <li><strong>Bone-Healthy Foods:</strong>
                    <ul>
                        <li><strong>Dairy:</strong> Calcium-rich foods like milk, yogurt, and cheese support bone health.</li>
                        <li><strong>Fortified Foods:</strong> Vitamin D-fortified cereals or plant-based milk for healthy bone metabolism.</li>
                        <li><strong>Nuts and Seeds:</strong> Almonds, chia seeds, and flaxseeds provide magnesium for bone and muscle health.</li>
                    </ul>
                </li>
            </ul>
        
        
        """)
        elif values["Alkaline Phosphatase"] < 43:
            advice.append("""
    
        
            <h2>Low Alkaline Phosphatase (ALP)</h2>
            <h3>Root Cause:</h3>
            <ul>
                <li><strong>Malnutrition:</strong> Inadequate intake of nutrients, especially protein, zinc, or vitamin C, can lower ALP levels.</li>
                <li><strong>Hypothyroidism:</strong> An underactive thyroid can reduce metabolic activity, leading to decreased ALP production.</li>
                <li><strong>Magnesium Deficiency:</strong> Low magnesium levels can impair enzyme function, including ALP.</li>
                <li><strong>Wilson’s Disease:</strong> A rare genetic disorder causing copper accumulation in tissues can lower ALP levels.</li>
                <li><strong>Pernicious Anemia:</strong> A deficiency of vitamin B12 or folate can contribute to low ALP.</li>
                <li><strong>Severe Illness or Chronic Conditions:</strong> Chronic illnesses like celiac disease or inflammatory disorders may result in low ALP levels.</li>
                <li><strong>Age:</strong> Lower ALP levels can naturally occur in older adults.</li>
            </ul>

            <h3>Health Risks of Low ALP:</h3>
            <ul>
                <li><strong>Bone Weakness:</strong> Insufficient ALP can impair bone mineralization, leading to weaker bones and a higher risk of fractures.</li>
                <li><strong>Delayed Wound Healing:</strong> ALP is essential for proper cell turnover, so low levels may slow healing processes.</li>
                <li><strong>Fatigue and Weakness:</strong> Nutritional deficiencies linked to low ALP can contribute to tiredness and muscle weakness.</li>
            </ul>

            <h3>Tips to Increase Low ALP:</h3>
            <ul>
                <li><strong>Improve Nutrition:</strong> Ensure a balanced diet rich in protein, zinc, vitamin C, and magnesium.</li>
                <li><strong>Treat Underlying Conditions:</strong> Address thyroid issues, Wilson’s disease, or any other underlying medical conditions with appropriate treatments.</li>
                <li><strong>Vitamin and Mineral Supplements:</strong> Take supplements for nutrients like zinc, magnesium, or vitamin B12 if deficiencies are diagnosed.</li>
                <li><strong>Regular Exercise:</strong> Engage in weight-bearing exercises to promote bone health and overall metabolic activity.</li>
            </ul>

            <h3>Foods to Eat for Low ALP:</h3>
            <ul>
                <li><strong>Protein-Rich Foods:</strong> Include lean meats, fish, eggs, and legumes to improve overall enzyme function.</li>
                <li><strong>Zinc-Rich Foods:</strong> Shellfish, nuts, seeds, and whole grains are excellent sources of zinc.</li>
                <li><strong>Vitamin C-Rich Foods:</strong> Oranges, strawberries, bell peppers, and kiwi support overall health and enzyme production.</li>
                <li><strong>Magnesium-Rich Foods:</strong> Dark leafy greens, nuts, seeds, and whole grains help boost enzyme activity.</li>
                <li><strong>Fortified Foods:</strong> Include cereals and dairy products fortified with essential nutrients.</li>
            </ul>
        
        
        """)

    # Total Protein (range: 6.0-8.3 g/dL)
        if values["Total Protein"] < 6.6:
            advice.append("""
    
        
            <h2>Low Total Protein</h2>
            <h3>Root Cause:</h3>
            <ul>
                <li><strong>Malnutrition or Poor Diet:</strong> Inadequate protein intake due to malnutrition, eating disorders, or insufficient dietary intake.</li>
                <li><strong>Starvation:</strong> Prolonged lack of calorie or nutrient intake can reduce protein production.</li>
                <li><strong>Liver Conditions:</strong> Cirrhosis or hepatitis impairs the liver’s ability to produce proteins like albumin.</li>
                <li><strong>Kidney Diseases:</strong> Chronic kidney disease or nephrotic syndrome leads to excessive protein loss in urine.</li>
                <li><strong>Malabsorption Syndromes:</strong> Conditions like celiac disease or Crohn’s disease prevent proper protein absorption.</li>
                <li><strong>Sepsis:</strong> Severe infections can decrease protein synthesis.</li>
                <li><strong>Burns or Trauma:</strong> Protein loss occurs as the body uses proteins for healing and repair.</li>
                <li><strong>Hypothyroidism:</strong> An underactive thyroid can lower protein metabolism and levels.</li>
            </ul>

            <h3>Health Risks of Low Total Protein:</h3>
            <ul>
                <li><strong>Edema:</strong> Low albumin levels can cause fluid retention in the legs, abdomen, and other areas.</li>
                <li><strong>Weak Immune Function:</strong> Proteins are essential for immune defense, and deficiencies weaken it.</li>
                <li><strong>Muscle Weakness:</strong> Low protein levels contribute to fatigue and reduced muscle strength.</li>
                <li><strong>Delayed Wound Healing:</strong> Proteins are crucial for tissue repair; deficiencies slow the healing process.</li>
                <li><strong>Growth Issues:</strong> In children, low protein levels impair growth and development.</li>
            </ul>

            <h3>Tips to Raise Low Total Protein:</h3>
            <ul>
                <li><strong>Increase Protein Intake:</strong> Include protein-rich foods such as lean meats, fish, eggs, dairy, legumes, and nuts in your diet.</li>
                <li><strong>Address Malabsorption Issues:</strong> Treat conditions like celiac or Crohn’s disease to improve nutrient absorption.</li>
                <li><strong>Manage Liver or Kidney Diseases:</strong> Use appropriate medications and lifestyle changes as advised by a healthcare provider.</li>
                <li><strong>Treat Hypothyroidism:</strong> Hormone therapy can improve protein metabolism.</li>
            </ul>

            <h3>Foods to Eat for Low Total Protein:</h3>
            <ul>
                <li><strong>Eggs and Lean Meats:</strong> Chicken, turkey, and lean beef are excellent protein sources.</li>
                <li><strong>Fish:</strong> Salmon, tuna, and shellfish provide high-quality protein and healthy fats.</li>
                <li><strong>Legumes:</strong> Lentils, beans, and chickpeas are great plant-based options.</li>
                <li><strong>Nuts and Seeds:</strong> Almonds, sunflower seeds, and chia seeds are rich in protein and healthy fats.</li>
                <li><strong>Dairy Products:</strong> Milk, Greek yogurt, and cheese are high in protein.</li>
            </ul>
        
        
        """)

        elif values["Total Protein"] > 8.3:
            advice.append("""
    
        
            <h2>High Total Protein</h2>
            <h3>Root Cause:</h3>
            <ul>
                <li><strong>Chronic Infections or Inflammatory Conditions:</strong> Conditions like tuberculosis, HIV/AIDS, rheumatoid arthritis, or lupus can increase antibody production.</li>
                <li><strong>Multiple Myeloma:</strong> A type of blood cancer causing abnormal plasma cell production of immunoglobulins.</li>
                <li><strong>Dehydration:</strong> Reduced blood plasma volume can make protein concentration appear higher.</li>
                <li><strong>Monoclonal Gammopathy:</strong> Disorders like MGUS or Waldenström’s macroglobulinemia increase abnormal protein levels.</li>
                <li><strong>Liver Conditions:</strong> Chronic liver diseases, such as cirrhosis or hepatitis, can raise total protein levels.</li>
                <li><strong>Nephrotic Syndrome:</strong> The body compensates for kidney-related protein loss by producing excess proteins.</li>
            </ul>

            <h3>Health Risks of High Total Protein:</h3>
            <ul>
                <li><strong>Multiple Myeloma:</strong> High protein levels may indicate plasma cell disorders like multiple myeloma or Waldenström’s macroglobulinemia.</li>
                <li><strong>Dehydration:</strong> Prolonged dehydration can cause electrolyte imbalances and kidney strain.</li>
                <li><strong>Liver or Kidney Damage:</strong> Elevated protein levels may reflect worsening liver or kidney conditions.</li>
            </ul>

            <h3>Tips to Lower High Total Protein:</h3>
            <ul>
                <li><strong>Address Underlying Conditions:</strong> Treat infections, inflammation, or blood cancers to normalize protein levels.</li>
                <li><strong>Stay Hydrated:</strong> Proper hydration can reduce protein concentration related to dehydration.</li>
                <li><strong>Manage Inflammation:</strong> Use anti-inflammatory medications or dietary changes to control inflammation.</li>
            </ul>

            <h3>Foods to Eat for High Total Protein:</h3>
            <ul>
                <li><strong>Antioxidant-Rich Foods:</strong> Berries and leafy greens help reduce inflammation.</li>
                <li><strong>Omega-3-Rich Foods:</strong> Salmon, walnuts, and flaxseeds provide anti-inflammatory benefits.</li>
                <li><strong>Hydration:</strong> Drink plenty of water to maintain proper fluid balance.</li>
            </ul>
        
        
        """)

    # Albumin (range: 3.5-5.0 g/dL)
        if values["Albumin"] < 3.5:
            advice.append("""
    
        
            <h2>Low Albumin (Hypoalbuminemia)</h2>
            <h3>Root Cause:</h3>
            <ul>
                <li><strong>Cirrhosis or Hepatitis:</strong> Chronic liver conditions impair albumin production.</li>
                <li><strong>Acute Liver Failure:</strong> Sudden liver damage due to toxins, infections, or medications.</li>
                <li><strong>Nephrotic Syndrome:</strong> A kidney disorder causing significant loss of albumin through urine.</li>
                <li><strong>Chronic Kidney Disease:</strong> Progressive kidney damage reducing albumin retention.</li>
                <li><strong>Protein Deficiency:</strong> Inadequate dietary protein intake due to malnutrition or eating disorders.</li>
                <li><strong>Inflammation and Infection:</strong> Conditions like rheumatoid arthritis, lupus, or sepsis impair albumin synthesis.</li>
                <li><strong>Malabsorption Syndromes:</strong> Issues like Celiac disease or Crohn’s disease impair protein absorption.</li>
                <li><strong>Protein-Losing Enteropathy:</strong> Loss of protein through the intestines.</li>
                <li><strong>Congestive Heart Failure:</strong> Fluid retention dilutes albumin levels.</li>
                <li><strong>Burns or Trauma:</strong> Protein loss from severe injuries or burns.</li>
            </ul>

            <h3>Health Risks of Low Albumin:</h3>
            <ul>
                <li><strong>Edema:</strong> Swelling in legs, abdomen, or around the eyes due to fluid buildup.</li>
                <li><strong>Weakened Immune System:</strong> Reduced albumin impairs immune response.</li>
                <li><strong>Muscle Weakness:</strong> Fatigue and reduced muscle recovery.</li>
                <li><strong>Impaired Wound Healing:</strong> Slower recovery from injuries or surgeries.</li>
                <li><strong>Hypotension:</strong> Low blood pressure due to poor fluid retention in the bloodstream.</li>
            </ul>

            <h3>Tips to Raise Low Albumin:</h3>
            <ul>
                <li><strong>Increase Protein Intake:</strong> Consume high-quality protein sources:
                    <ul>
                        <li>Animal-Based Proteins: Lean meats (chicken, turkey), fish, eggs, and dairy products.</li>
                        <li>Plant-Based Proteins: Beans, lentils, quinoa, tofu, nuts, and seeds.</li>
                    </ul>
                </li>
                <li><strong>Treat Underlying Liver or Kidney Diseases:</strong> Follow medical advice, including medications or lifestyle changes.</li>
                <li><strong>Address Malabsorption or Inflammation:</strong> Manage conditions like celiac disease or Crohn’s disease.</li>
                <li><strong>Hydration:</strong> Ensure adequate hydration but avoid overhydration in kidney or heart conditions.</li>
            </ul>

            <h3>Foods to Eat for Low Albumin:</h3>
            <ul>
                <li><strong>Protein-Rich Foods:</strong> Eggs, lean meats, fish, and dairy products.</li>
                <li><strong>Nuts and Seeds:</strong> Almonds, chia seeds, and sunflower seeds.</li>
                <li><strong>Legumes:</strong> Lentils, chickpeas, and beans.</li>
                <li><strong>Vitamins and Minerals:</strong> Leafy greens, sweet potatoes, carrots, and citrus fruits to support overall nutrition.</li>
            </ul>
        
        
        """)

        elif values["Albumin"] > 5.2:
            advice.append("""
    
        
            <h2>High Albumin (Hyperalbuminemia)</h2>
            <h3>Root Cause:</h3>
            <ul>
                <li><strong>Severe Dehydration:</strong> Loss of fluids due to vomiting, diarrhea, or sweating reduces blood volume and increases albumin concentration.</li>
                <li><strong>Excessive Protein Intake:</strong> Rarely, very high protein intake can slightly elevate albumin levels.</li>
                <li><strong>Gastrointestinal Bleeding:</strong> Blood loss reduces plasma volume, increasing albumin concentration.</li>
                <li><strong>HIV/AIDS:</strong> In some cases, immune response to infections elevates albumin levels.</li>
                <li><strong>Anabolic Steroid Use:</strong> Steroids or certain medications can increase albumin levels.</li>
                <li><strong>Polycythemia Vera:</strong> A blood disorder causing increased red blood cells and reduced plasma volume.</li>
            </ul>

            <h3>Health Risks of High Albumin:</h3>
            <ul>
                <li><strong>Dehydration:</strong> Chronic dehydration can lead to kidney stones, electrolyte imbalances, and kidney damage.</li>
                <li><strong>Increased Blood Viscosity:</strong> Elevated albumin thickens blood, increasing the risk of clots and cardiovascular issues.</li>
                <li><strong>Impaired Circulation:</strong> High albumin reduces oxygen and nutrient flow, potentially affecting organ function.</li>
            </ul>

            <h3>Tips to Lower High Albumin:</h3>
            <ul>
                <li><strong>Increase Fluid Intake:</strong> Rehydrate with water, coconut water, or herbal teas. Aim for 6-8 cups daily or more if needed.</li>
                <li><strong>Monitor Protein Intake:</strong> Moderate excessive protein consumption, particularly from supplements.</li>
                <li><strong>Address Underlying Conditions:</strong> Treat dehydration, bleeding, or other causes to normalize albumin levels.</li>
            </ul>

            <h3>Foods to Eat for High Albumin:</h3>
            <ul>
                <li><strong>Hydration:</strong> Water, coconut water, and herbal teas help rehydrate.</li>
                <li><strong>Electrolyte-Rich Foods:</strong> Bananas, oranges, spinach, and potatoes maintain fluid balance and hydration.</li>
            </ul>
        
        
        """)

    # Globulin (range: 2.0-3.5 g/dL)
        if values["Globulin"] < 1.8:
            advice.append("""
    
        
            <h2>Low Globulin (Hypoglobulinemia)</h2>
            <h3>Root Cause:</h3>
            <ul>
                <li><strong>Liver Cirrhosis:</strong> Impaired production of globulins due to liver damage.</li>
                <li><strong>Acute Liver Failure:</strong> Severe liver damage reduces globulin synthesis.</li>
                <li><strong>Nephrotic Syndrome:</strong> Kidney disorders leading to protein loss through urine.</li>
                <li><strong>Gastrointestinal Disorders:</strong> Protein-losing enteropathy causing globulin loss through intestines.</li>
                <li><strong>Severe Burns or Trauma:</strong> Protein loss from tissue repair needs.</li>
                <li><strong>Primary Immunodeficiencies:</strong> Inherited conditions impairing immunoglobulin production.</li>
                <li><strong>Immunosuppressive Therapy:</strong> Reduced globulin production due to immune-suppressing medications.</li>
                <li><strong>Protein Deficiency:</strong> Inadequate dietary protein intake or malnutrition.</li>
                <li><strong>Aplastic Anemia:</strong> Bone marrow not producing sufficient blood cells, including globulins.</li>
                <li><strong>Acute and Chronic Infections:</strong> Reduced globulin levels due to immune and liver function impairment.</li>
                <li><strong>Chronic Inflammatory Diseases:</strong> Conditions like lupus or rheumatoid arthritis affecting immune function.</li>
            </ul>

            <h3>Health Risks of Low Globulin:</h3>
            <ul>
                <li><strong>Weakened Immune System:</strong> Increased susceptibility to infections.</li>
                <li><strong>Edema:</strong> Fluid accumulation in tissues due to reduced globulin levels.</li>
                <li><strong>Delayed Healing:</strong> Impaired wound healing due to insufficient immunoglobulins.</li>
                <li><strong>Bleeding Risks:</strong> Impaired blood clotting mechanisms.</li>
            </ul>

            <h3>Tips to Raise Low Globulin:</h3>
            <ul>
                <li><strong>Increase Protein Intake:</strong> Add high-quality proteins such as lean meats, fish, eggs, beans, and dairy products.</li>
                <li><strong>Treat Underlying Conditions:</strong> Address liver, kidney, or immune system disorders through medical intervention.</li>
                <li><strong>Immunoglobulin Replacement:</strong> Consider therapy for immunoglobulin deficiencies under medical supervision.</li>
                <li><strong>Manage Inflammatory Conditions:</strong> Use anti-inflammatory medications or biologics as prescribed.</li>
            </ul>

            <h3>Foods to Eat for Low Globulin:</h3>
            <ul>
                <li><strong>Protein-Rich Foods:</strong> Eggs, lean meats, fish, tofu, and legumes.</li>
                <li><strong>Nuts and Seeds:</strong> Almonds, walnuts, chia seeds, and sunflower seeds.</li>
                <li><strong>Whole Grains:</strong> Quinoa and oats for plant-based protein.</li>
                <li><strong>Vitamins and Minerals:</strong> Leafy greens, citrus fruits, and berries to support immune function.</li>
            </ul>
        
        
        """)

        elif values["Globulin"] > 3.6:
            advice.append("""
    
        
            <h2>High Globulin (Hyperglobulinemia)</h2>
            <h3>Root Cause:</h3>
            <ul>
                <li><strong>Chronic Bacterial Infections:</strong> Persistent infections like tuberculosis or endocarditis triggering antibody production.</li>
                <li><strong>Viral Infections:</strong> Conditions like hepatitis or HIV increasing globulin levels.</li>
                <li><strong>Autoimmune Diseases:</strong> Rheumatoid arthritis or lupus causing elevated globulin production.</li>
                <li><strong>Multiple Myeloma:</strong> Cancer of plasma cells leading to excess immunoglobulin production.</li>
                <li><strong>Chronic Liver Disease:</strong> Liver damage increasing globulin levels due to inflammation.</li>
                <li><strong>Monoclonal Gammopathy:</strong> Abnormal proteins causing increased globulin levels.</li>
                <li><strong>Dehydration:</strong> Reduced plasma volume concentrating globulins.</li>
                <li><strong>Bone Marrow Disorders:</strong> Conditions like Waldenström's macroglobulinemia producing excess immunoglobulins.</li>
            </ul>

            <h3>Health Risks of High Globulin:</h3>
            <ul>
                <li><strong>Chronic Inflammation:</strong> Tissue damage due to excessive immune response.</li>
                <li><strong>Kidney Damage:</strong> Excessive immunoglobulins leading to kidney strain, particularly in multiple myeloma.</li>
                <li><strong>Blood Clotting Risks:</strong> Increased blood viscosity elevating clotting risks.</li>
            </ul>

            <h3>Tips to Lower High Globulin:</h3>
            <ul>
                <li><strong>Treat Underlying Conditions:</strong> Use antibiotics, antivirals, or immunosuppressants as needed.</li>
                <li><strong>Cancer Management:</strong> Chemotherapy or targeted therapies for conditions like multiple myeloma.</li>
                <li><strong>Hydration:</strong> Ensure adequate water intake to normalize globulin concentration.</li>
                <li><strong>Manage Chronic Inflammation:</strong> Use anti-inflammatory diets or prescribed medications.</li>
                <li><strong>Plasmapheresis:</strong> Medical procedures to remove excess globulins in severe cases.</li>
            </ul>

            <h3>Foods to Eat for High Globulin:</h3>
            <ul>
                <li><strong>Anti-Inflammatory Foods:</strong> Omega-3 rich foods like salmon, walnuts, and flaxseeds.</li>
                <li><strong>Antioxidant-Rich Foods:</strong> Berries, leafy greens, and cruciferous vegetables.</li>
                <li><strong>Hydration:</strong> Water, coconut water, and electrolyte-rich drinks.</li>
                <li><strong>Spices:</strong> Turmeric, ginger, and garlic to combat inflammation.</li>
            </ul>
        
        
        """)

        # Protein A/G Ratio (range: 1.0-2.5)
        if values["Protein A/G Ratio"] < 0.8:
            advice.append("""
        <div style="font-family: Arial, sans-serif; font-size: 14px;">
            <h2>Low Protein A/G Ratio</h2>
            <p>A low A/G ratio occurs when the globulin levels are higher than albumin levels. This imbalance may indicate an underlying health problem.</p>

            <h4>Root Cause:</h4>
            <ul>
                <li><strong>Chronic Inflammatory Diseases:</strong> Conditions like rheumatoid arthritis or systemic lupus erythematosus (SLE) may result in increased globulin levels due to chronic immune system activation and inflammation.</li>
                <li><strong>Chronic Infections:</strong> Tuberculosis, chronic hepatitis, or viral infections can increase globulin production (specifically immunoglobulins), leading to a decrease in the A/G ratio.</li>
                <li><strong>Cirrhosis:</strong> Cirrhosis and other chronic liver diseases can affect the liver’s ability to produce albumin, leading to lower albumin levels and, consequently, a reduced A/G ratio.</li>
                <li><strong>Hepatitis:</strong> Hepatitis or liver inflammation may also contribute to a reduced albumin synthesis, lowering the A/G ratio.</li>
                <li><strong>Nephrotic Syndrome:</strong> In this condition, there is significant protein loss through the kidneys, particularly albumin. This can lead to a lower A/G ratio due to the relative increase in globulins compared to albumin.</li>
                <li><strong>Multiple Myeloma:</strong> A cancer of the plasma cells in the bone marrow, which produces immunoglobulins (antibodies), can significantly increase globulin levels, leading to a lower A/G ratio.</li>
                <li><strong>Waldenström's Macroglobulinemia:</strong> A condition that involves the production of excess immunoglobulin M (IgM), also elevates globulin levels and can result in a low A/G ratio.</li>
                <li><strong>Autoimmune Diseases:</strong> Lupus and Rheumatoid Arthritis: Autoimmune diseases trigger the immune system to produce more globulins (especially antibodies), which can overwhelm albumin production, leading to a low A/G ratio.</li>
                <li><strong>Protein Deficiency:</strong> Insufficient dietary protein intake can lead to low albumin production, while globulin levels may remain normal or even rise due to inflammation or immune response, lowering the A/G ratio.</li>
                <li><strong>Protein-Losing Enteropathy:</strong> Conditions like Crohn’s disease or celiac disease, which cause protein loss from the intestines, may result in decreased albumin levels while globulin levels remain normal or increase.</li>
                <li><strong>Acute Inflammatory Conditions:</strong> Acute infections or inflammatory conditions (e.g., sepsis) can cause a temporary drop in albumin levels while globulins rise as part of the body’s immune response.</li>
            </ul>

            <h4>Health Risks of Low A/G Ratio:</h4>
            <ul>
                <li><strong>Weakened Immune System:</strong> A high globulin level (due to chronic inflammation or infection) may indicate overactivation of the immune system, which can cause tissue damage.</li>
                <li><strong>Liver Dysfunction:</strong> Low albumin levels suggest impaired liver function, which can result in edema, ascites, and poor nutrient absorption.</li>
                <li><strong>Kidney Problems:</strong> Low albumin levels due to kidney conditions can lead to fluid retention, edema, and complications such as high blood pressure or heart failure.</li>
                <li><strong>Chronic Inflammation:</strong> A prolonged low A/G ratio may reflect persistent inflammatory or autoimmune disorders, which can lead to damage to tissues and organs.</li>
            </ul>

            <h4>Tips to Raise A/G Ratio (Normalize Albumin Levels):</h4>
            <ul>
                <li><strong>Increase Protein Intake:</strong> Ensure a sufficient intake of high-quality proteins to boost albumin levels.</li>
                <li><strong>Animal-Based Proteins:</strong> Include eggs, lean meats (chicken, turkey), fish, and dairy products.</li>
                <li><strong>Plant-Based Proteins:</strong> Lentils, beans, tofu, quinoa, and nuts are good sources.</li>
                <li><strong>Manage Underlying Conditions:</strong> Treat liver diseases (e.g., hepatitis or cirrhosis) or kidney diseases (e.g., nephrotic syndrome) with appropriate medications.</li>
                <li><strong>Anti-Inflammatory Diet:</strong> Focus on anti-inflammatory foods such as fatty fish (salmon, mackerel), olive oil, and turmeric.</li>
                <li>Avoid processed foods and excessive sugar intake to prevent chronic inflammation.</li>
                <li><strong>Hydration and Electrolyte Balance:</strong> Maintain proper hydration to support kidney and liver function, and to prevent fluid retention, which could affect albumin production.</li>
            </ul>

            <h4>Foods to Eat for Low A/G Ratio:</h4>
            <ul>
                <li><strong>Protein-Rich Foods:</strong> Chicken, fish, eggs, legumes (lentils, beans), tofu, quinoa, and nuts.</li>
                <li><strong>Anti-Inflammatory Foods:</strong> Leafy greens, citrus fruits, fatty fish, turmeric, and ginger.</li>
                <li><strong>Liver-Supportive Foods:</strong> Garlic, cruciferous vegetables (broccoli, cauliflower), and green tea.</li>
            </ul>
        </div>
        """)
        elif values["Protein A/G Ratio"] > 2:
            advice.append("""
        <div style="font-family: Arial, sans-serif; font-size: 14px;">
            <h2>High Protein A/G Ratio</h2>
            <p>A high A/G ratio occurs when the albumin levels are disproportionately higher than globulin levels, often because globulin levels are abnormally low.</p>

            <h4>Root Cause:</h4>
            <ul>
                <li><strong>Severe Dehydration:</strong> In cases of dehydration, the blood volume decreases, which can result in an increase in the concentration of albumin relative to globulins. This can cause a higher A/G ratio.</li>
                <li><strong>Chronic Liver Disease (in early stages):</strong> Early stages of liver disease may result in a decrease in globulin production while albumin production is maintained or slightly reduced, leading to a higher A/G ratio.</li>
                <li><strong>Malnutrition (with low globulin levels):</strong> Severe malnutrition or protein deficiency might lead to low globulin production, which can raise the A/G ratio if albumin levels are adequate.</li>
                <li><strong>Genetic Disorders:</strong> Certain rare genetic disorders, such as selective immunoglobulin deficiencies (e.g., IgA deficiency), may cause low globulin levels, leading to an elevated A/G ratio.</li>
                <li><strong>Kidney Disease (with protein loss):</strong> In some kidney diseases like Minimal Change Disease or Focal Segmental Glomerulosclerosis (FSGS), the loss of globulins from the body might lead to a higher A/G ratio, although this is rare.</li>
                <li><strong>Multiple Myeloma (Early Stages):</strong> In the early stages of multiple myeloma, there may be a relative decrease in globulins, especially in the absence of hyperviscosity symptoms, leading to an elevated A/G ratio.</li>
                <li><strong>Diabetes:</strong> In some cases of diabetes, particularly poorly managed diabetes, high albumin levels relative to globulins may be observed due to the body’s metabolic changes affecting protein levels.</li>
                <li><strong>Hyperthyroidism:</strong> In hyperthyroidism, where the metabolism is increased, albumin production may remain high while globulin levels may not increase as much, causing a higher A/G ratio.</li>
            </ul>

            <h4>Health Risks of High A/G Ratio:</h4>
            <ul>
                <li><strong>Dehydration:</strong> The most common cause of a high A/G ratio, dehydration, can lead to complications like kidney stones, blood clots, and electrolyte imbalances.</li>
                <li><strong>Nutritional Deficiencies:</strong> If malnutrition is causing low globulin levels, this can increase the risk of infections and delayed healing due to an impaired immune system.</li>
                <li><strong>Immune Deficiencies:</strong> Low globulin levels can result in an increased risk of infections as there are fewer antibodies available to fight pathogens.</li>
            </ul>

            <h4>Tips to Lower A/G Ratio (Normalize Globulin Levels):</h4>
            <ul>
                <li><strong>Hydrate Properly:</strong> Drink adequate water to ensure proper fluid balance and to help prevent the concentration of albumin due to dehydration.</li>
                <li><strong>Address Malnutrition:</strong> If malnutrition or protein deficiency is the cause, ensure adequate intake of essential nutrients and proteins, focusing on protein-rich foods (like eggs, meats, legumes) to help normalize globulin levels.</li>
                <li><strong>Treat Underlying Conditions:</strong> Manage conditions like liver disease, kidney disease, and hyperthyroidism to ensure that globulin production is not impaired and the A/G ratio is normalized.</li>
                <li><strong>Manage Inflammatory or Immune Conditions:</strong> If autoimmune conditions or infections are causing changes in globulin levels, treat the underlying condition to bring globulin levels back to a normal range.</li>
            </ul>

            <h4>Foods to Eat for High A/G Ratio:</h4>
            <ul>
                <li><strong>Hydration:</strong> Drink water, coconut water, and electrolyte-rich beverages.</li>
                <li><strong>Protein-Rich Foods:</strong> Increase protein intake with lean meats, fish, legumes, tofu, and nuts.</li>
                <li><strong>Anti-Inflammatory Foods:</strong> Incorporate foods like turmeric, ginger, and green leafy vegetables to help manage immune response and inflammation.</li>
            </ul>
        """)

    # Creatinine (range: 0.6-1.2 mg/dL)
        if values["Creatinine"] < 0.7:
            advice.append("""<h2>Low Creatinine (Hypocreatininemia)</h2>
<p>A low creatinine level is typically rare and is often associated with specific medical conditions or factors that affect muscle mass, kidney function, or hydration.</p>

<h4>Root Causes of Low Creatinine:</h4>
<ul>
    <li><strong>Reduced Muscle Mass:</strong>
        <ul>
            <li><strong>Aging:</strong> As people age, muscle mass tends to decrease, which can result in lower creatinine production.</li>
            <li><strong>Muscle Wasting Conditions:</strong> Diseases such as muscular dystrophy, sarcopenia (age-related muscle loss), or polymyositis can result in reduced muscle mass and, consequently, low creatinine production.</li>
            <li><strong>Malnutrition:</strong> Inadequate nutrition, particularly a deficiency in proteins and calories, can lead to muscle loss and lower creatinine levels.</li>
            <li><strong>Severe Weight Loss:</strong> Unintentional or rapid weight loss due to illness or extreme dieting can also reduce muscle mass, causing lower creatinine levels.</li>
        </ul>
    </li>
    <li><strong>Pregnancy:</strong> Increased Blood Volume during pregnancy, blood volume increases, and the kidneys filter more blood. This can lead to a dilution of creatinine levels, causing them to appear lower than normal.</li>
    <li><strong>Chronic Liver Disease:</strong> In advanced liver cirrhosis or other liver conditions, muscle protein synthesis is often reduced, leading to lower muscle mass and lower creatinine production.</li>
    <li><strong>Overhydration:</strong> Excessive fluid intake or hyperhydration can dilute blood creatinine levels, making them appear lower than usual.</li>
    <li><strong>Acute and Chronic Kidney Disease (in very early stages):</strong> In rare cases, especially in the early stages of kidney disease, the kidneys may not filter creatinine efficiently, causing blood creatinine levels to remain at lower levels. However, this is less common as creatinine typically rises as kidney function worsens.</li>
    <li><strong>Use of Certain Medications:</strong> Corticosteroids or anabolic steroids can cause a shift in muscle mass and might lower creatinine levels, though this is not common.</li>
    <li><strong>Dietary Factors:</strong> A vegetarian or vegan diet might result in slightly lower creatinine levels because plant-based diets often contain less creatine than meat-based diets. Creatine is the precursor to creatinine, and without sufficient intake, creatinine production may be lower.</li>
</ul>

<h4>Health Risks of Low Creatinine:</h4>
<ul>
    <li><strong>Muscle Loss:</strong> Low creatinine levels can indicate decreased muscle mass, which can result in weakness, frailty, and decreased mobility, particularly in elderly individuals.</li>
    <li><strong>Nutritional Deficiencies:</strong> Chronic low creatinine levels due to poor nutrition can signal deficiencies in essential nutrients like protein.</li>
    <li><strong>Potential Kidney Dysfunction:</strong> Although less common, abnormally low creatinine can sometimes be seen in the early stages of kidney disease. This requires further investigation to determine the cause.</li>
</ul>

<h4>Tips to Increase Creatinine Levels:</h4>
<ul>
    <li><strong>Increase Muscle Mass:</strong> Engage in strength training or resistance exercises to build muscle mass. This can naturally increase creatinine production.</li>
    <li><strong>Protein Intake:</strong> Ensure adequate protein intake to support muscle growth. Include animal-based proteins (like lean meats, eggs, and dairy) or plant-based proteins (like legumes, tofu, and quinoa) in your diet.</li>
    <li><strong>Balanced Nutrition:</strong> Focus on a nutrient-dense diet that includes vitamins and minerals to support muscle health and overall well-being.</li>
    <li><strong>Manage Hydration:</strong> While adequate hydration is important, avoid excessive fluid intake that may dilute creatinine levels.</li>
</ul>""")
        elif values["Creatinine"] > 1.2:
            advice.append("""<h2>High Creatinine (Hypercreatininemia)</h2>
<p>High creatinine levels are more commonly seen and typically indicate impaired kidney function or other factors that affect kidney health. The kidneys are responsible for filtering creatinine, so high levels are often a sign that the kidneys are not working properly.</p>

<h4>Root Causes of High Creatinine:</h4>
<ul>
    <li><strong>Acute Kidney Injury (AKI):</strong> Sudden damage to the kidneys (due to trauma, infection, or dehydration) can result in a rapid rise in creatinine levels.</li>
    <li><strong>Chronic Kidney Disease:</strong> Long-term kidney diseases, such as diabetic nephropathy or hypertensive nephropathy, impair kidney function, leading to elevated creatinine levels.</li>
    <li><strong>Dehydration:</strong> Inadequate Fluid Intake: When the body is dehydrated, the kidneys retain water to compensate, which can result in concentrated creatinine in the blood, causing elevated levels.</li>
    <li><strong>Rhabdomyolysis:</strong> This is a serious condition where muscle tissue breaks down rapidly due to injury, extreme physical exertion, or certain medications (e.g., statins), releasing creatine and creatinine into the bloodstream.</li>
    <li><strong>Severe Burns or Trauma:</strong> Extensive muscle damage from burns or trauma can lead to high creatinine levels as muscles release more creatinine into the blood.</li>
    <li><strong>Medications:</strong> Certain Drugs and Some medications, such as nonsteroidal anti-inflammatory drugs (NSAIDs), ACE inhibitors, and diuretics, can affect kidney function, leading to increased creatinine levels.</li>
    <li><strong>Chemotherapy:</strong> Chemotherapy drugs, especially in high doses, can cause kidney damage and elevate creatinine levels.</li>
    <li><strong>High Protein Diet:</strong> Excessive Meat Consumption: A high-protein diet, especially one rich in red meat, can increase the production of creatinine, as creatine (which is found in muscle tissues) is broken down into creatinine.</li>
    <li><strong>Heart Failure:</strong> Reduced Kidney Perfusion: In heart failure, the kidneys may not receive enough blood flow due to low cardiac output, which can impair their ability to filter waste and elevate creatinine levels.</li>
    <li><strong>Hypothyroidism:</strong> Low thyroid hormone levels can reduce kidney function, leading to elevated creatinine levels.</li>
    <li><strong>Cushing’s Syndrome:</strong> Elevated cortisol levels can impair kidney function, causing high creatinine levels.</li>
    <li><strong>Glomerulonephritis:</strong> Inflammation of the glomeruli (the filtering units of the kidneys) can impair kidney function and increase creatinine levels. This condition may be due to an autoimmune response or infection.</li>
    <li><strong>Kidney Dysfunction:</strong> High creatinine is one of the most important markers for kidney dysfunction. Elevated levels indicate that the kidneys are not filtering waste effectively, which can lead to a buildup of toxins in the body.</li>
    <li><strong>Fluid Imbalance:</strong> Poor kidney function can result in fluid retention, causing swelling, high blood pressure, and electrolyte imbalances.</li>
    <li><strong>Progression of Kidney Disease:</strong> Elevated creatinine levels can indicate the progression of kidney disease. Early intervention is critical to slow disease progression and prevent further damage.</li>
    <li><strong>Cardiovascular Risk:</strong> Chronic kidney disease and elevated creatinine levels are closely associated with an increased risk of cardiovascular events, such as heart attacks and strokes.</li>
</ul>

<h4>Tips to Lower Creatinine Levels:</h4>
<ul>
    <li><strong>Treat Kidney Disease:</strong> Work with a healthcare provider to manage underlying kidney disease, whether it’s diabetic nephropathy, hypertension, or glomerulonephritis. Proper medication, diet adjustments, and lifestyle changes can help manage creatinine levels.</li>
    <li><strong>Hydration:</strong> Stay adequately hydrated, but avoid excessive fluid intake, as this can stress the kidneys. Balance hydration with kidney health.</li>
    <li><strong>Limit Protein Intake:</strong> Reducing the intake of animal proteins and focusing on plant-based proteins can help reduce the workload on the kidneys and prevent further increases in creatinine levels.</li>
    <li><strong>Manage Blood Pressure and Blood Sugar:</strong> Controlling hypertension and diabetes is crucial in preventing kidney damage and managing creatinine levels. Aim for a healthy weight, exercise, and take prescribed medications.</li>
    <li><strong>Avoid Harmful Medications:</strong> Avoid medications or substances that can cause kidney damage, including certain over-the-counter pain relievers (NSAIDs) and some prescription medications. Always consult a healthcare provider before taking new medications.</li>
    <li><strong>Dietary Modifications:</strong> A kidney-friendly diet includes limiting salt intake, reducing phosphorus and potassium-rich foods (if advised by a healthcare provider), and eating foods that support overall kidney health, like blueberries, leafy greens, and whole grains.</li>
</ul>""")

    # Blood Urea Nitrogen (BUN) (range: 7-20 mg/dL)
    

    # Uric Acid (range: 3.5-7.2 mg/dL)
        if values["Blood Urea Nitrogen"] < 8:
            advice.append("""
        <h2>Low BUN (Hypoazotemia)</h2>
        <p>A low BUN level indicates that the kidneys are not filtering urea nitrogen properly or that there is an issue affecting protein breakdown. Though less common than high BUN levels, low levels can still point to specific health issues.</p>
        
        <h3>Root Causes of Low BUN:</h3>
        <ul>
            <li><b>Malnutrition or Low Protein Intake:</b> If the body does not have enough dietary protein to break down, urea production decreases, leading to low BUN levels. This can occur in cases of severe malnutrition, eating disorders (e.g., anorexia), or very low-protein diets.</li>
            <li><b>Liver Disease:</b> Since urea is produced in the liver, any condition that impairs liver function, such as cirrhosis or acute liver failure, can result in decreased urea production, leading to low BUN levels.</li>
            <li><b>Overhydration:</b> Excessive fluid intake or overhydration can dilute the blood, resulting in low concentrations of waste products, including urea, in the bloodstream.</li>
            <li><b>Severe Anemia:</b> Certain types of severe anemia, particularly those associated with a low red blood cell count, can lead to low BUN levels. Anemia decreases the body’s metabolic demand for protein, which results in less urea being produced.</li>
            <li><b>Pregnancy:</b> Pregnancy increases the blood volume, which can dilute waste products like BUN in the bloodstream. This is particularly common in the second and third trimesters.</li>
            <li><b>Nephrotic Syndrome:</b> In rare cases, nephrotic syndrome (a kidney disorder characterized by excessive protein loss in the urine) can result in a decreased BUN level due to altered kidney function and reduced urea production.</li>
            <li><b>Excessive Anabolic Steroid Use:</b> Anabolic steroids, which are used for muscle growth and recovery, can lower BUN levels by enhancing muscle protein synthesis, leading to reduced breakdown of proteins and, consequently, less urea production.</li>
            <li><b>Diabetes (in the early stages):</b> Although more commonly associated with high BUN, in the early stages of diabetes, low BUN can sometimes be observed, especially if the patient has experienced significant weight loss or poor nutrition.</li>
        </ul>

        <h3>Health Risks of Low BUN:</h3>
        <ul>
            <li><b>Malnutrition:</b> A low BUN level might indicate an insufficient intake of protein, leading to nutritional deficiencies and muscle wasting.</li>
            <li><b>Liver Disease:</b> Low BUN may indicate that the liver is not functioning properly, which can affect overall metabolic and detoxification processes.</li>
            <li><b>Kidney Dysfunction:</b> In some cases, kidney problems may contribute to low BUN, but it is less common than elevated levels.</li>
            <li><b>Fluid Imbalance:</b> Overhydration can result in diluted blood, which may mask other important biomarkers and distort the overall picture of kidney function.</li>
        </ul>

        <h3>Tips to Increase BUN Levels:</h3>
        <ul>
            <li><b>Increase Protein Intake:</b> Incorporate more lean meats, fish, eggs, and dairy products into the diet. For vegetarians, lentils, beans, and tofu are excellent sources of protein.</li>
            <li><b>Address Nutritional Deficiencies:</b> Consider working with a nutritionist to ensure you are getting an adequate, balanced diet to support overall health and liver function.</li>
            <li><b>Monitor Hydration:</b> While staying hydrated is important, avoid excessive fluid intake, especially in cases of low BUN due to overhydration.</li>
            <li><b>Treat Liver Conditions:</b> If liver disease is diagnosed, managing it with proper medical care, such as medications or lifestyle changes, may help increase BUN levels indirectly by improving liver function.</li>
            <li><b>Exercise Regularly:</b> Engage in regular physical activity to increase muscle mass and metabolism, which can increase urea production.</li>
        </ul>
        """)
        elif values["Blood Urea Nitrogen"] > 20:
            advice.append("""
        <h2>High BUN (Azotemia)</h2>
        <p>A high BUN level is more common and typically indicates that the kidneys are not functioning properly or that there are issues related to hydration, diet, or muscle metabolism.</p>
        
        <h3>Root Causes of High BUN:</h3>
        <ul>
            <li><b>Chronic Kidney Disease (CKD):</b> Conditions like CKD, acute kidney injury, or glomerulonephritis impair the kidneys' ability to filter urea, causing a buildup in the blood.</li>
            <li><b>Dehydration:</b> Insufficient fluid intake can lead to concentrated waste products like urea in the bloodstream.</li>
            <li><b>Excessive Fluid Loss:</b> Conditions causing fluid loss, such as vomiting, diarrhea, or fever, can lead to dehydration and an increase in BUN levels.</li>
            <li><b>High Protein Diet:</b> Consuming excessive amounts of protein increases urea production and may elevate BUN levels.</li>
            <li><b>Heart Failure:</b> Reduced kidney perfusion from heart failure impairs the kidneys' ability to filter waste products like urea.</li>
            <li><b>Gastrointestinal Bleeding:</b> Internal bleeding leads to increased nitrogen levels and elevated BUN.</li>
            <li><b>Shock:</b> Low blood pressure or shock reduces blood flow to the kidneys, impairing their ability to filter waste products properly.</li>
            <li><b>Uncontrolled Diabetes:</b> High blood sugar levels can stress the kidneys, causing high BUN levels.</li>
            <li><b>Medication Use:</b> Drugs like NSAIDs, diuretics, or antibiotics can lead to kidney damage or dehydration, raising BUN levels.</li>
            <li><b>Increased Muscle Breakdown:</b> Conditions like rhabdomyolysis release large amounts of urea nitrogen, raising BUN levels.</li>
        </ul>

        <h3>Health Risks of High BUN:</h3>
        <ul>
            <li><b>Kidney Dysfunction:</b> Elevated BUN is often a sign of impaired kidney function. Chronic kidney disease needs prompt treatment to avoid progression to kidney failure.</li>
            <li><b>Dehydration:</b> Persistent dehydration may lead to kidney damage and other complications like kidney stones.</li>
            <li><b>Cardiovascular Risk:</b> High BUN levels may indicate heart disease, particularly in individuals with existing heart or kidney conditions.</li>
            <li><b>Gastrointestinal Problems:</b> High BUN caused by gastrointestinal bleeding is a medical emergency requiring immediate attention.</li>
        </ul>

        <h3>Tips to Lower BUN Levels:</h3>
        <ul>
            <li><b>Improve Hydration:</b> Stay hydrated by drinking an adequate amount of water. Adjust fluid intake based on any underlying conditions.</li>
            <li><b>Manage Kidney Health:</b> Control conditions like hypertension, diabetes, or heart disease to protect kidney function.</li>
            <li><b>Moderate Protein Intake:</b> Reduce high-protein food consumption, especially red meat, and focus on lean protein sources.</li>
            <li><b>Treat Underlying Conditions:</b> Address issues like gastrointestinal bleeding, shock, or muscle breakdown promptly with medical care.</li>
            <li><b>Monitor Kidney Function:</b> Regular check-ups can help detect issues early and guide treatment strategies.</li>
        </ul>
        """)
        if values["Uric Acid"] < 3.5:
            advice.append("""
        <div>
            <h2>Low Uric Acid (Hypouricemia)</h2>
            <p>A low uric acid level is less common than a high level but can still be indicative of specific health issues.</p>
            <h3>Root Causes of Low Uric Acid:</h3>
            <ul>
                <li><strong>Kidney Dysfunction:</strong> Certain kidney diseases, particularly those that impair the renal tubules' ability to filter waste, can result in low uric acid levels in the blood.</li>
                <li><strong>Dietary Factors:</strong> A diet that is extremely low in purines (found in red meat, organ meats, and seafood) can result in low uric acid levels.</li>
                <li><strong>Overuse of Certain Medications:</strong>
                    <ul>
                        <li>Diuretics (e.g., Thiazides): Can lead to low uric acid levels by increasing its excretion in the urine.</li>
                        <li>Losartan (blood pressure medication): Known to lower uric acid levels.</li>
                        <li>Vitamin C Overuse: High doses can increase the renal clearance of uric acid.</li>
                    </ul>
                </li>
                <li><strong>Low Estrogen:</strong> In women, low estrogen levels, especially during menopause, can result in decreased uric acid levels.</li>
                <li><strong>Fanconi Syndrome:</strong> A rare disorder that affects kidney function, leading to the loss of important substances, including uric acid.</li>
                <li><strong>Wilson's Disease:</strong> A genetic disorder causing copper buildup, which can lead to low uric acid levels.</li>
            </ul>
            <h3>Health Risks of Low Uric Acid:</h3>
            <ul>
                <li><strong>Kidney Dysfunction:</strong> May indicate renal tubular dysfunction.</li>
                <li><strong>Gout Prevention:</strong> Reflects abnormal kidney function, which could lead to complications if untreated.</li>
                <li><strong>Metabolic Problems:</strong> Indicates imbalances such as issues with purine metabolism.</li>
            </ul>
            <h3>Tips to Increase Uric Acid Levels:</h3>
            <ul>
                <li><strong>Increase Purine-Rich Foods:</strong> Include red meat, shellfish, organ meats, and alcohol in moderation.</li>
                <li><strong>Proper Kidney Function:</strong> Ensure adequate hydration but avoid excessive fluid intake.</li>
                <li><strong>Monitor Medication Use:</strong> Discuss with your doctor about adjustments for diuretics or Vitamin C supplements.</li>
                <li><strong>Consult a Healthcare Provider:</strong> Seek specialized care for conditions like Wilson's disease or Fanconi syndrome.</li>
            </ul>
        </div>
        """)
        elif values["Uric Acid"] > 7.2:
            advice.append("""
        <div>
            <h2>High Uric Acid (Hyperuricemia)</h2>
            <p>High uric acid levels are more common and can result from factors that increase production or decrease excretion. Left untreated, it can lead to gout or kidney stones.</p>
            <h3>Root Causes of High Uric Acid:</h3>
            <ul>
                <li><strong>Purine-Rich Foods:</strong> Excessive consumption of red meat, seafood, organ meats, alcohol, and sugary drinks.</li>
                <li><strong>Kidney Impairment:</strong> Impaired kidney function leads to a buildup of uric acid.</li>
                <li><strong>Obesity:</strong> Excess body fat increases uric acid production and decreases its excretion.</li>
                <li><strong>Dehydration:</strong> Reduces the kidneys' ability to excrete uric acid.</li>
                <li><strong>Genetic Factors:</strong> Family history or genetic variations affecting uric acid processing.</li>
                <li><strong>Medications:</strong>
                    <ul>
                        <li>Diuretics: Can raise uric acid levels by causing dehydration.</li>
                        <li>Aspirin and Immunosuppressants: Reduce uric acid excretion.</li>
                    </ul>
                </li>
                <li><strong>Medical Conditions:</strong>
                    <ul>
                        <li>Gout: Uric acid crystals in joints cause inflammation and pain.</li>
                        <li>Psoriasis: Increased cell turnover elevates uric acid production.</li>
                        <li>Hypothyroidism: Decreases kidney clearance of uric acid.</li>
                        <li>Leukemia or Lymphoma: High cell turnover increases purine breakdown.</li>
                        <li>Lead Poisoning: Impairs kidney function.</li>
                    </ul>
                </li>
            </ul>
            <h3>Health Risks of High Uric Acid:</h3>
            <ul>
                <li><strong>Gout:</strong> Painful attacks due to uric acid crystallization in joints.</li>
                <li><strong>Kidney Stones:</strong> Uric acid can form kidney stones.</li>
                <li><strong>Cardiovascular Disease:</strong> Associated with hypertension and heart disease.</li>
                <li><strong>Kidney Damage:</strong> Long-term elevated levels can lead to renal failure.</li>
            </ul>
            <h3>Tips to Lower Uric Acid Levels:</h3>
            <ul>
                <li><strong>Limit Purine-Rich Foods:</strong> Reduce intake of red meats, seafood, and alcohol.</li>
                <li><strong>Stay Hydrated:</strong> Drink at least 8 glasses of water daily.</li>
                <li><strong>Limit Alcohol:</strong> Especially beer, which increases uric acid production.</li>
                <li><strong>Maintain a Healthy Weight:</strong> Regular exercise and a balanced diet.</li>
                <li><strong>Medications:</strong> Consult a doctor for options like allopurinol or febuxostat.</li>
                <li><strong>Avoid Sugary Beverages:</strong> Reduce fructose consumption from sodas and processed foods.</li>
                <li><strong>Manage Health Conditions:</strong> Treat hypertension, diabetes, and kidney disease effectively.</li>
                <li><strong>Eat Low-Purine Foods:</strong> Include low-fat dairy, whole grains, vegetables, and cherries.</li>
            </ul>
        </div>
        """)

    
    # Bilirubin (range: 0.1-1.2 mg/dL)
                # Gamma Glutamyl Transferase (range: 9-48 U/L)
        if values["Gamma Glutamyl Transferase"] < 9:
            advice.append("""
        <div>
            <h2>Low Gamma Glutamyl Transferase (GGT)</h2>
            <p>While low GGT levels are less common and less frequently discussed, they can still occur under certain circumstances. Generally, low GGT levels are not typically a cause for concern, but they can indicate specific health scenarios.</p>
            <h3>Root Causes of Low GGT:</h3>
            <ul>
                <li><strong>Hypothyroidism:</strong> Low thyroid function can decrease GGT production due to slower metabolic processes.</li>
                <li><strong>Malnutrition or Protein Deficiency:</strong> Protein deficiency or inadequate nutrition affects GGT synthesis, as proper liver enzyme production depends on specific nutrients.</li>
                <li><strong>Diabetes and Insulin Resistance:</strong> Though the connection isn't entirely clear, insulin resistance and diabetes may reduce GGT production.</li>
                <li><strong>Certain Medications:</strong> Medications such as oral contraceptives or statins can indirectly lower GGT levels.</li>
                <li><strong>Hypervitaminosis:</strong> Excessive intake of vitamins, especially Vitamin C, can lower GGT due to antioxidant effects on liver enzymes.</li>
                <li><strong>Genetics:</strong> Naturally low GGT levels may be due to genetic factors, which aren't usually concerning unless accompanied by other health issues.</li>
            </ul>
            <h3>Health Implications of Low GGT:</h3>
            <ul>
                <li>Low GGT levels are generally not a major concern unless linked to underlying conditions like hypothyroidism, nutritional deficiencies, or liver dysfunction.</li>
                <li>They can also be an indicator of good liver health, suggesting that the liver is functioning efficiently.</li>
            </ul>
            <h3>Tips to Maintain or Increase GGT Levels:</h3>
            <ul>
                <li><strong>Maintain Thyroid Health:</strong> Monitor thyroid function and address hypothyroidism with appropriate treatments.</li>
                <li><strong>Proper Nutrition:</strong> Consume a balanced diet rich in proteins and essential nutrients. Include lean meats, fish, eggs, dairy, and legumes.</li>
                <li><strong>Manage Diabetes:</strong> Regular exercise and a healthy diet help manage blood sugar levels, supporting metabolic health and enzyme balance.</li>
                <li><strong>Avoid Excessive Vitamin Intake:</strong> Avoid over-consuming vitamins, especially Vitamin C, unless prescribed by a healthcare provider.</li>
                <li><strong>Regular Check-Ups:</strong> Periodic health checks can help detect and address any underlying issues affecting GGT levels.</li>
            </ul>
        </div>
        """)

        elif values["Gamma Glutamyl Transferase"] > 48:
            advice.append("""
        <div>
            <h2>High Gamma Glutamyl Transferase (GGT)</h2>
            <p>Elevated GGT levels are more common and associated with various conditions involving the liver, bile ducts, and alcohol consumption. High GGT often indicates liver dysfunction and correlates with the extent of damage.</p>
            <h3>Root Causes of High GGT:</h3>
            <ul>
                <li><strong>Liver Diseases:</strong> Hepatitis, cirrhosis, fatty liver, and liver fibrosis elevate GGT due to liver cell damage.</li>
                <li><strong>Bile Duct Obstruction:</strong> Blockages (e.g., gallstones, pancreatitis) prevent proper bile flow, raising GGT levels.</li>
                <li><strong>Alcohol Consumption:</strong> Chronic or heavy drinking significantly raises GGT levels due to liver damage.</li>
                <li><strong>Non-Alcoholic Fatty Liver Disease (NAFLD):</strong> Obesity or metabolic syndrome can lead to fat accumulation in the liver, increasing GGT.</li>
                <li><strong>Medications:</strong> Drugs like phenytoin, barbiturates, statins, and acetaminophen affect liver metabolism and raise GGT.</li>
                <li><strong>Chronic Pancreatitis:</strong> Pancreas inflammation often linked to alcohol or gallstones can elevate GGT.</li>
                <li><strong>Cardiovascular Disease:</strong> High GGT is associated with increased oxidative stress and cardiovascular risks.</li>
                <li><strong>Diabetes and Obesity:</strong> Metabolic dysfunction due to these conditions elevates GGT.</li>
            </ul>
            <h3>Health Implications of High GGT:</h3>
            <ul>
                <li><strong>Liver Dysfunction:</strong> Often seen in liver diseases like hepatitis, cirrhosis, and alcoholic liver disease.</li>
                <li><strong>Bile Duct Obstruction:</strong> High GGT suggests bile flow issues, potentially leading to damage.</li>
                <li><strong>Alcohol Abuse:</strong> Indicates liver stress or damage from chronic alcohol use.</li>
                <li><strong>Cardiovascular Risk:</strong> Linked to oxidative stress and inflammation, both factors in heart disease.</li>
            </ul>
            <h3>Tips to Lower High GGT Levels:</h3>
            <ul>
                <li><strong>Limit Alcohol:</strong> Reducing or avoiding alcohol is crucial for lowering GGT levels and supporting liver recovery.</li>
                <li><strong>Healthy Diet:</strong> A liver-friendly diet with antioxidants (fruits, vegetables, whole grains) and healthy fats (e.g., omega-3) supports liver health.</li>
                <li><strong>Exercise and Weight Loss:</strong> Regular activity and weight management reduce liver fat and improve function.</li>
                <li><strong>Treat Underlying Conditions:</strong> Manage conditions like diabetes, obesity, and hypertension effectively.</li>
                <li><strong>Medication Management:</strong> If medications are contributing to elevated GGT, discuss alternatives with a doctor.</li>
                <li><strong>Regular Monitoring:</strong> Keep track of GGT and liver enzymes, especially in high-risk individuals.</li>
                <li><strong>Hydration and Liver Support:</strong> Drink water and consider liver-supportive supplements like milk thistle (after consulting a healthcare provider).</li>
            </ul>
        </div>
        """)

    # e-GFR (Glomerular Filtration Rate) (range: > 60 mL/min/1.73m²)
        if values["e-GFR (Glomerular Filtration Rate)"] < 60:
            advice.append("""
        <div style="font-family: Arial, sans-serif; line-height: 1.6;">
            <h2 ">Low e-GFR (Kidney Dysfunction)</h2>
            <p>A low e-GFR generally suggests that the kidneys are not functioning optimally and may be at risk of progressing to chronic kidney disease (CKD). The lower the e-GFR, the worse the kidney function.</p>
            
            <h3>Root Causes of Low e-GFR:</h3>
            <ul>
                <li><b>Chronic Kidney Disease (CKD):</b> The most common cause of a low e-GFR is chronic kidney disease, often resulting from long-term conditions such as diabetes, high blood pressure (hypertension), or glomerulonephritis (inflammation of the kidney’s filtering units).</li>
                <li><b>Acute Kidney Injury (AKI):</b> Sudden damage to the kidneys caused by severe dehydration, medications, infections, or trauma can temporarily drop e-GFR.</li>
                <li><b>Diabetes:</b> Diabetic nephropathy is a common complication of diabetes, leading to gradual damage to the kidneys and reduced ability to filter waste effectively.</li>
                <li><b>High Blood Pressure (Hypertension):</b> A major risk factor for kidney disease, hypertension can cause damage to the kidneys over time, resulting in reduced e-GFR levels.</li>
                <li><b>Glomerulonephritis:</b> Inflammation of the kidneys’ filtering units, often caused by infections, autoimmune diseases, or medications.</li>
                <li><b>Obstructions in the Urinary Tract:</b> Issues like kidney stones, prostate enlargement, or bladder problems obstructing urine flow.</li>
                <li><b>Kidney Infections or Inflammation:</b> Conditions like pyelonephritis (kidney infection) can impair filtration and reduce e-GFR.</li>
                <li><b>Age-Related Decline:</b> Natural decline in kidney function with age, even in the absence of major diseases.</li>
                <li><b>Genetic Disorders:</b> Disorders like polycystic kidney disease (PKD) that lead to kidney damage over time.</li>
            </ul>

            <h3>Health Implications of Low e-GFR:</h3>
            <ul>
                <li><b>Progression of Kidney Disease:</b> Persistently low e-GFR may indicate progression toward end-stage renal disease (ESRD).</li>
                <li><b>Toxin Build-Up:</b> The kidneys may not filter waste effectively, leading to uremia (build-up of waste in the blood).</li>
                <li><b>Electrolyte Imbalances:</b> May lead to complications like heart arrhythmias.</li>
                <li><b>Fluid Retention:</b> Trouble excreting excess fluid can cause swelling in the legs, ankles, or other parts of the body.</li>
            </ul>

            <h3>Tips to Improve or Manage Low e-GFR:</h3>
            <ul>
                <li><b>Control Blood Sugar:</b> Keep blood sugar levels under control to reduce the risk of diabetic nephropathy.</li>
                <li><b>Control Blood Pressure:</b> Manage blood pressure through diet, exercise, and medications to protect kidney health.</li>
                <li><b>Maintain a Kidney-Friendly Diet:</b>
                    <ul>
                        <li>Focus on a low-protein diet to reduce kidney stress.</li>
                        <li>Reduce sodium intake to control blood pressure.</li>
                        <li>Increase potassium and fiber intake through fruits and vegetables.</li>
                    </ul>
                </li>
                <li><b>Stay Hydrated:</b> Drink plenty of water, but follow medical advice if fluid retention is an issue.</li>
                <li><b>Avoid Smoking and Alcohol:</b> Quit smoking and limit alcohol consumption to improve kidney function.</li>
                <li><b>Monitor Kidney Function:</b> Regular testing of kidney function helps detect issues early for timely intervention.</li>
                <li><b>Avoid Nephrotoxic Drugs:</b> Limit the use of NSAIDs and consult a doctor before taking new medications.</li>
            </ul>
        </div>
        """)
        elif values["e-GFR (Glomerular Filtration Rate)"] > 90:
            advice.append("""
        <div style="font-family: Arial, sans-serif; line-height: 1.6;">
            <h2 >High e-GFR (Hyperfiltration)</h2>
            <p>A high e-GFR is usually a sign of increased kidney filtration and can sometimes indicate excessive kidney function. Though less common, a high e-GFR may occur under certain conditions.</p>
            
            <h3>Root Causes of High e-GFR:</h3>
            <ul>
                <li><b>Hyperfiltration in Early Kidney Disease:</b> The kidneys compensate for nephron loss by increasing filtration rates, leading to an initially high e-GFR.</li>
                <li><b>Pregnancy:</b> Increased blood volume and kidney function during pregnancy can elevate e-GFR.</li>
                <li><b>High Protein Intake:</b> A high-protein diet can temporarily increase kidney workload, raising e-GFR.</li>
                <li><b>Exercise:</b> Strenuous physical activity temporarily increases e-GFR due to increased kidney blood flow.</li>
                <li><b>Early-Stage Diabetes:</b> The kidneys may hyperfilter in response to excess glucose in the blood.</li>
                <li><b>Severe Hypertension (Stage 1):</b> Increased fluid filtration due to high blood pressure can elevate e-GFR.</li>
            </ul>

            <h3>Health Implications of High e-GFR:</h3>
            <ul>
                <li><b>Risk of Kidney Damage:</b> Prolonged hyperfiltration may damage nephrons over time.</li>
                <li><b>Underlying Conditions:</b> A high e-GFR might indicate conditions like diabetes or high protein intake requiring attention.</li>
                <li><b>Short-Term Effects:</b> In cases like pregnancy, high e-GFR is usually temporary and not a cause for concern.</li>
            </ul>

            <h3>Tips to Manage or Lower High e-GFR:</h3>
            <ul>
                <li><b>Monitor Kidney Function Regularly:</b> Early detection of hyperfiltration allows for timely intervention.</li>
                <li><b>Control Blood Sugar:</b> Maintain optimal blood sugar levels to prevent kidney hyperfiltration.</li>
                <li><b>Adopt a Balanced Diet:</b> Reduce protein intake if high protein consumption is stressing the kidneys.</li>
                <li><b>Manage Weight:</b> Maintaining a healthy weight reduces risks associated with hypertension and diabetes.</li>
                <li><b>Stay Hydrated:</b> Proper hydration supports kidney health and reduces dehydration risks.</li>
            </ul>
        </div>
        """)

    # Urea (range: 7-20 mg/dL)
        if values["Urea"] < 7:
            advice.append("""
        <div style="font-family: Arial, sans-serif; line-height: 1.6;">
            <h2>Low Urea (Hypouremia)</h2>
            <p>Low urea levels in the blood can occur due to several factors that influence its production or clearance.</p>

            <h3>Root Causes of Low Urea:</h3>
            <ul>
                <li><b>Liver Disease:</b> Liver dysfunction or diseases such as cirrhosis, hepatitis, or liver failure can result in low urea production. The liver is responsible for converting ammonia into urea, so if the liver is not functioning properly, this process is impaired, leading to lower urea levels.</li>
                <li><b>Malnutrition:</b> A protein-deficient diet can result in low urea levels because insufficient protein intake leads to reduced urea production.</li>
                <li><b>Overhydration:</b> Excessive fluid intake can dilute the urea concentration in the blood, often seen in cases of polydipsia or excessive intravenous fluid administration.</li>
                <li><b>Severe Bone Marrow Depression:</b> Conditions such as aplastic anemia or certain chemotherapies may lead to low urea levels due to reduced protein breakdown.</li>
                <li><b>Pregnancy:</b> Increased blood volume and more efficient kidney filtration during pregnancy can lead to lower urea levels.</li>
                <li><b>Acute or Chronic Renal Failure (rare):</b> Advanced kidney disease can lead to decreased urea production due to reduced protein metabolism or other kidney dysfunctions.</li>
                <li><b>High Carbohydrate Diet:</b> A high carbohydrate, low protein diet reduces urea production as carbohydrates are not metabolized into urea.</li>
            </ul>

            <h3>Health Implications of Low Urea:</h3>
            <ul>
                <li><b>Indication of Liver Dysfunction:</b> Low urea levels may point to significant liver damage or dysfunction.</li>
                <li><b>Malnutrition:</b> Extremely low urea levels can signal poor nutrition or malnutrition.</li>
                <li><b>Electrolyte Imbalance:</b> Overhydration-related dilution of urea may disturb electrolyte balance, negatively affecting the heart, muscles, and other organs.</li>
            </ul>

            <h3>Tips to Improve or Manage Low Urea:</h3>
            <ul>
                <li><b>Support Liver Health:</b>
                    <ul>
                        <li>Avoid alcohol and other substances that can damage the liver.</li>
                        <li>Follow a liver-healthy diet rich in antioxidants, fruits, vegetables, and healthy fats.</li>
                        <li>Consult your doctor for regular liver function tests.</li>
                    </ul>
                </li>
                <li><b>Improve Nutrition:</b>
                    <ul>
                        <li>Increase protein intake by including lean meats, fish, eggs, legumes, and dairy in your diet.</li>
                        <li>Maintain a balanced, nutrient-rich diet to support overall health and urea production.</li>
                    </ul>
                </li>
                <li><b>Monitor Fluid Intake:</b> Avoid excessive water consumption and drink fluids based on your body’s needs.</li>
                <li><b>Consult a Doctor for Kidney Function:</b> Regular monitoring with blood tests and urinalysis is essential if kidney dysfunction is suspected.</li>
            </ul>
        </div>
        """)
        elif values["Urea"] > 20:
            advice.append("""
        <div style="font-family: Arial, sans-serif; line-height: 1.6;">
            <h2 >High Urea (Hyperuremia)</h2>
            <p>High urea levels in the blood typically indicate that the kidneys are not efficiently clearing urea or may signify excess protein breakdown.</p>

            <h3>Root Causes of High Urea:</h3>
            <ul>
                <li><b>Kidney Dysfunction (CKD):</b> Chronic kidney disease reduces the kidneys' ability to filter out waste products like urea.</li>
                <li><b>Dehydration:</b> Reduced fluid intake or excessive fluid loss concentrates blood, increasing urea levels.</li>
                <li><b>Excessive Protein Intake:</b> High-protein diets can elevate urea levels due to increased protein breakdown.</li>
                <li><b>Acute Kidney Injury (AKI):</b> Sudden kidney damage from dehydration, infections, or medications can cause elevated urea.</li>
                <li><b>Heart Failure:</b> Poor kidney perfusion due to heart failure may lead to higher urea levels.</li>
                <li><b>Gastrointestinal Bleeding:</b> Increased protein breakdown from digestive tract bleeding raises urea levels.</li>
                <li><b>Burns or Severe Trauma:</b> Tissue breakdown increases protein catabolism, raising urea production.</li>
                <li><b>High Blood Pressure:</b> Uncontrolled hypertension damages kidneys over time, leading to high urea levels.</li>
                <li><b>Medications:</b> Diuretics, certain antibiotics, and other drugs can promote dehydration or impair kidney function, increasing urea.</li>
                <li><b>Infections:</b> Severe infections, particularly of the kidneys, can impair kidney function and increase urea levels.</li>
            </ul>

            <h3>Health Implications of High Urea:</h3>
            <ul>
                <li><b>Kidney Disease:</b> Persistent high urea levels may indicate chronic kidney disease or acute kidney injury.</li>
                <li><b>Dehydration:</b> Elevated urea levels may point to dehydration, which can lead to electrolyte imbalances and kidney damage.</li>
                <li><b>Heart and Blood Pressure Issues:</b> Conditions like heart failure or high blood pressure can impair kidney function and elevate urea levels.</li>
            </ul>

            <h3>Tips to Manage or Lower High Urea:</h3>
            <ul>
                <li><b>Hydration:</b> Drink enough water daily to maintain proper kidney function and flush out toxins.</li>
                <li><b>Manage Kidney Health:</b> Follow your doctor’s advice for medications, dialysis, and lifestyle changes.</li>
                <li><b>Dietary Modifications:</b>
                    <ul>
                        <li>Reduce protein intake to lower the burden on kidneys.</li>
                        <li>Limit salt and processed foods to control blood pressure.</li>
                    </ul>
                </li>
                <li><b>Control Blood Pressure:</b> Regularly monitor blood pressure and manage it with medications or lifestyle changes.</li>
                <li><b>Avoid Nephrotoxic Substances:</b> Avoid drugs that can worsen kidney function and consult your doctor before taking new medications.</li>
                <li><b>Address Underlying Conditions:</b> Manage conditions like heart failure or diabetes to improve kidney function and reduce urea levels.</li>
            </ul>
        </div>
        """)

    # T3 Total (range: 80-180 ng/dL)
        if values["T3 Total"] < 0.6:
            advice.append("""
        <h2>Low T3 Total (Hypothyroidism)</h2>
        <p>Low levels of T3 can occur when the thyroid gland is underactive and fails to produce enough thyroid hormones. This condition is called hypothyroidism.</p>
        
        <h3>Root Causes of Low T3 Total:</h3>
        <ul>
            <li><strong>Hypothyroidism:</strong> The most common cause of low T3 levels is hypothyroidism, where the thyroid gland doesn't produce enough hormones, including T3. This can be due to autoimmune diseases like Hashimoto's thyroiditis, iodine deficiency, or surgery that removes part or all of the thyroid.</li>
            <li><strong>Severe Illness or Stress:</strong> Severe illnesses or high levels of physical stress can lead to low T3 levels. This is sometimes referred to as "non-thyroidal illness syndrome" or "sick euthyroid syndrome." In this case, T3 levels drop even though there is no thyroid dysfunction, often as a response to the body’s stress response.</li>
            <li><strong>Pituitary Dysfunction:</strong> The pituitary gland produces thyroid-stimulating hormone (TSH), which regulates the thyroid’s hormone production. If the pituitary is not functioning properly, it can result in insufficient T3 production. This could be due to pituitary tumors or other pituitary disorders.</li>
            <li><strong>Iodine Deficiency:</strong> Iodine deficiency is a common cause of hypothyroidism in certain parts of the world. The thyroid requires iodine to produce T3 and T4 hormones. A lack of iodine in the diet can lead to reduced T3 levels.</li>
            <li><strong>Medications:</strong> Certain medications, such as amiodarone, lithium, and beta-blockers, can interfere with thyroid function and result in low T3 levels.</li>
            <li><strong>Nutritional Deficiencies:</strong> Deficiencies in zinc, selenium, or iron can affect thyroid function and lead to low T3 levels, as these nutrients are necessary for optimal thyroid hormone production.</li>
            <li><strong>Starvation or Extreme Weight Loss:</strong> In cases of starvation, extreme calorie restriction, or anorexia nervosa, the body may conserve energy by lowering the production of T3 to reduce metabolic rate.</li>
        </ul>
        
        <h3>Health Implications of Low T3 Total:</h3>
        <ul>
            <li><strong>Slowed Metabolism:</strong> Low T3 levels can lead to a slower metabolic rate, causing symptoms like fatigue, weight gain, cold intolerance, constipation, and dry skin.</li>
            <li><strong>Thyroid Disease:</strong> Prolonged low T3 levels are typically associated with hypothyroidism, which requires medical treatment to regulate hormone levels.</li>
            <li><strong>Cardiovascular Risk:</strong> Severe hypothyroidism can lead to high cholesterol levels, heart disease, and other cardiovascular complications.</li>
        </ul>
        
        <h3>Tips to Improve or Manage Low T3 Total:</h3>
        <ul>
            <li><strong>Thyroid Hormone Replacement:</strong> If you have hypothyroidism, your doctor may prescribe levothyroxine (synthetic T4) or liothyronine (synthetic T3) to normalize hormone levels. Follow your doctor’s advice and have your thyroid levels monitored regularly.</li>
            <li><strong>Manage Stress:</strong> Chronic stress can contribute to low T3 levels. Implementing stress management techniques such as meditation, deep breathing exercises, yoga, or mindfulness can help improve your thyroid function.</li>
            <li><strong>Improve Nutrition:</strong> Ensure adequate iodine intake by consuming iodized salt, seafood, and dairy products. Also, consider eating foods rich in selenium (such as Brazil nuts, sunflower seeds, and fish) and zinc (found in meat, shellfish, legumes, and seeds).</li>
            <li><strong>Avoid Goitrogenic Foods:</strong> If you have thyroid problems, avoid excess intake of goitrogenic foods such as soy products, cruciferous vegetables (e.g., cabbage, cauliflower), and millet, which can interfere with thyroid hormone production.</li>
            <li><strong>Regular Exercise:</strong> Engage in regular moderate exercise to help support metabolism and improve thyroid function. This can also help mitigate weight gain associated with hypothyroidism.</li>
            <li><strong>Monitor Medications:</strong> If you are taking medications that affect thyroid function, such as beta-blockers or amiodarone, discuss alternatives or adjustments with your healthcare provider.</li>
        </ul>
        """)

        elif values["T3 Total"] > 1.81:
            advice.append("""
        <h2>High T3 Total (Hyperthyroidism)</h2>
        <p>High levels of T3 typically indicate an overactive thyroid, a condition known as hyperthyroidism.</p>
        
        <h3>Root Causes of High T3 Total:</h3>
        <ul>
            <li><strong>Graves' Disease:</strong> The most common cause of high T3 levels is Graves' disease, an autoimmune disorder where the body produces antibodies that stimulate the thyroid gland to produce excess T3 and T4 hormones.</li>
            <li><strong>Toxic Multinodular Goiter:</strong> In this condition, multiple nodules in the thyroid gland become overactive and secrete excess thyroid hormones, leading to elevated T3 levels.</li>
            <li><strong>Thyroiditis:</strong> Thyroiditis, including subacute thyroiditis and Hashimoto’s thyroiditis, can cause temporary increases in thyroid hormone production, including T3. This often occurs in the early stages of the condition before the thyroid becomes underactive (hypothyroidism).</li>
            <li><strong>Excessive Iodine Intake:</strong> Excessive iodine intake from supplements or foods (like iodine-rich seaweed) can cause an increase in thyroid hormone production, resulting in higher T3 levels.</li>
            <li><strong>Thyroid Cancer:</strong> Thyroid cancer can cause abnormal production of thyroid hormones, including high T3 levels.</li>
            <li><strong>Medications:</strong> Some medications, such as thyroid hormone replacement therapy (if overused) or amiodarone, can lead to excessive thyroid hormone levels, including high T3.</li>
            <li><strong>Pituitary Tumor:</strong> Rarely, pituitary tumors (e.g., thyrotropinoma) can cause overproduction of thyroid-stimulating hormone (TSH), leading to increased thyroid hormone production, including T3.</li>
        </ul>
        
        <h3>Health Implications of High T3 Total:</h3>
        <ul>
            <li><strong>Increased Metabolism:</strong> High T3 levels accelerate metabolism, leading to symptoms such as weight loss, nervousness, tremors, heat intolerance, increased heart rate, and high blood pressure.</li>
            <li><strong>Thyroid Storm:</strong> In severe cases, uncontrolled hyperthyroidism can lead to thyroid storm, a life-threatening condition that causes fever, confusion, and cardiovascular collapse.</li>
            <li><strong>Osteoporosis:</strong> Chronic high T3 levels can increase the risk of bone loss and osteoporosis.</li>
            <li><strong>Cardiovascular Issues:</strong> Hyperthyroidism increases the risk of heart conditions like atrial fibrillation and heart failure.</li>
        </ul>
        
        <h3>Tips to Manage or Lower High T3 Total:</h3>
        <ul>
            <li><strong>Antithyroid Medications:</strong> Methimazole or propylthiouracil can be prescribed to block thyroid hormone production in conditions like Graves' disease or toxic goiters. Follow your doctor’s guidance closely.</li>
            <li><strong>Radioactive Iodine Therapy:</strong> In cases of toxic multinodular goiter or Graves’ disease, radioactive iodine therapy may be used to shrink the thyroid or destroy overactive thyroid tissue.</li>
            <li><strong>Beta-Blockers:</strong> Beta-blockers (such as propranolol) may be used to control symptoms like increased heart rate and tremors associated with high T3 levels.</li>
            <li><strong>Thyroidectomy:</strong> In cases where medication and radioactive iodine therapy are ineffective, a partial or total thyroidectomy (removal of part or all of the thyroid) may be necessary.</li>
            <li><strong>Monitor Iodine Intake:</strong> If you have hyperthyroidism, avoid excessive intake of iodine, which can exacerbate the condition. Be cautious with iodine-rich supplements and foods like seaweed.</li>
            <li><strong>Stress Management:</strong> Stress can exacerbate hyperthyroidism, so managing stress through relaxation techniques and lifestyle changes is beneficial.</li>
        </ul>
        """)

    # T4 Total (range: 5.0-12.0 µg/dL)
        if values["T4 Total"] < 3.2:
            advice.append("""
        <h2>Low T4 Total (Hypothyroidism)</h2>
        <p>Low levels of T4 can indicate an underactive thyroid (hypothyroidism), where the thyroid fails to produce adequate amounts of thyroid hormones.</p>
        
        <h3>Root Causes of Low T4 Total:</h3>
        <ul>
            <li><strong>Hypothyroidism (Primary):</strong> Primary hypothyroidism is the most common cause of low T4 levels. It occurs when the thyroid gland itself is not functioning properly. This can be due to autoimmune diseases like Hashimoto's thyroiditis, iodine deficiency, or thyroid surgery.</li>
            <li><strong>Pituitary Dysfunction:</strong> Pituitary gland dysfunction can result in low T4 levels. The pituitary gland produces thyroid-stimulating hormone (TSH), which signals the thyroid to release T4. If the pituitary is not working properly (due to tumors, injury, or other disorders), it can lead to insufficient stimulation of the thyroid, causing low T4 levels.</li>
            <li><strong>Iodine Deficiency:</strong> Iodine deficiency is a common cause of hypothyroidism, especially in regions where the diet lacks adequate iodine. Since iodine is a key component of T4 and T3 hormones, its deficiency can lead to low T4 levels.</li>
            <li><strong>Medications:</strong> Certain medications, such as lithium, amiodarone, and antithyroid drugs like methimazole, can interfere with thyroid hormone production and cause low T4 levels.</li>
            <li><strong>Thyroiditis:</strong> Inflammation of the thyroid (such as Hashimoto’s thyroiditis or subacute thyroiditis) can result in an initial increase in thyroid hormones followed by a drop in T4 levels.</li>
            <li><strong>Starvation or Extreme Calorie Restriction:</strong> During periods of starvation or severe caloric restriction, the body reduces the production of T4 as part of a mechanism to conserve energy.</li>
            <li><strong>Pregnancy (Hypothyroidism in Pregnancy):</strong> In pregnant women, especially during the first trimester, there may be an increased need for thyroid hormone, and insufficient thyroid production can lead to low T4 levels.</li>
        </ul>

        <h3>Health Implications of Low T4 Total:</h3>
        <ul>
            <li><strong>Slowed Metabolism:</strong> Symptoms include weight gain, fatigue, cold intolerance, constipation, and dry skin.</li>
            <li><strong>Mental Health:</strong> Low T4 can lead to depression, memory issues, and brain fog.</li>
            <li><strong>Cardiovascular Impact:</strong> Low T4 may contribute to high cholesterol levels and an increased risk of cardiovascular disease.</li>
            <li><strong>Growth and Development:</strong> In children, untreated hypothyroidism can result in delayed growth and cognitive development.</li>
        </ul>

        <h3>Tips to Improve or Manage Low T4 Total:</h3>
        <ul>
            <li><strong>Thyroid Hormone Replacement:</strong> Levothyroxine (synthetic T4) is the standard treatment for low T4 levels. It helps normalize hormone levels and alleviate symptoms of hypothyroidism. Regular blood tests to monitor T4 and TSH levels are essential to adjust the dosage.</li>
            <li><strong>Nutrition:</strong>
                <ul>
                    <li><strong>Iodine:</strong> Ensure adequate iodine intake by consuming iodized salt, seafood, and dairy products.</li>
                    <li><strong>Selenium:</strong> Foods such as Brazil nuts, fish, and seeds are good sources of selenium, which supports thyroid function.</li>
                    <li><strong>Zinc:</strong> Meat, shellfish, and legumes are rich in zinc, another essential mineral for thyroid health.</li>
                </ul>
            </li>
            <li><strong>Manage Stress:</strong> High levels of stress can negatively impact thyroid function. Incorporate stress management techniques such as yoga, meditation, and regular exercise.</li>
            <li><strong>Avoid Goitrogens:</strong> Limit the intake of goitrogenic foods (e.g., soy, cruciferous vegetables) that may interfere with thyroid hormone production.</li>
            <li><strong>Regular Monitoring:</strong> If you are on thyroid medication, ensure regular check-ups with your healthcare provider to monitor T4 and TSH levels and adjust treatment as needed.</li>
        </ul>
        """)

        elif values["T4 Total"] > 12.6:
            advice.append("""
        <h2>High T4 Total (Hyperthyroidism)</h2>
        <p>High levels of T4 indicate an overactive thyroid (hyperthyroidism), where the thyroid produces excessive thyroid hormones, speeding up the body’s metabolic processes.</p>
        
        <h3>Root Causes of High T4 Total:</h3>
        <ul>
            <li><strong>Graves' Disease:</strong> Graves' disease is the most common cause of hyperthyroidism. It’s an autoimmune disorder where the immune system produces antibodies that stimulate the thyroid gland to produce excessive amounts of T4.</li>
            <li><strong>Toxic Multinodular Goiter:</strong> In a toxic multinodular goiter, multiple nodules in the thyroid become overactive and secrete excess thyroid hormones, leading to high T4 levels.</li>
            <li><strong>Thyroiditis:</strong> Thyroiditis, especially subacute thyroiditis or Hashimoto’s thyroiditis, can cause a temporary increase in thyroid hormone production, including T4. This can occur in the early stages of thyroid inflammation before the thyroid becomes underactive.</li>
            <li><strong>Excessive Iodine Intake:</strong> Excessive iodine intake, particularly from supplements or iodine-rich foods (such as seaweed), can lead to increased thyroid hormone production, causing high T4 levels.</li>
            <li><strong>Thyroid Hormone Overuse:</strong> If you are on thyroid hormone replacement therapy (e.g., levothyroxine) and take too much, it can lead to high T4 levels.</li>
            <li><strong>Pituitary Tumor (Thyrotropinoma):</strong> Rarely, pituitary tumors (thyrotropinoma) can produce excess thyroid-stimulating hormone (TSH), which in turn stimulates the thyroid to produce excess T4.</li>
            <li><strong>Thyroid Cancer:</strong> Thyroid cancer can sometimes cause overproduction of thyroid hormones, leading to high T4 levels.</li>
        </ul>

        <h3>Health Implications of High T4 Total:</h3>
        <ul>
            <li><strong>Increased Metabolism:</strong> Symptoms include weight loss, nervousness, tremors, heat intolerance, increased heart rate, and high blood pressure.</li>
            <li><strong>Cardiovascular Issues:</strong> Hyperthyroidism can lead to arrhythmias (e.g., atrial fibrillation), high blood pressure, and increased risk of heart disease.</li>
            <li><strong>Bone Health:</strong> Long-term hyperthyroidism can lead to osteoporosis and bone fractures due to increased metabolic activity.</li>
            <li><strong>Thyroid Storm:</strong> In severe cases, thyroid storm (a life-threatening condition) can occur, causing fever, delirium, tachycardia, and heart failure.</li>
        </ul>

        <h3>Tips to Manage or Lower High T4 Total:</h3>
        <ul>
            <li><strong>Antithyroid Medications:</strong> Methimazole or propylthiouracil can be prescribed to block thyroid hormone production. These medications help to control hyperthyroidism.</li>
            <li><strong>Radioactive Iodine Therapy:</strong> Radioactive iodine therapy may be used to shrink the thyroid or destroy overactive thyroid tissue, which reduces hormone production.</li>
            <li><strong>Beta-Blockers:</strong> Beta-blockers, such as propranolol, can be prescribed to control symptoms like tachycardia and tremors that occur with high T4 levels.</li>
            <li><strong>Surgical Treatment (Thyroidectomy):</strong> In cases of toxic multinodular goiter or Graves' disease that do not respond to medication or radioactive iodine, surgical removal of part or all of the thyroid may be necessary.</li>
            <li><strong>Monitor Iodine Intake:</strong> Limit excessive intake of iodine through supplements or foods like seaweed if you have hyperthyroidism, as this can worsen the condition.</li>
            <li><strong>Stress Management:</strong> Reducing stress can help manage hyperthyroid symptoms. Engage in relaxation techniques, yoga, and mindfulness practices.</li>
        </ul>
        """)

    # TSH Ultrasensitive (range: 0.4-4.0 µIU/mL)
        if values["TSH Ultrasensitive"] < 0.55:
            advice.append("""
<div style="font-family: Arial, sans-serif; line-height: 1.6;">
    <h2>Low TSH (Hypothyroidism or Secondary Hypothyroidism)</h2>
    <p>
        A low TSH level typically indicates hyperthyroidism or thyroid overactivity, where the thyroid produces excessive amounts of thyroid hormones (T3 and T4). In rare cases, low TSH can also indicate secondary hypothyroidism, which occurs due to issues with the pituitary gland or hypothalamus.
    </p>
    <h3>Root Causes of Low TSH:</h3>
    <ul>
        <li><strong>Hyperthyroidism:</strong> Graves' disease, toxic multinodular goiter, and thyroiditis are common causes of hyperthyroidism. In this condition, excessive thyroid hormone production leads to a suppression of TSH secretion.</li>
        <li><strong>Graves' Disease:</strong> An autoimmune condition where the immune system mistakenly stimulates the thyroid to produce too much thyroid hormone.</li>
        <li><strong>Toxic Multinodular Goiter:</strong> A condition where multiple overactive thyroid nodules secrete excess thyroid hormones.</li>
        <li><strong>Thyroiditis:</strong> Inflammation of the thyroid gland causing an initial surge in thyroid hormones.</li>
        <li><strong>Secondary Hypothyroidism:</strong> Issues with the pituitary gland or hypothalamus failing to produce enough TSH or TRH.</li>
        <li><strong>Thyroid Hormone Overuse:</strong> Excessive thyroid hormone replacement treatment can suppress TSH.</li>
        <li><strong>Severe Illness or Stress:</strong> Stress reactions like non-thyroidal illness syndrome may suppress TSH levels.</li>
        <li><strong>Excessive Iodine Intake:</strong> High iodine intake from supplements or foods can lead to suppressed TSH levels.</li>
    </ul>
    <h3>Health Implications of Low TSH:</h3>
    <ul>
        <li><strong>Increased Metabolism:</strong> Symptoms include weight loss, increased heart rate, nervousness, tremors, heat intolerance, and insomnia.</li>
        <li><strong>Cardiovascular Risks:</strong> Increased risk of arrhythmias, high blood pressure, and heart failure.</li>
        <li><strong>Osteoporosis:</strong> Long-term hyperthyroidism can cause bone loss.</li>
    </ul>
    <h3>Tips to Manage Low TSH:</h3>
    <ul>
        <li><strong>Treat Underlying Hyperthyroidism:</strong> Medications like methimazole or radioactive iodine therapy.</li>
        <li><strong>Surgery:</strong> Thyroidectomy for large goiters or unresponsive cases.</li>
        <li><strong>Beta-Blockers:</strong> Propranolol to manage symptoms like tremors and tachycardia.</li>
        <li><strong>Monitoring:</strong> Regular testing for TSH and free T4 levels.</li>
        <li><strong>Stress Management:</strong> Techniques such as yoga, meditation, and breathing exercises.</li>
    </ul>
</div>
        """)
        elif values["TSH Ultrasensitive"] > 4.78:
            advice.append("""
<div style="font-family: Arial, sans-serif; line-height: 1.6;">
    <h2>High TSH (Hypothyroidism or Pituitary Overactivity)</h2>
    <p>
        High TSH typically indicates an underactive thyroid (hypothyroidism), where the thyroid fails to produce enough thyroid hormones, and the pituitary gland compensates by producing more TSH in an attempt to stimulate thyroid hormone production. Rarely, it may result from pituitary dysfunction.
    </p>
    <h3>Root Causes of High TSH:</h3>
    <ul>
        <li><strong>Primary Hypothyroidism:</strong> Thyroid gland dysfunction leading to insufficient thyroid hormone production.</li>
        <li><strong>Hashimoto's Thyroiditis:</strong> Autoimmune attack on the thyroid.</li>
        <li><strong>Iodine Deficiency:</strong> Lack of iodine in the diet causing reduced thyroid hormone production.</li>
        <li><strong>Thyroidectomy:</strong> Removal of part or all of the thyroid gland.</li>
        <li><strong>Secondary Hypothyroidism:</strong> Pituitary tumors or dysfunction leading to excessive TSH production.</li>
        <li><strong>Medications:</strong> Abrupt withdrawal of thyroid hormone therapy.</li>
        <li><strong>Congenital Hypothyroidism:</strong> Non-functioning thyroid at birth.</li>
    </ul>
    <h3>Health Implications of High TSH:</h3>
    <ul>
        <li><strong>Slowed Metabolism:</strong> Symptoms include weight gain, fatigue, cold intolerance, and dry skin.</li>
        <li><strong>Mental Health:</strong> Difficulty concentrating and memory issues.</li>
        <li><strong>Cardiovascular Risks:</strong> High cholesterol and increased heart disease risk.</li>
    </ul>
    <h3>Tips to Manage High TSH:</h3>
    <ul>
        <li><strong>Thyroid Hormone Replacement:</strong> Levothyroxine to normalize thyroid hormone levels.</li>
        <li><strong>Regular Monitoring:</strong> Regular TSH and free T4 tests to adjust dosage.</li>
        <li><strong>Iodine Supplementation:</strong> If iodine deficiency is the cause, dietary adjustments are necessary.</li>
        <li><strong>Pituitary Tumor Management:</strong> Surgery, radiation, or medications for pituitary tumors.</li>
        <li><strong>Medication Review:</strong> Ensure correct dosage of thyroid hormone therapy.</li>
    </ul>
</div>
        """)

    # Vitamin B12 (range: 200-900 pg/mL)
        if values["Vitamin B12"] < 211:
            advice.append("""
<div style="font-family: Arial, sans-serif; line-height: 1.6;">
    <h2>Low Vitamin B12 (Cobalamin Deficiency)</h2>
    <p>
        A low vitamin B12 level can lead to a range of health issues because B12 is essential for nerve health, blood cell formation, and the metabolism of homocysteine (an amino acid linked to heart disease). B12 deficiency can also cause neurological and cognitive symptoms.
    </p>
    <h3>Root Causes of Low Vitamin B12:</h3>
    <ul>
        <li><strong>Poor Dietary Intake:</strong> A vegetarian or vegan diet, which excludes animal-based foods, is a common cause of vitamin B12 deficiency because B12 is found primarily in animal products like meat, fish, eggs, and dairy.</li>
        <li><strong>Malabsorption Disorders:</strong> Conditions like celiac disease, Crohn’s disease, or gastric bypass surgery can impair B12 absorption. Atrophic gastritis or pernicious anemia can also cause malabsorption.</li>
        <li><strong>Aging:</strong> Reduced stomach acid production with age can lead to impaired B12 absorption.</li>
        <li><strong>Medications:</strong> Proton pump inhibitors (PPIs), H2 blockers, and metformin can interfere with B12 absorption.</li>
        <li><strong>Alcoholism:</strong> Chronic alcohol consumption can impair B12 absorption.</li>
        <li><strong>Pregnancy and Breastfeeding:</strong> Increased requirements during pregnancy and breastfeeding can lead to deficiency if intake is insufficient.</li>
    </ul>
    <h3>Symptoms of Low Vitamin B12:</h3>
    <ul>
        <li>Fatigue, weakness, and anemia</li>
        <li>Numbness, tingling, or burning sensations in hands and feet</li>
        <li>Cognitive issues such as memory loss or difficulty concentrating</li>
        <li>Depression or mood changes</li>
        <li>Glossitis (inflamed tongue) and mouth ulcers</li>
        <li>Vision problems due to nerve damage</li>
        <li>Pale or jaundiced skin</li>
    </ul>
    <h3>Tips to Increase Vitamin B12:</h3>
    <ul>
        <li><strong>Dietary Sources:</strong> Include more animal-based foods like meat (especially liver), fish (salmon, tuna), dairy, and eggs. For vegetarians and vegans, opt for fortified cereals, plant-based milks, and nutritional yeast.</li>
        <li><strong>Vitamin B12 Supplements:</strong> Take oral B12 supplements or consider sublingual forms. In severe cases, injections or nasal sprays may be necessary.</li>
        <li><strong>Address Malabsorption Issues:</strong> Work with your healthcare provider if you have conditions like celiac disease or pernicious anemia.</li>
        <li><strong>Check Medications:</strong> If you're on medications like metformin or PPIs, consult your doctor about potential B12 deficiency.</li>
    </ul>
</div>
        """)
        elif values["Vitamin B12"] > 911:
            advice.append("""
<div style="font-family: Arial, sans-serif; line-height: 1.6;">
    <h2>High Vitamin B12 (Cobalamin Excess)</h2>
    <p>
        While vitamin B12 toxicity is rare (since it is a water-soluble vitamin), high levels of B12 can sometimes be associated with certain medical conditions or excess supplementation. The body typically excretes excess B12 through urine.
    </p>
    <h3>Root Causes of High Vitamin B12:</h3>
    <ul>
        <li><strong>Excessive Supplementation:</strong> High doses of B12 supplements or injections without medical supervision.</li>
        <li><strong>Liver Disease:</strong> Conditions like liver cirrhosis or hepatitis can release stored B12 into the bloodstream.</li>
        <li><strong>Kidney Dysfunction:</strong> Difficulty excreting excess B12 due to kidney problems.</li>
        <li><strong>Blood Disorders:</strong> Conditions like leukemia or polycythemia vera can cause elevated B12 levels.</li>
        <li><strong>Intestinal Issues:</strong> Small intestine bacterial overgrowth (SIBO) can alter B12 levels in the gut.</li>
        <li><strong>Excessive Animal Products:</strong> High consumption of organ meats like liver can lead to elevated B12 levels.</li>
    </ul>
    <h3>Symptoms of High Vitamin B12:</h3>
    <ul>
        <li>Acne or skin rashes (rare but reported)</li>
        <li>Nausea or vomiting</li>
        <li>Headaches or dizziness</li>
        <li>Fatigue or weakness (often related to underlying conditions)</li>
        <li>Increased risk of blood clots or cardiovascular issues</li>
    </ul>
    <h3>Tips for Managing High Vitamin B12:</h3>
    <ul>
        <li><strong>Review Supplementation:</strong> Reduce or stop supplements under medical guidance.</li>
        <li><strong>Monitor Medical Conditions:</strong> Work with your healthcare provider to manage underlying issues like liver or kidney disease.</li>
        <li><strong>Test for Underlying Conditions:</strong> Elevated levels may indicate serious health concerns requiring further testing.</li>
    </ul>
</div>
        """)

   

    
        if values["Vitamin D Total (D2 + D3)"] < 20:
            advice.append("""
<div style="font-family: Arial, sans-serif; line-height: 1.6;">
    <h2>Low Vitamin D Total (D2 + D3) – Deficiency</h2>
    <p>
        Low levels of Vitamin D Total (D2 + D3) indicate vitamin D deficiency, which can negatively impact bone health, immune function, and overall well-being.
    </p>
    <h3>Root Causes of Low Vitamin D Total (D2 + D3):</h3>
    <ul>
        <li><strong>Inadequate Sunlight Exposure:</strong> Lack of sun exposure, especially in regions with long winters or due to indoor lifestyles, can result in low Vitamin D levels.</li>
        <li><strong>Dietary Deficiency:</strong> Diets low in Vitamin D-rich foods like fatty fish, egg yolks, and fortified foods can cause deficiency, particularly in vegans or vegetarians.</li>
        <li><strong>Malabsorption Disorders:</strong> Conditions like Crohn's disease, celiac disease, or IBS can interfere with Vitamin D absorption.</li>
        <li><strong>Aging:</strong> Older adults produce less Vitamin D when exposed to sunlight, and their kidneys may be less efficient at converting Vitamin D to its active form.</li>
        <li><strong>Obesity:</strong> Vitamin D, being fat-soluble, can be stored in fat tissue, reducing its availability in the body.</li>
        <li><strong>Liver or Kidney Disease:</strong> These organs are essential for converting Vitamin D to its active form. Diseases like cirrhosis or kidney dysfunction can impair this process.</li>
        <li><strong>Medications:</strong> Certain drugs, like anticonvulsants or steroids, can disrupt Vitamin D metabolism and reduce its levels.</li>
    </ul>
    <h3>Health Implications of Low Vitamin D Total:</h3>
    <ul>
        <li><strong>Bone Health:</strong> Chronic deficiency can lead to osteomalacia (soft bones) or osteoporosis (fragile bones).</li>
        <li><strong>Muscle Weakness:</strong> Low Vitamin D levels can contribute to muscle weakness, especially in older adults.</li>
        <li><strong>Weakened Immune System:</strong> Deficiency impairs immune function, increasing infection risk.</li>
        <li><strong>Mood Disorders:</strong> Linked to depression and anxiety.</li>
        <li><strong>Chronic Conditions:</strong> Deficiency may raise the risk of cardiovascular diseases and type 2 diabetes.</li>
    </ul>
    <h3>Tips to Increase Vitamin D Total (D2 + D3):</h3>
    <ul>
        <li><strong>Increase Sun Exposure:</strong> Spend 10–30 minutes in direct sunlight several times a week, exposing large areas of skin (face, arms, legs).</li>
        <li><strong>Dietary Sources:</strong> Include foods like fatty fish (salmon, sardines, mackerel), egg yolks, fortified dairy and plant-based milks, cereals, and liver (chicken or beef).</li>
        <li><strong>Supplements:</strong> Vitamin D3 supplements may be needed for at-risk individuals. Consult a healthcare provider for dosage recommendations.</li>
        <li><strong>Manage Malabsorption Conditions:</strong> Address digestive disorders like celiac disease or Crohn's disease to improve Vitamin D absorption.</li>
        <li><strong>Regular Monitoring:</strong> Regular blood tests can help ensure sufficient Vitamin D levels, especially for high-risk groups (e.g., elderly or obese individuals).</li>
    </ul>
</div>
        """)
        elif values["Vitamin D Total (D2 + D3)"] > 100:
            advice.append("""
<div style="font-family: Arial, sans-serif; line-height: 1.6;">
    <h2>High Vitamin D Total (D2 + D3) – Toxicity or Excess</h2>
    <p>
        High levels of Vitamin D Total (D2 + D3) indicate Vitamin D toxicity or excessive intake, often caused by over-supplementation rather than natural sources like food or sunlight.
    </p>
    <h3>Root Causes of High Vitamin D Total (D2 + D3):</h3>
    <ul>
        <li><strong>Excessive Supplementation:</strong> Taking high doses of supplements (above 4,000 IU daily, or 10,000 IU in extreme cases) without supervision can cause toxicity.</li>
        <li><strong>Fortified Foods:</strong> Overconsumption of fortified foods alongside high-dose supplements may contribute to elevated levels.</li>
        <li><strong>Granulomatous Diseases:</strong> Diseases like sarcoidosis or tuberculosis can increase Vitamin D conversion, raising blood levels.</li>
        <li><strong>Hyperparathyroidism:</strong> Excessive parathyroid hormone (PTH) production can disrupt calcium and Vitamin D metabolism.</li>
    </ul>
    <h3>Health Implications of High Vitamin D Total:</h3>
    <ul>
        <li><strong>Hypercalcemia:</strong> Symptoms include nausea, vomiting, weakness, fatigue, confusion, kidney stones, and soft tissue calcification.</li>
        <li><strong>Kidney Damage:</strong> Excess calcium can cause kidney stones or, in severe cases, lead to kidney failure.</li>
        <li><strong>Bone Pain and Mineralization Issues:</strong> Prolonged high Vitamin D can cause bone pain and soft tissue calcification.</li>
        <li><strong>Cardiovascular Issues:</strong> High Vitamin D levels may lead to vascular calcification, increasing the risk of heart disease and stroke.</li>
    </ul>
    <h3>Tips to Manage High Vitamin D Total (D2 + D3):</h3>
    <ul>
        <li><strong>Stop Supplementation:</strong> Discontinue high-dose Vitamin D supplements immediately and consult a healthcare provider.</li>
        <li><strong>Monitor Calcium Levels:</strong> Check blood calcium levels for signs of hypercalcemia and take corrective measures as needed.</li>
        <li><strong>Increase Fluid Intake:</strong> Stay hydrated to flush out excess calcium through the kidneys.</li>
        <li><strong>Treat Underlying Conditions:</strong> Manage conditions like sarcoidosis or hyperparathyroidism to normalize Vitamin D levels.</li>
        <li><strong>Gradual Reduction:</strong> Reduce Vitamin D intake under medical supervision to avoid complications.</li>
    </ul>
</div>
        """)

    # Iron (range: 50-170 µg/dL)
        if values["Iron"] < 70:
            advice.append("""
<div style="font-family: Arial, sans-serif; line-height: 1.6;">
    <h2>Low Iron – Iron Deficiency</h2>
    <p>Low iron levels typically indicate iron deficiency, which can lead to various health complications.</p>
    <h3>Root Causes of Low Iron:</h3>
    <ul>
        <li><strong>Inadequate Dietary Intake:</strong> A diet lacking in iron-rich foods like red meat, poultry, fish, legumes, and leafy greens can cause low iron levels.</li>
        <li><strong>Blood Loss:</strong> Heavy menstruation, bleeding ulcers, gastric bleeding, or frequent blood donations can deplete iron levels over time.</li>
        <li><strong>Malabsorption:</strong> Conditions like celiac disease, Crohn's disease, or gastric bypass surgery can impair iron absorption.</li>
        <li><strong>Pregnancy:</strong> Increased iron demand during pregnancy often leads to deficiency if not supplemented.</li>
        <li><strong>Chronic Conditions:</strong> Chronic kidney disease or heart failure can affect iron metabolism, causing low iron levels.</li>
        <li><strong>Vegetarian or Vegan Diets:</strong> Non-heme iron from plant sources is less efficiently absorbed than heme iron from animal sources.</li>
    </ul>
    <h3>Health Implications of Low Iron:</h3>
    <ul>
        <li><strong>Iron-Deficiency Anemia:</strong> Fatigue, weakness, and paleness due to reduced hemoglobin production.</li>
        <li><strong>Impaired Oxygen Transport:</strong> Leads to shortness of breath, dizziness, and heart palpitations.</li>
        <li><strong>Weakened Immune System:</strong> Increased susceptibility to infections.</li>
        <li><strong>Hair Loss:</strong> May cause hair thinning or brittle hair.</li>
        <li><strong>Cold Intolerance:</strong> Low iron levels can cause cold sensitivity due to decreased blood flow.</li>
    </ul>
    <h3>Tips to Increase Iron Levels:</h3>
    <ul>
        <li><strong>Increase Iron-Rich Foods:</strong> 
            <ul>
                <li><strong>Heme Iron:</strong> Red meat, poultry, fish, and shellfish.</li>
                <li><strong>Non-Heme Iron:</strong> Spinach, lentils, beans, tofu, quinoa, fortified cereals, and iron-fortified bread and pasta.</li>
            </ul>
            Pair with Vitamin C-rich foods (like citrus fruits, tomatoes, and bell peppers) to enhance absorption.
        </li>
        <li><strong>Iron Supplements:</strong> Use supplements like ferrous sulfate under medical guidance to avoid iron overload.</li>
        <li><strong>Cook in Cast Iron Pans:</strong> Cooking acidic foods in cast iron pans increases iron content in meals.</li>
        <li><strong>Avoid Iron Blockers:</strong> Limit substances that inhibit absorption:
            <ul>
                <li>Coffee and tea (tannins).</li>
                <li>Calcium-rich foods (when consumed with iron-rich meals).</li>
                <li>High-fiber foods (in excess with iron-rich foods).</li>
            </ul>
        </li>
        <li><strong>Manage Menstrual Flow:</strong> Consult a doctor for heavy periods to reduce blood loss.</li>
    </ul>
</div>
        """)
        elif values["Iron"] > 180:
            advice.append("""
<div style="font-family: Arial, sans-serif; line-height: 1.6;">
    <h2>High Iron – Iron Overload (Hemochromatosis)</h2>
    <p>High iron levels indicate iron overload, where excessive iron accumulates in the body, potentially damaging organs.</p>
    <h3>Root Causes of High Iron:</h3>
    <ul>
        <li><strong>Hereditary Hemochromatosis:</strong> A genetic disorder causing excessive iron absorption, leading to tissue and organ damage.</li>
        <li><strong>Excessive Iron Supplementation:</strong> Overuse of supplements without medical supervision can cause toxicity.</li>
        <li><strong>Frequent Blood Transfusions:</strong> Individuals with anemia or blood disorders may accumulate excess iron from transfusions.</li>
        <li><strong>Liver Disease:</strong> Conditions like chronic hepatitis or cirrhosis impair iron metabolism, causing overload.</li>
        <li><strong>Chronic Alcoholism:</strong> Excessive alcohol consumption damages the liver, affecting iron metabolism.</li>
    </ul>
    <h3>Health Implications of High Iron:</h3>
    <ul>
        <li><strong>Liver Damage:</strong> Can lead to cirrhosis, fibrosis, or liver cancer.</li>
        <li><strong>Heart Problems:</strong> Iron accumulation in the heart may cause arrhythmias, heart failure, and cardiomyopathy.</li>
        <li><strong>Diabetes:</strong> High iron levels may impair insulin production, causing diabetes.</li>
        <li><strong>Joint Pain:</strong> Excess iron in joints can lead to arthritis.</li>
        <li><strong>Endocrine Disorders:</strong> Iron overload may disrupt hormones by affecting glands like the thyroid and adrenal glands.</li>
    </ul>
    <h3>Tips to Manage High Iron Levels:</h3>
    <ul>
        <li><strong>Phlebotomy (Blood Donation):</strong> Regular blood donation or therapeutic phlebotomy helps reduce iron levels in individuals with hereditary hemochromatosis.</li>
        <li><strong>Iron Chelation Therapy:</strong> Medications like deferoxamine or deferasirox help excrete excess iron for those unable to donate blood.</li>
        <li><strong>Avoid Iron-Rich Foods and Supplements:</strong> Limit foods like red meat, liver, and iron-fortified cereals. Avoid supplements unless prescribed.</li>
        <li><strong>Limit Vitamin C Intake:</strong> Avoid high Vitamin C with iron-rich meals to reduce absorption.</li>
        <li><strong>Avoid Alcohol:</strong> Reduce alcohol intake to prevent further liver damage.</li>
        <li><strong>Regular Monitoring:</strong> Monitor serum ferritin and transferrin saturation levels to prevent organ damage.</li>
    </ul>
</div>
        """)

    # Transferrin Saturation (range: 20-50%)
        if values["Transferrin Saturation"] < 18:
            advice.append("""
<div style="font-family: Arial, sans-serif; line-height: 1.6;">
    <h2>Low Transferrin Saturation – Iron Deficiency</h2>
    <p>Low transferrin saturation indicates that the amount of iron bound to transferrin is lower than normal, which usually suggests iron deficiency.</p>
    <h3>Root Causes of Low Transferrin Saturation:</h3>
    <ul>
        <li><strong>Iron Deficiency:</strong> Inadequate dietary intake of iron or poor absorption can result in iron deficiency anemia.</li>
        <li><strong>Chronic Blood Loss:</strong> Conditions like heavy menstruation, gastric ulcers, or hemorrhoids can lead to decreased iron levels.</li>
        <li><strong>Malabsorption Syndromes:</strong> Diseases like celiac disease, Crohn’s disease, or gastric bypass surgery can impair absorption.</li>
        <li><strong>Pregnancy:</strong> Increased iron requirements during pregnancy may cause low transferrin saturation if iron intake is insufficient.</li>
        <li><strong>Acute or Chronic Inflammation:</strong> Conditions like chronic kidney disease or rheumatoid arthritis can result in anemia of chronic disease.</li>
        <li><strong>Hypoproteinemia:</strong> Low protein levels from liver disease or malnutrition can reduce transferrin production.</li>
    </ul>
    <h3>Health Implications of Low Transferrin Saturation:</h3>
    <ul>
        <li><strong>Iron-Deficiency Anemia:</strong> Symptoms include fatigue, paleness, dizziness, and headaches.</li>
        <li><strong>Weak Immune System:</strong> Increased susceptibility to infections due to low iron.</li>
        <li><strong>Hair Loss:</strong> Insufficient iron can cause brittle hair and hair thinning.</li>
        <li><strong>Cognitive Impairments:</strong> May lead to concentration problems and memory difficulties.</li>
    </ul>
    <h3>Tips to Increase Transferrin Saturation (for Iron Deficiency):</h3>
    <ul>
        <li><strong>Increase Iron-Rich Foods:</strong>
            <ul>
                <li><strong>Heme Iron:</strong> Red meat, poultry, fish, and shellfish.</li>
                <li><strong>Non-Heme Iron:</strong> Spinach, lentils, tofu, beans, quinoa, and fortified cereals.</li>
            </ul>
            Pair with Vitamin C (e.g., citrus fruits, tomatoes) to enhance absorption.
        </li>
        <li><strong>Iron Supplements:</strong> For severe deficiencies, use supplements like ferrous sulfate under medical guidance.</li>
        <li><strong>Cook with Cast Iron Cookware:</strong> Cooking acidic foods (e.g., tomatoes) in cast iron pans can increase iron content.</li>
        <li><strong>Treat Underlying Conditions:</strong> Address issues like chronic blood loss or inflammation to improve iron levels.</li>
    </ul>
</div>
        """)
        elif values["Transferrin Saturation"] > 40:
            advice.append("""
<div style="font-family: Arial, sans-serif; line-height: 1.6;">
    <h2>High Transferrin Saturation – Iron Overload</h2>
    <p>High transferrin saturation suggests that a larger percentage of transferrin is bound to iron, which could indicate iron overload.</p>
    <h3>Root Causes of High Transferrin Saturation:</h3>
    <ul>
        <li><strong>Hereditary Hemochromatosis:</strong> A genetic disorder causing excessive iron absorption and iron buildup in organs.</li>
        <li><strong>Excessive Iron Supplementation:</strong> Overuse of iron supplements can lead to high transferrin saturation.</li>
        <li><strong>Frequent Blood Transfusions:</strong> Conditions like thalassemia or sickle cell disease can result in iron accumulation.</li>
        <li><strong>Chronic Liver Disease:</strong> Conditions like cirrhosis or hepatitis can impair iron metabolism.</li>
        <li><strong>Iron Overload Due to Other Disorders:</strong> Blood diseases can increase iron storage, leading to high transferrin saturation.</li>
        <li><strong>Excessive Vitamin C Intake:</strong> High Vitamin C levels may exacerbate iron overload by increasing absorption.</li>
    </ul>
    <h3>Health Implications of High Transferrin Saturation:</h3>
    <ul>
        <li><strong>Iron Toxicity:</strong> Excess iron can damage organs like the liver, heart, and pancreas.</li>
        <li><strong>Joint Pain:</strong> Iron deposition in joints may lead to arthritis.</li>
        <li><strong>Endocrine Dysfunction:</strong> Iron overload may disrupt hormone production, causing conditions like diabetes.</li>
        <li><strong>Cardiac Issues:</strong> Excess iron can lead to arrhythmias, heart failure, and cardiomyopathy.</li>
    </ul>
    <h3>Tips to Manage High Transferrin Saturation (for Iron Overload):</h3>
    <ul>
        <li><strong>Phlebotomy (Blood Donation):</strong> Regular blood donation or therapeutic phlebotomy is often the first-line treatment.</li>
        <li><strong>Iron Chelation Therapy:</strong> Medications like deferoxamine or deferasirox can help excrete excess iron.</li>
        <li><strong>Limit Iron-Rich Foods:</strong> Reduce intake of red meat, liver, and iron-fortified cereals.</li>
        <li><strong>Avoid Vitamin C Supplements:</strong> Avoid high doses of Vitamin C, which increase iron absorption.</li>
        <li><strong>Monitor Iron Levels:</strong> Regular monitoring of serum ferritin and transferrin saturation can help manage iron levels effectively.</li>
    </ul>
</div>
        """)

        return advice if advice else ["No specific advice. Keep maintaining a healthy lifestyle!"]

def analyze_deficiencies(results):
    advice = []

    if float(results['Haemoglobin']) < 13 or float(results['Iron']) < 70 or float(results['Transferrin Saturation']) < 18:
        advice.append({
            "deficiency": "Iron Deficiency",
            "recommendation": """
                <h3>Iron Deficiency</h3>
                <ul>
                    <li><strong>Diet:</strong> Increase intake of iron-rich foods like red meat, liver, spinach, lentils, beans, and fortified cereals.</li>
                    <li><strong>Supplements:</strong> Consider iron supplements (ferrous sulfate) after consulting your doctor. Take with Vitamin C to improve absorption.</li>
                    <li><strong>Lifestyle:</strong> Avoid tea/coffee during meals as it inhibits iron absorption.</li>
                </ul>
            """
        })

    if float(results['Vitamin B12']) < 211:
        advice.append({
            "deficiency": "Vitamin B12 Deficiency",
            "recommendation": """
                <h3>Vitamin B12 Deficiency</h3>
                <ul>
                    <li><strong>Diet:</strong> Include animal products like eggs, milk, cheese, chicken, and fish. For vegetarians, try fortified cereals or plant-based milks.</li>
                    <li><strong>Supplements:</strong> Take Vitamin B12 supplements or injections based on severity.</li>
                    <li><strong>Lifestyle:</strong> Regularly monitor levels if on a vegan diet.</li>
                </ul>
            """
        })

    if float(results['Vitamin D Total (D2 + D3)']) < 30:
        advice.append({
            "deficiency": "Vitamin D Deficiency",
            "recommendation": """
                <h3>Vitamin D Deficiency</h3>
                <ul>
                    <li><strong>Diet:</strong> Include fatty fish (salmon, mackerel), egg yolks, and fortified dairy products.</li>
                    <li><strong>Supplements:</strong> Vitamin D3 supplements (cholecalciferol) are recommended, especially during winter.</li>
                    <li><strong>Lifestyle:</strong> Spend 15-20 minutes in sunlight daily (preferably in the morning).</li>
                </ul>
            """
        })

    if float(results['Total Protein']) < 6.6 or float(results['Albumin']) < 3.5:
        advice.append({
            "deficiency": "Protein Deficiency",
            "recommendation": """
                <h3>Protein Deficiency</h3>
                <ul>
                    <li><strong>Diet:</strong> Increase lean protein sources like chicken, turkey, eggs, tofu, beans, nuts, and seeds.</li>
                    <li><strong>Supplements:</strong> Consider protein powders if dietary intake is insufficient.</li>
                    <li><strong>Lifestyle:</strong> Ensure balanced meals with protein in every meal.</li>
                </ul>
            """
        })

    if float(results['Total Cholesterol']) > 200 or float(results['LDL Cholesterol']) > 100 or float(results['Triglycerides']) > 150:
        advice.append({
            "deficiency": "Cholesterol Imbalance",
            "recommendation": """
                <h3>Cholesterol Imbalance</h3>
                <ul>
                    <li><strong>Diet:</strong> Reduce saturated fats and trans fats. Include foods high in omega-3 fatty acids (salmon, walnuts, flaxseeds). Add soluble fiber from oats, fruits, and vegetables.</li>
                    <li><strong>Supplements:</strong> Omega-3 fish oil supplements can help lower triglycerides.</li>
                    <li><strong>Lifestyle:</strong> Exercise regularly (150 minutes/week), maintain a healthy weight, and avoid smoking.</li>
                </ul>
            """
        })

    if float(results['Fasting Plasma Glucose']) > 100 or float(results['Glycated Hemoglobin']) > 5.7:
        advice.append({
            "deficiency": "High Blood Sugar",
            "recommendation": """
                <h3>High Blood Sugar</h3>
                <ul>
                    <li><strong>Diet:</strong> Follow a low-glycemic index diet with whole grains, vegetables, lean protein, and healthy fats. Avoid sugary foods and refined carbs.</li>
                    <li><strong>Supplements:</strong> Chromium and magnesium supplements may help regulate blood sugar levels.</li>
                    <li><strong>Lifestyle:</strong> Regular exercise, stress management, and weight loss are critical.</li>
                </ul>
            """
        })
    
        # 9. Thyroid Dysfunction
    if float(results['TSH Ultrasensitive']) > 4.78:
        advice.append({
            "deficiency": "Hypothyroidism",
            "recommendation": """<ul>
<li><strong>Diet</strong>: Add iodine-rich foods like iodized salt, seaweed, fish, and dairy. Selenium-rich foods (Brazil nuts) also support thyroid health.</li>
<li><strong>Supplements</strong>: Consult your doctor for levothyroxine if diagnosed.</li>
<li><strong>Lifestyle</strong>: Regular check-ups and medication adherence are critical.</li>
</ul>"""
        })

    # 10. Uric Acid Elevation (Gout Risk)
    if float(results['Uric Acid']) > 7.2:
        advice.append({
            "deficiency": "High Uric Acid (Gout Risk)",
            "recommendation": """<ul>
<li><strong>Diet</strong>: Reduce purine-rich foods like red meat, shellfish, and alcohol. Increase cherries, citrus fruits, and water intake.</li>
<li><strong>Supplements</strong>: Vitamin C may help reduce uric acid levels.</li>
<li><strong>Lifestyle</strong>: Maintain a healthy weight and avoid dehydration.</li>
</ul>"""
        })

    # 11. Kidney Health (Creatinine and e-GFR)
    if float(results['Creatinine']) > 1.2 or float(results['e-GFR (Glomerular Filtration Rate)']) < 90:
        advice.append({
            "deficiency": "Kidney Function Impairment",
            "recommendation": """<ul>
<li><strong>Diet</strong>: Limit protein intake to moderate levels. Avoid high-sodium and high-potassium foods if advised by your doctor.</li>
<li><strong>Supplements</strong>: Avoid nephrotoxic supplements without consulting a healthcare professional.</li>
<li><strong>Lifestyle</strong>: Stay hydrated and monitor kidney function regularly.</li>
</ul>"""
        })

    # 12. High SGPT/ALT or SGOT/AST (Liver Health)
    if float(results['SGPT/ALT']) > 50 or float(results['SGOT/AST']) > 50:
        advice.append({
            "deficiency": "Liver Health Issues",
            "recommendation": """<ul>
<li><strong>Diet</strong>: Avoid alcohol and processed foods. Add antioxidant-rich foods like berries, leafy greens, and green tea.</li>
<li><strong>Supplements</strong>: Milk thistle or N-acetylcysteine may help, but consult your doctor.</li>
<li><strong>Lifestyle</strong>: Maintain a healthy weight and avoid hepatotoxic substances.</li>
</ul>"""
        })

    # 16. Anemia (Low Red Blood Cell Count)
    if float(results.get('Total RBC Count', '0')) < 4.2:
        advice.append({
            "deficiency": "Anemia",
            "recommendation": """<ul>
<li><strong>Diet</strong>: Focus on foods rich in iron, folate, and Vitamin B12, such as red meat, spinach, beans, and eggs.</li>
<li><strong>Supplements</strong>: Iron or multivitamin supplements may help, based on the cause of anemia.</li>
<li><strong>Lifestyle</strong>: Monitor symptoms like fatigue and dizziness and consult a doctor for further investigation.</li>
</ul>"""
        })

    if float(results['Erythrocyte Sedimentation Rate']) > 15:
        advice.append({
        "deficiency": "High ESR (Inflammation)",
        "recommendation": """
        <h2>Diet</h2>
        <p>Consume anti-inflammatory foods like fatty fish, turmeric, ginger, berries, and green tea.</p>
        <h2>Supplements</h2>
        <p>Omega-3 fatty acids or turmeric with curcumin may help reduce inflammation.</p>
        <h2>Lifestyle</h2>
        <p>Identify and manage underlying conditions, and practice regular stress management techniques.</p>
        """
    })

    if float(results['Alkaline Phosphatase']) < 43:
        advice.append({
        "deficiency": "Low Alkaline Phosphatase",
        "recommendation": """
        <h2>Diet</h2>
        <p>Increase intake of zinc and Vitamin B6-rich foods such as poultry, fish, nuts, and whole grains.</p>
        <h2>Supplements</h2>
        <p>Zinc or Vitamin B6 supplements may be required if dietary intake is insufficient.</p>
        <h2>Lifestyle</h2>
        <p>Ensure regular health check-ups to monitor bone and liver health.</p>
        """
    })

    if float(results['Alkaline Phosphatase']) > 115:
        advice.append({
        "deficiency": "High Alkaline Phosphatase",
        "recommendation": """
        <h2>Diet</h2>
        <p>Limit intake of processed foods and ensure adequate hydration.</p>
        <h2>Supplements</h2>
        <p>Avoid unnecessary supplements, especially those containing Vitamin D and calcium, without consulting a doctor.</p>
        <h2>Lifestyle</h2>
        <p>Investigate underlying causes, such as bone or liver issues, with medical guidance.</p>
        """
    })

    if float(results['RDW']) > 14:
        advice.append({
        "deficiency": "High RDW (Possible Anemia or Nutritional Deficiency)",
        "recommendation": """
        <h2>Diet</h2>
        <p>Include foods rich in iron, folate, and Vitamin B12 such as spinach, lentils, red meat, and eggs.</p>
        <h2>Supplements</h2>
        <p>Depending on the cause, iron or multivitamin supplements may be beneficial.</p>
        <h2>Lifestyle</h2>
        <p>Regularly monitor blood parameters and address the underlying condition with professional advice.</p>
        """
    })

    if float(results['Total Bilirubin']) > 1.2:
        advice.append({
        "deficiency": "Elevated Bilirubin (Liver Health Concern)",
        "recommendation": """
        <h2>Diet</h2>
        <p>Follow a liver-friendly diet with fruits, vegetables, and whole grains. Avoid alcohol and fatty foods.</p>
        <h2>Supplements</h2>
        <p>Milk thistle or turmeric may support liver health, but consult your doctor first.</p>
        <h2>Lifestyle</h2>
        <p>Manage stress, stay hydrated, and maintain a healthy weight.</p>
        """
    })

    if float(results['Urea']) > 43 or float(results['Blood Urea Nitrogen']) > 20:
        advice.append({
        "deficiency": "High Urea or BUN (Kidney Stress)",
        "recommendation": """
        <h2>Diet</h2>
        <p>Limit high-protein foods such as red meat and dairy if advised by a healthcare provider. Increase hydration.</p>
        <h2>Supplements</h2>
        <p>Avoid nephrotoxic supplements without medical advice.</p>
        <h2>Lifestyle</h2>
        <p>Monitor kidney function and avoid excessive exercise that can increase protein breakdown.</p>
        """
    })

    if float(results['Globulin']) < 1.8:
        advice.append({
        "deficiency": "Low Globulin Levels",
        "recommendation": """
        <h2>Diet</h2>
        <p>Increase intake of protein-rich foods like eggs, dairy, beans, and lean meats.</p>
        <h2>Supplements</h2>
        <p>Consider protein powders or amino acid supplements if necessary.</p>
        <h2>Lifestyle</h2>
        <p>Ensure a balanced diet and address any underlying infections or inflammation.</p>
        """
    })

    if float(results['Globulin']) > 3.6:
        advice.append({
        "deficiency": "High Globulin Levels",
        "recommendation": """
        <h2>Diet</h2>
        <p>Focus on anti-inflammatory foods such as leafy greens, berries, and fatty fish. Avoid excessive processed or fatty foods.</p>
        <h2>Lifestyle</h2>
        <p>Consult a doctor to investigate potential chronic infections or immune-related disorders.</p>
        """
    })

    if float(results['T3 Total']) < 0.6 or float(results['T4 Total']) < 3.2:
        advice.append({
        "deficiency": "Hypothyroidism (Low Thyroid Hormones)",
        "recommendation": """
        <h2>Diet</h2>
        <p>Include iodine-rich foods such as iodized salt, seaweed, and seafood. Selenium-rich foods (Brazil nuts, sunflower seeds) also help.</p>
        <h2>Supplements</h2>
        <p>Consult a doctor for thyroid hormone replacement therapy if required.</p>
        <h2>Lifestyle</h2>
        <p>Regularly monitor thyroid levels and ensure medication adherence if prescribed.</p>
        """
    })

    if float(results['T3 Total']) > 1.81 or float(results['T4 Total']) > 12.6:
        advice.append({
        "deficiency": "Hyperthyroidism (Overactive Thyroid)",
        "recommendation": """
        <h2>Diet</h2>
        <p>Avoid iodine-rich foods like seaweed and iodized salt if advised by a doctor. Focus on a balanced diet to manage energy levels.</p>
        <h2>Lifestyle</h2>
        <p>Consult an endocrinologist for appropriate treatment and regularly monitor thyroid levels.</p>
        """
    })

    if float(results['Albumin']) < 3.5:
        advice.append({
        "deficiency": "Low Albumin Levels",
        "recommendation": """
        <h2>Diet</h2>
        <p>Add high-quality protein sources such as eggs, chicken, fish, and dairy.</p>
        <h2>Supplements</h2>
        <p>Protein supplements or albumin infusion may be required in severe cases, based on medical advice.</p>
        <h2>Lifestyle</h2>
        <p>Stay hydrated and manage chronic illnesses that may affect protein metabolism.</p>
        """
    })

    if float(results['Gamma Glutamyl Transferase']) > 55:
        advice.append({
        "deficiency": "High GGT (Liver Health Concern)",
        "recommendation": """
        <h2>Diet</h2>
        <p>Avoid alcohol and focus on liver-supporting foods like green vegetables, citrus fruits, and garlic.</p>
        <h2>Supplements</h2>
        <p>Milk thistle or NAC may support liver detoxification after consulting a healthcare provider.</p>
        <h2>Lifestyle</h2>
        <p>Avoid hepatotoxic substances and maintain a healthy lifestyle.</p>
        """
    })

    if float(results['Platelet Count']) > 410000:
        advice.append({
        "deficiency": "High Platelet Count (Thrombocytosis)",
        "recommendation": """
        <h2>Diet</h2>
        <p>Maintain a balanced diet with anti-inflammatory foods such as olive oil, nuts, and fatty fish.</p>
        <h2>Supplements</h2>
        <p>Avoid supplements that may exacerbate clotting without medical advice.</p>
        <h2>Lifestyle</h2>
        <p>Address underlying causes like inflammation or infection with medical support.</p>
        """
    })

    if float(results['Platelet Count']) < 150000:
        advice.append({
        "deficiency": "Low Platelet Count (Thrombocytopenia)",
        "recommendation": """
        <h2>Diet</h2>
        <p>Include foods that promote platelet production like papaya leaves, spinach, pumpkin, and citrus fruits.</p>
        <h2>Supplements</h2>
        <p>Consult a doctor for appropriate treatments or supplements like folate or Vitamin K.</p>
        <h2>Lifestyle</h2>
        <p>Avoid activities that may lead to injuries or excessive bleeding.</p>
        """
    })



    return advice if advice else ["No specific advice. Keep maintaining a healthy lifestyle!"]

   



@app.route("/", methods=["GET", "POST"])
def homepage():
    return render_template("index.html")

@app.route("/blogspage", methods=["GET", "POST"])
def blogs():
    return render_template("blog.html")

@app.route("/userblog/<blog_id>", methods=["GET"])
def blogpage(blog_id):
    print(f"Blog ID: {blog_id}")  # For debugging purposes
    # Pass the blog_id to the HTML template
    return render_template("userblog.html", blog_id=blog_id)



@app.template_filter('extract_h2')
def extract_h2(value):
    match = re.search(r'<h2[^>]*>(.*?)</h2>', value, re.IGNORECASE)
    return match.group(1) if match else 'No Title Available'

app.jinja_env.filters['extract_h2'] = extract_h2

@app.route("/uploads", methods=["GET", "POST"])
def home():
    if 'values' not in session:
        session['values'] = OrderedDict([
            ("Haemoglobin", 0),
            ("Total RBC Count", 0),
            ("Packed Cell Volume / Hematocrit", 0),
            ("MCV", 0),
            ("MCH", 0),
            ("MCHC", 0),
            ("RDW", 0),
            ("Total Leucocytes Count", 0),
            ("Neutrophils", 0),
            ("Lymphocytes", 0),
            ("Eosinophils", 0),
            ("Monocytes", 0),
            ("Basophils", 0),
            ("Absolute Neutrophil Count", 0),
            ("Absolute Lymphocyte Count", 0),
            ("Absolute Eosinophil Count", 0),
            ("Absolute Monocyte Count", 0),
            ("Platelet Count", 0),
            ("Erythrocyte Sedimentation Rate", 0),
            ("Fasting Plasma Glucose", 0),
            ("Glycated Hemoglobin", 0),
            ("Triglycerides", 0),
            ("Total Cholesterol", 0),
            ("LDL Cholesterol", 0),
            ("HDL Cholesterol", 0),
            ("VLDL Cholesterol", 0),
            ("Total Cholesterol / HDL Cholesterol Ratio", 0),
            ("LDL Cholesterol / HDL Cholesterol Ratio", 0),
            ("Total Bilirubin", 0),
            ("Direct Bilirubin", 0),
            ("Indirect Bilirubin", 0),
            ("SGPT/ALT", 0),
            ("SGOT/AST", 0),
            ("Alkaline Phosphatase", 0),
            ("Total Protein", 0),
            ("Albumin", 0),
            ("Globulin", 0),
            ("Protein A/G Ratio", 0),
            ("Gamma Glutamyl Transferase", 0),
            ("Creatinine", 0),
            ("e-GFR (Glomerular Filtration Rate)", 0),
            ("Urea", 0),
            ("Blood Urea Nitrogen", 0),
            ("Uric Acid", 0),
            ("T3 Total", 0),
            ("T4 Total", 0),
            ("TSH Ultrasensitive", 0),
            ("Vitamin B12", 0),
            ("Vitamin D Total (D2 + D3)", 0),
            ("Iron", 0),
            ("Total Iron Binding Capacity", 0),
            ("Transferrin Saturation", 0)
        ])

        session.modified = True

    values = session.get('values', OrderedDict([
            ("Haemoglobin", 0),
            ("Total RBC Count", 0),
            ("Packed Cell Volume / Hematocrit", 0),
            ("MCV", 0),
            ("MCH", 0),
            ("MCHC", 0),
            ("RDW", 0),
            ("Total Leucocytes Count", 0),
            ("Neutrophils", 0),
            ("Lymphocytes", 0),
            ("Eosinophils", 0),
            ("Monocytes", 0),
            ("Basophils", 0),
            ("Absolute Neutrophil Count", 0),
            ("Absolute Lymphocyte Count", 0),
            ("Absolute Eosinophil Count", 0),
            ("Absolute Monocyte Count", 0),
            ("Platelet Count", 0),
            ("Erythrocyte Sedimentation Rate", 0),
            ("Fasting Plasma Glucose", 0),
            ("Glycated Hemoglobin", 0),
            ("Triglycerides", 0),
            ("Total Cholesterol", 0),
            ("LDL Cholesterol", 0),
            ("HDL Cholesterol", 0),
            ("VLDL Cholesterol", 0),
            ("Total Cholesterol / HDL Cholesterol Ratio", 0),
            ("LDL Cholesterol / HDL Cholesterol Ratio", 0),
            ("Total Bilirubin", 0),
            ("Direct Bilirubin", 0),
            ("Indirect Bilirubin", 0),
            ("SGPT/ALT", 0),
            ("SGOT/AST", 0),
            ("Alkaline Phosphatase", 0),
            ("Total Protein", 0),
            ("Albumin", 0),
            ("Globulin", 0),
            ("Protein A/G Ratio", 0),
            ("Gamma Glutamyl Transferase", 0),
            ("Creatinine", 0),
            ("e-GFR (Glomerular Filtration Rate)", 0),
            ("Urea", 0),
            ("Blood Urea Nitrogen", 0),
            ("Uric Acid", 0),
            ("T3 Total", 0),
            ("T4 Total", 0),
            ("TSH Ultrasensitive", 0),
            ("Vitamin B12", 0),
            ("Vitamin D Total (D2 + D3)", 0),
            ("Iron", 0),
            ("Total Iron Binding Capacity", 0),
            ("Transferrin Saturation", 0)
        ]))
    advice = None

    if request.method == "POST":
        if "pdf_file" in request.files:
            pdf_file = request.files["pdf_file"]
            extracted_text = extract_text_from_pdf(pdf_file)
            
            values = OrderedDict(extract_values(extracted_text))
            
            session['values'] = list(values.items())  
            session.modified = True
            
            advice = give_health_advice(values)
            nutrient_advice=analyze_deficiencies(values)
            return render_template("results.html", values=values, advice=advice,nutrient_advice=nutrient_advice)

        elif request.form:
            values = OrderedDict(session.get('values', [])) 
            
            
            for key in values.keys():
                if key in request.form:
                    values[key] = float(request.form[key])  
            
            session['values'] = list(values.items()) 
            session.modified = True
            
            
            advice = give_health_advice(values)
            nutrient_advice=analyze_deficiencies(values)
            return render_template("results.html", values=values, advice=advice,nutrient_advice=nutrient_advice)


if __name__ == "__main__":
    app.run(debug=True)