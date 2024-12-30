# DogeAutoSub

Just run the `DogeAutoSub.bat` file.

The first launch may take some time to load as it sets up the environment and downloads necessary dependencies.

## Model Sizes

There are six model sizes, four with English-only versions, offering speed and accuracy tradeoffs. Below are the names of the available models and their approximate memory requirements and inference speed relative to the large model. The relative speeds below are measured by transcribing English speech on an A100, and the real-world speed may vary significantly depending on many factors including the language, the speaking speed, and the available hardware.

| Size   | Parameters | English-only Model | Multilingual Model | Required VRAM | Relative Speed |
|--------|------------|--------------------|--------------------|---------------|----------------|
| tiny   | 39 M       | tiny.en            | tiny               | ~1 GB         | ~10x           |
| base   | 74 M       | base.en            | base               | ~1 GB         | ~7x            |
| small  | 244 M      | small.en           | small              | ~2 GB         | ~4x            |
| medium | 769 M      | medium.en          | medium             | ~5 GB         | ~2x            |
| large  | 1550 M     | N/A                | large              | ~10 GB        | 1x             |
| turbo  | 809 M      | N/A                | turbo              | ~6 GB         | ~8x            |