"""
Backward-compatible entrypoint: generates data into data/raw/.

Delegates to scripts.generate_data. Run from project root:
  python generate_fake_data.py
"""
from scripts.generate_data import main

if __name__ == "__main__":
    main()
