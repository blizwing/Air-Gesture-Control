# Air-Gesture-Control

This project provides a Windows-compatible gesture recognition system using OpenCV and MediaPipe.

## Setup

1. Install [Python 3.10](https://www.python.org/downloads/).
2. Install the [Visual C++ Build Tools](https://visualstudio.microsoft.com/visual-cpp-build-tools/) if MediaPipe fails to build.
3. Create a virtual environment and install dependencies:

```cmd
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
```

The `requirements.txt` file pins OpenCV below version 4.12 because newer
releases require `numpy>=2`, while MediaPipe still depends on `numpy<2`.

## Running

Run the main application:

```cmd
python main.py
```

A window will display the webcam feed with checkboxes to enable or disable gestures.
Swipe gestures control paging.
You can hide the main window with the **Hide** button and gestures will continue to work in the background.
