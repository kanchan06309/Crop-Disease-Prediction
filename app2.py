"""
Create class_labels.json for PlantVillage Dataset
Run this if training didn't create the file or labels are missing
"""

import json
import os

# PlantVillage Dataset - 38 Classes in alphabetical order
# These are the standard classes from the dataset
PLANT_VILLAGE_CLASSES = [
    "Apple___Apple_scab",
    "Apple___Black_rot",
    "Apple___Cedar_apple_rust",
    "Apple___healthy",
    "Blueberry___healthy",
    "Cherry_(including_sour)___Powdery_mildew",
    "Cherry_(including_sour)___healthy",
    "Corn_(maize)___Cercospora_leaf_spot Gray_leaf_spot",
    "Corn_(maize)___Common_rust_",
    "Corn_(maize)___Northern_Leaf_Blight",
    "Corn_(maize)___healthy",
    "Grape___Black_rot",
    "Grape___Esca_(Black_Measles)",
    "Grape___Leaf_blight_(Isariopsis_Leaf_Spot)",
    "Grape___healthy",
    "Orange___Haunglongbing_(Citrus_greening)",
    "Peach___Bacterial_spot",
    "Peach___healthy",
    "Pepper,_bell___Bacterial_spot",
    "Pepper,_bell___healthy",
    "Potato___Early_blight",
    "Potato___Late_blight",
    "Potato___healthy",
    "Raspberry___healthy",
    "Soybean___healthy",
    "Squash___Powdery_mildew",
    "Strawberry___Leaf_scorch",
    "Strawberry___healthy",
    "Tomato___Bacterial_spot",
    "Tomato___Early_blight",
    "Tomato___Late_blight",
    "Tomato___Leaf_Mold",
    "Tomato___Septoria_leaf_spot",
    "Tomato___Spider_mites Two-spotted_spider_mite",
    "Tomato___Target_Spot",
    "Tomato___Tomato_Yellow_Leaf_Curl_Virus",
    "Tomato___Tomato_mosaic_virus",
    "Tomato___healthy"
]

def create_class_labels():
    """Create class_labels.json file"""
    class_labels = {str(i): class_name for i, class_name in enumerate(PLANT_VILLAGE_CLASSES)}
    
    with open('class_labels.json', 'w') as f:
        json.dump(class_labels, f, indent=2)
    
    print("✓ Created class_labels.json")
    print(f"✓ Total classes: {len(class_labels)}")
    print(f"\nFirst 5 classes:")
    for i in range(5):
        print(f"  {i}: {class_labels[str(i)]}")
    print(f"\nLast 5 classes:")
    for i in range(33, 38):
        print(f"  {i}: {class_labels[str(i)]}")

def verify_with_dataset(data_dir='PlantVillage'):
    """Verify labels match actual dataset folders"""
    if not os.path.exists(data_dir):
        print(f"\n⚠ Warning: Dataset directory '{data_dir}' not found")
        print("Labels created based on standard PlantVillage dataset")
        return
    
    # Get actual folder names from dataset
    actual_classes = sorted([d for d in os.listdir(data_dir) 
                            if os.path.isdir(os.path.join(data_dir, d))])
    
    print(f"\n✓ Found {len(actual_classes)} folders in dataset")
    
    # Compare
    if set(PLANT_VILLAGE_CLASSES) == set(actual_classes):
        print("✓ Labels match dataset folders perfectly!")
    else:
        print("⚠ Warning: Some differences found")
        print(f"Expected: {len(PLANT_VILLAGE_CLASSES)} classes")
        print(f"Found: {len(actual_classes)} classes")
        
        # Show differences
        missing = set(PLANT_VILLAGE_CLASSES) - set(actual_classes)
        extra = set(actual_classes) - set(PLANT_VILLAGE_CLASSES)
        
        if missing:
            print(f"\nMissing from dataset: {missing}")
        if extra:
            print(f"\nExtra in dataset: {extra}")

if __name__ == "__main__":
    print("Creating class_labels.json for PlantVillage Dataset...\n")
    create_class_labels()
    verify_with_dataset()
    print("\n✓ Done! Now restart your Flask app.")