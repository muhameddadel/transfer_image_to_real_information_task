from setuptools import setup, find_packages

setup(
    name="fakturama-automation",
    version="1.0.0",
    description="Automated order-to-invoice processing for Fakturama",
    author="Your Name",
    packages=find_packages(),
    install_requires=[
        "uiautomation==2.0.16",
        "pyautogui==0.9.54",
        "opencv-python==4.8.1.78",
        "pytesseract==0.3.10",
        "Pillow==10.1.0",
        "openai==1.3.0",
        "pandas==2.1.3",
        "pydantic==2.5.0",
        "python-dotenv==1.0.0",
        "loguru==0.7.2",
        "click==8.1.7",
        "numpy==1.24.3",
    ],
    entry_points={
        "console_scripts": [
            "fakturama-auto=src.main:main",
        ],
    },
    python_requires=">=3.9",
)