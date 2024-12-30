import whisper

# List of all model sizes
model_sizes = ["tiny", "base", "small", "medium", "large", "turbo"]

# Download each model
for model_size in model_sizes:
    print(f"Downloading {model_size} model...")
    model = whisper.load_model(model_size)
    print(f"{model_size} model downloaded successfully.")