# winrtqrabber

A QRcode webcam scanner for win10 only (no opencv, no pyzbar).
There are many tutorials available that explain how to scan a barcode using your webcam with python.
They all make use of opencv for camera access and pyzbar for decoding the barcode, but windows10 has all these capabilities built-in, and I wanted to use these, assuming this would lead to a cleaner/better (?) solution.

This package makes use of the python bindings for winrt (https://pypi.org/project/winrt/), which allows using the "Universal Windows Platform" API directly. For Barcode specific info: https://docs.microsoft.com/en-us/uwp/api/windows.devices.pointofservice.barcodescanner?view=winrt-19041

## Installation

`pip install winrtqrabber`

## Demo

Clone the repo or copy the `demo.py` and `requirements.txt` file.

From inside a virtual environment install the requirements:
`pip install -r requirements.txt`

Run the demo:
`python demp.py`
