import os
import numpy as np
from deepface import DeepFace

def generate_average_embedding_from_existing():
    project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    face_folder = os.path.join(project_root, "face_data")
    embedding_path = os.path.join(face_folder, "vansh_face_embedding.npy")

    img_files = [f for f in os.listdir(face_folder) if f.lower().endswith((".jpg", ".jpeg", ".png"))]

    if not img_files:
        print("❌ No images found in face_data folder.")
        return

    embeddings = []
    for img_file in img_files:
        img_path = os.path.join(face_folder, img_file)
        try:
            rep = DeepFace.represent(img_path=img_path, model_name="ArcFace", enforce_detection=True)
            if rep:
                embeddings.append(np.array(rep[0]["embedding"]))
                print(f"✅ Processed embedding for {img_file}")
        except Exception as e:
            print(f"⚠️ Error processing {img_file}: {e}")

    if not embeddings:
        print("❌ No embeddings generated from images!")
        return

    avg_embedding = np.mean(embeddings, axis=0)
    np.save(embedding_path, avg_embedding)
    print(f"✅ Average embedding saved to {embedding_path}")

if __name__ == "__main__":
    generate_average_embedding_from_existing()
