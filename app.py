from flask import Flask, request, jsonify, render_template, Response, session, url_for
from datetime import timedelta
from flask_jwt_extended import decode_token
import uuid

from dotenv import load_dotenv
from backend.ImageProcessor import ImageProcessor
from backend.S3Uploader import S3Uploader
from backend.StabbleDifusionApi import StableDiffusionApi
# from backend.core import GameInsightExtractor
from db.db import db
from flask_cors import CORS
from flask import send_from_directory
import os
import random
import bcrypt
from flask_jwt_extended import (
    JWTManager,
    create_access_token,
    jwt_required,
    create_refresh_token,
    get_jwt_identity,
)

from pymongo.errors import DuplicateKeyError
from bson import ObjectId
import base64
import shutil

# from backend.AmazonProductsSearchApi import AmazonProductsSearchApi
from backend.PromptProcessor import PromptProcessor
from backend.OutfitGenerator import OutfitGenerator
from backend.FaceEmbeddingGenerator import FaceEmbeddingGenerator

load_dotenv()
app = Flask(__name__)
app.secret_key = os.getenv("FLASK_SECRET_KEY")
app.config["JWT_SECRET_KEY"] = os.getenv("JWT_SECRET_KEY")
app.config["JWT_ACCESS_TOKEN_EXPIRES"] = timedelta(hours=1)
app.config["JWT_REFRESH_TOKEN_EXPIRES"] = timedelta(days=10)

jwt = JWTManager(app)

CORS(app)

# extractor = GameInsightExtractor()

stableDiffusionApi = StableDiffusionApi()
imageProcessor = ImageProcessor()
uploader = S3Uploader()
promptProcessor = PromptProcessor()

outfitGenerator = OutfitGenerator()
faceEmbeddingGenerator = FaceEmbeddingGenerator()

# amazon_search_api = AmazonProductsSearchApi('www.amazon.com')

@app.route("/api/generate_avatar", methods=["POST"])
# @jwt_required()
def generate_outfit():
    data = request.get_json()
    if data:
        prompt = data["prompt"]
        image_path = "images/avatar.png"
        negative_prompt = "ugly"
        result = faceEmbeddingGenerator.generate_image( image_path, prompt, negative_prompt)

        if result:
            image_name = uuid.uuid4().hex[:8]
            file_path = f'images/{image_name}.png'
            result.save(file_path)
            generated_image_url = uploader.upload_file(file_path, f'Images/avatars/{image_name}.png')
            try:
                os.remove(file_path)
                print(f"File '{file_path}' has been deleted.")
            except OSError as e:
                print(f"Error: {e.strerror}")

            return jsonify({"generated_image_url": generated_image_url}), 200
        else:
            return jsonify({"response": "Failed to generate image"}), 200
    else:
        return jsonify({"response": "Failed"}), 200

@app.route("/api/upload_main_image", methods=["PUT"])
# @jwt_required()
def upload_main_image():
    if 'image' not in request.files:
        return jsonify({'error': 'No image part'}), 400
    image_data = request.files.get("image")

    user_id = request.headers.get('X-User-Id')
    if user_id:
        filename = f'{user_id}_main_image.png'
        input_path = imageProcessor.save_image(image_data, filename)
        imageProcessor.process_image(input_path, user_id)

        file_path = f'closes-segmentation/input/{filename}'
        s3_file_key = f'{user_id}/Images/{filename}'
        user_image = {"user_id": user_id, "main_image_s3_key": s3_file_key}

        uploaded_file_url = uploader.upload_file(file_path, s3_file_key)
        if uploaded_file_url:
            print(f"File uploaded successfully. URL: {uploaded_file_url}")
            try:
                os.remove(file_path)
                print(f"File '{file_path}' has been deleted.")
            except OSError as e:
                print(f"Error: {e.strerror}")

            folder_path = f'closes-segmentation/output/alpha/{user_id}/'
            for filename in os.listdir(folder_path):
                file_path = os.path.join(folder_path, filename)

                # Skip directories, only upload files
                if os.path.isfile(file_path):
                    s3_file_key = f'{user_id}/Images/segmentations/{filename}'
                    uploaded_file_url = uploader.upload_file(file_path, s3_file_key)
                    if uploaded_file_url:
                        user_image[filename.split('.')[0]] = s3_file_key
                        print(f'Uploaded {filename} to {uploaded_file_url}')
                        try:
                            os.remove(file_path)
                            print(f"File '{file_path}' has been deleted.")
                        except OSError as e:
                            print(f"Error: {e.strerror}")
            try:
                shutil.rmtree(folder_path)
                print(f"Folder '{folder_path}' has been deleted.")
            except OSError as e:
                print(f"Error: {e.strerror}")
            
            folder_path = f'closes-segmentation/output/cloth_seg/{user_id}/'
            try:
                shutil.rmtree(folder_path)
                print(f"Folder '{folder_path}' has been deleted.")
            except OSError as e:
                print(f"Error: {e.strerror}")
            
            db_user_image = db.user_images.find_one({"user_id": user_id})
            if db_user_image:
                db.user_images.update_one({"_id": db_user_image["_id"]}, {"$set": user_image})
            else:
                db.user_images.insert_one(user_image)

        else:
            print("Failed to upload file.")

        return jsonify({"response": "done"}), 200
    else:
        return jsonify({"response": "Failed"}), 200

@app.route("/api/get_prompts", methods=["GET"])
# @jwt_required()
def get_prompts():
    user_id = request.headers.get('X-User-Id')
    if user_id:
        db_user = db.users.find_one({"_id": ObjectId(user_id)})
        if db_user:
            user_gender = db_user["gender"]
            user_age = db_user["age"]
            user_styles = db_user["styles"]
            user_styles = ','.join(user_styles)
            city = request.args.get('city', default="")
            weather = request.args.get('weather', default="")
            prompts = promptProcessor.get_prompts(user_gender, user_age, user_styles, city, weather)

            return jsonify({"prompts": prompts}), 200
        else:
            return jsonify({"response": "No such user"}), 400
    else:
        return jsonify({"response": "No user id sent"}), 400

@app.route("/api/generate_outfit", methods=["POST"])
# @jwt_required()
def generate_outfit():
    data = request.get_json()
    user_id = request.headers.get('X-User-Id')
    if user_id:
        db_user_image = db.user_images.find_one({"user_id": user_id})
        db_user = db.users.find_one({"_id": ObjectId(user_id)})
        if db_user_image and db_user:
            main_image_s3_file_key = db_user_image["main_image_s3_key"]
            upper_body_s3_file_key = db_user_image["upper_body"]
            lower_body_s3_file_key = db_user_image["lower_body"]

            user_gender = db_user["gender"]
            user_age = db_user["age"]
            user_styles = db_user["styles"]
            user_styles = ','.join(user_styles)

            main_image_url = uploader.generate_presigned_url(main_image_s3_file_key, 600)
            upper_mask_image_url = uploader.generate_presigned_url(upper_body_s3_file_key, 600)
            lower_mask_image_url = uploader.generate_presigned_url(lower_body_s3_file_key, 600)

            if main_image_url and upper_mask_image_url and lower_mask_image_url:
                user_input = data["prompt"]
                city = data["city"]
                weather = data["weather"]
                keywords = promptProcessor.get_keywords(user_input, user_gender, user_age, user_styles, city, weather)
                
                result = outfitGenerator.generateOutfit(user_id, keywords, main_image_url, upper_mask_image_url, lower_mask_image_url)
                image_name = result[0]
                file_path = result[1]
                products = result[2]
                s3_file_key = f'{user_id}/Images/generations/{image_name}'
                user_generation = {"user_id": user_id, "generation_s3_file_key": s3_file_key}
                db.user_generations.insert_one(user_generation)

                generated_image_url = uploader.upload_file(file_path, s3_file_key)
                
                try:
                    os.remove(file_path)
                    print(f"File '{file_path}' has been deleted.")
                except OSError as e:
                    print(f"Error: {e.strerror}")

                response = {"generated_image_url": generated_image_url}
                response["products"] = products
                return jsonify(
                                response
                        ), 201
            else:
                return jsonify({"response": "Failed to generate presigned URL"}), 200
        else:
            return jsonify({"response": "No Uploaded Image"}), 200
    else:
        return jsonify({"response": "Failed"}), 200

@app.route("/api/create_user", methods=["POST"])
# @jwt_required()
def create_user():
    data = request.get_json()
    new_user = {"gender": data["gender"], "age": data["age"], "styles": data["styles"]}

    try:
        result = db.users.insert_one(new_user)
        user_id_str = str(result.inserted_id)
    except DuplicateKeyError:
        return jsonify({"success": False, "message": "Failed to create user"}), 400
    return (
        jsonify(
            {
                "success": True,
                "message": "User registered successfully",
                "user_id": user_id_str
            }
        ),
        201,
    )

@app.route("/api/delete_user", methods=["POST"])
# @jwt_required()
def delete_user():
    user_id = request.headers.get('X-User-Id')
    if user_id:
        # Delete user document
        db.users.delete_one({"_id": ObjectId(user_id)})
        # Delete all user images documents
        delete_result = db.user_images.delete_many({"user_id": user_id})
        
        print(f"Deleted {delete_result.deleted_count} user images")

        return jsonify({"response": "User and associated images deleted successfully"}), 200
    else:
        return jsonify({"response": "User ID not provided"}), 400

    

@app.route('/terms_of_service')
def terms_of_service():
    return send_from_directory('static', 'tos.html')

@app.route('/privacy_policy')
def privacy_policy():
    return send_from_directory('static', 'privacy.html')

# @app.route("/api/token/refresh", methods=["POST"])
# @jwt_required(refresh=True)
# def refresh():
#     current_user_id = get_jwt_identity()
#     new_token = create_access_token(identity=current_user_id)
#     return jsonify({"access_token": new_token}), 200


# @app.route("/api/signup", methods=["POST"])
# def signup():
#     data = request.get_json()

#     # Check if email already exists
#     user = db.users.find_one({"email": data["email"]})
#     if user:
#         return jsonify({"success": False, "message": "Email already registered"}), 400

#     hashed_password = hash_password(data["password"])

#     new_user = {"email": data["email"], "password": hashed_password}

#     try:
#         result = db.users.insert_one(new_user)
#         user_id_str = str(result.inserted_id)
#         access_token = create_access_token(identity=user_id_str)
#         refresh_token = create_refresh_token(identity=user_id_str)
#     except DuplicateKeyError:
#         return jsonify({"success": False, "message": "Email already registered"}), 400

#     return (
#         jsonify(
#             {
#                 "success": True,
#                 "access_token": access_token,
#                 "refresh_token": refresh_token,
#                 "message": "User registered successfully",
#             }
#         ),
#         201,
#     )

# @app.route("/api/login", methods=["POST"])
# def login():
#     data = request.get_json()
#     user = db.users.find_one({"email": data["email"]})

#     if not user or not check_password(data["password"], user["password"]):
#         return jsonify({"success": False, "message": "Invalid email or password"}), 403

#     user_id_str = str(user["_id"])

#     access_token = create_access_token(identity=user_id_str)
#     refresh_token = create_refresh_token(identity=user_id_str)

#     return (
#         jsonify(
#             {
#                 "success": True,
#                 "access_token": access_token,
#                 "refresh_token": refresh_token,
#                 "message": "Login successful",
#             }
#         ),
#         200,
#     )


# @app.route("/api/ask-jenna-promts", methods=["POST"])
# @jwt_required()
# def ask_jenna_promts():
#     text_snippet = request.json.get("text", "")
#     response_list = extractor.get_prompts(text_snippet)
#     return jsonify(generated_response=response_list)


# @app.route("/api/create_project", methods=["POST"])
# @jwt_required()
# def create_project():
#     project_name = request.form.get("project_name")
#     brief = request.form.get("brief")
#     template_id = request.form.get("template_id")
#     brief_file = request.files.get("briefFile")
#     template_file = request.files.get("templateFile")

#     # Validate required fields
#     if (
#         not project_name
#         or not (brief or brief_file)
#         or not (template_id or template_file)
#     ):
#         return jsonify({"success": False, "message": "Missing required fields"}), 400

#     user_id = get_jwt_identity() 

#     # Prepare document to be inserted into MongoDB
#     new_project = {
#         "user_id": user_id,
#         "project_name": project_name,
#         "brief": brief,
#         "template_id": template_id,
#         "brief_file_path": f"uploads/{brief_file.filename}" if brief_file else None,
#         "template_file_path": f"uploads/{template_file.filename}"
#         if template_file
#         else None,
#     }

#     try:
#         # Insert the new project document into MongoDB
#         result = db.projects.insert_one(new_project)
#         project_id_str = str(result.inserted_id)

#          # Determine the directories
#         brief_dir = f"user_projects/{user_id}/{project_id_str}/brief"
#         template_dir = f"user_projects/{user_id}/{project_id_str}/template"

#         # Create directories if they don't exist
#         os.makedirs(brief_dir, exist_ok=True)
#         os.makedirs(template_dir, exist_ok=True)

#         # Save files to the directories
#         if brief_file:
#             brief_file.save(os.path.join(brief_dir, brief_file.filename))
#         if template_file:
#             template_file.save(os.path.join(template_dir, template_file.filename))
#     except Exception as e:
#         # Handle any exceptions that occur
#         return jsonify({"success": False, "message": str(e)}), 500

#     return (
#         jsonify(
#             {
#                 "success": True,
#                 "project_id": project_id_str,
#                 "message": "Project created successfully",
#             }
#         ),
#         201,
#     )

# @app.route("/api/get_projects", methods=["GET"])
# @jwt_required()
# def get_projects():
#     user_id = get_jwt_identity()

#     projects_cursor = db.projects.find({"user_id": user_id})
    
#     # Convert the projects to a list and then to JSON
#     projects_list = list(projects_cursor)
#     for project in projects_list:
#         project["_id"] = str(project["_id"])

#     return jsonify(projects_list), 200

# @app.route("/api/delete_project/<project_id>", methods=["DELETE"])
# @jwt_required()
# def delete_project(project_id):
#     user_id = get_jwt_identity()

#     try:
#         # Delete the project if it belongs to the logged-in user
#         result = db.projects.delete_one({"_id": ObjectId(project_id), "user_id": user_id})

#         if result.deleted_count == 0:
#             return jsonify({"success": False, "message": "Project not found or unauthorized"}), 404

#         return jsonify({"success": True, "message": "Project deleted successfully"}), 200

#     except Exception as e:
#         return jsonify({"success": False, "message": str(e)}), 500


# @app.route("/api/get_project/<project_id>", methods=["GET"])
# @jwt_required()
# def get_project(project_id):
#     user_id = get_jwt_identity()

#     try:
#         project = db.projects.find_one({"_id": ObjectId(project_id), "user_id": user_id})

#         if not project:
#             return jsonify({"success": False, "message": "Project not found"}), 404

#         # Convert the project ID to a string for JSON serialization
#         project["_id"] = str(project["_id"])

#         # Optionally, format or modify the response data as needed
#         return jsonify(project), 200

#     except Exception as e:
#         return jsonify({"success": False, "message": str(e)}), 500

# @app.route("/api/update_project/<project_id>", methods=["PUT"])
# @jwt_required()
# def update_project(project_id):
#     user_id = get_jwt_identity()
#     data = request.get_json()

#     try:
#         result = db.projects.update_one(
#             {"_id": ObjectId(project_id), "user_id": user_id},
#             {"$set": {
#                 "project_name": data["project_name"],
#                 "brief": data["brief"],
#                 "template_id": data["template_id"]
#                 # Add other fields as necessary
#             }}
#         )

#         if result.matched_count == 0:
#             return jsonify({"success": False, "message": "Project not found or unauthorized"}), 404

#         return jsonify({"success": True, "message": "Project updated successfully"}), 200

#     except Exception as e:
#         return jsonify({"success": False, "message": str(e)}), 500

# @app.route("/api/templates", methods=["GET"])
# def get_templates():
#     try:
#         templates_cursor = db.templates.find({})
#         templates_list = list(templates_cursor)

#         for template in templates_list:
#             template["_id"] = str(template["_id"])
#             template["image"] = request.url_root + url_for('static', filename=template["image"]).lstrip('/')

#         return jsonify(templates_list), 200

#     except Exception as e:
#         return jsonify({"success": False, "message": str(e)}), 500



# @app.route("/api/get-insights", methods=["POST"])
# @jwt_required()
# def get_insights():
#     text_snippet = request.json.get("text", "")
#     insight_data = request.json.get("insightData", "")
#     if len(text_snippet) == 0:
#         return {}
#     generated_insight = extractor.get_marketing_insight(text_snippet, insight_data)
#     if len(generated_insight) > 0:
#         return jsonify(generated_insight=generated_insight)
#     return {}


# @app.route("/api/process-conversation", methods=["POST"])
# @jwt_required()
# async def process_conversation():
#     message = request.json.get("message", "")

#     return Response(process_conversation_text(message), mimetype="text/plain")


# def process_conversation_text(message):
#     for chunk in extractor.run_llm_chat(message):
#         yield chunk


# def check_password(password: str, hashed: bytes) -> bool:
#     # Compare the provided password against the hashed version
#     return bcrypt.checkpw(password.encode("utf-8"), hashed)


# def hash_password(password: str) -> bytes:
#     # Generate a salt
#     salt = bcrypt.gensalt()

#     # Hash the password combined with the salt
#     hashed = bcrypt.hashpw(password.encode("utf-8"), salt)

#     return hashed


if __name__ == "__main__":
    app.run(async_mode="threading")  # or any other port you prefer
