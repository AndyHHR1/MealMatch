import kagglehub
import json
import os
import sys

# Download latest version
print("📥 Descargando dataset de Kaggle...")
path = kagglehub.dataset_download("thedevastator/healthy-diet-recipes-a-comprehensive-dataset")
print(f"✅ Descargado en: {path}")

# List archivos descargados
print("\n📂 Archivos descargados:")
for root, dirs, files in os.walk(path):
    level = root.replace(path, '').count(os.sep)
    indent = ' ' * 2 * level
    print(f"{indent}{os.path.basename(root)}/")
    subindent = ' ' * 2 * (level + 1)
    for file in files[:10]:  # Limitar a 10 archivos por carpeta
        print(f"{subindent}{file}")
    if len(files) > 10:
        print(f"{subindent}... ({len(files)} archivos total)")
