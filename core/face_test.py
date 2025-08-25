from deepface import DeepFace
import numpy as np
import os

project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
face_folder = os.path.join(project_root, "face_data")
embedding_path = os.path.join(face_folder, "vansh_face_embedding.npy")

image_files = [f for f in os.listdir(face_folder) if f.lower().endswith((".jpg", ".jpeg", ".png"))]

if not image_files:
    print("❌ No images found in face_data folder.")
    exit(1)

embeddings = []

print(f"Found {len(image_files)} images. Generating embeddings...")

for img_file in image_files:
    img_path = os.path.join(face_folder, img_file)
    try:
        embedding = DeepFace.represent(img_path=img_path, model_name="ArcFace", enforce_detection=True)[0]["embedding"]
        embeddings.append(embedding)
        print(f"✅ Generated embedding for {img_file}")
    except Exception as e:
        print(f"❌ Failed on {img_file}: {e}")

if not embeddings:
    print("❌ No embeddings generated. Exiting.")
    exit(1)

# Average embeddings for final reference
avg_embedding = np.mean(embeddings, axis=0)

np.save(embedding_path, avg_embedding)

print(f"🎉 Saved averaged reference embedding at {embedding_path}")
print(f"Embedding shape: {avg_embedding.shape}")
print(f"First 5 values: {avg_embedding[:5]}")
