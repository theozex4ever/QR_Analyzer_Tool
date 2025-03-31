# Data Matrix Analyzer

A PyQt5-based application for analyzing and decoding Data Matrix codes in images using OpenCV and pylibdmtx. Supports both manual analysis and automated batch processing.

## Features

### Manual Analysis
- Load images from a folder
- Interactive area selection
- Single Data Matrix detection and decoding
- Real-time visualization

### Automated Processing
- Batch processing of multiple images
- Automatic detection of multiple Data Matrix codes per image
- Scaling support for large images (25%-100%)
- Individual extraction of each detected matrix
- Automatic file naming based on decoded content
- Progress tracking and logging
- Output organization by source image

## Image Processing Features
- OpenCV-based image preprocessing
- Automatic grayscale conversion
- Adaptive thresholding for better code detection
- Noise reduction using non-local means denoising
- Support for PNG, JPG, JPEG, and BMP image formats

## Dependencies

```bash
pip install opencv-python pylibdmtx PyQt5
```

## Usage

### Manual Analysis
1. Launch the application and select the "Manual Analysis" tab
2. Click "Load Folder" to select a directory containing images
3. Select an image from the list to display it
4. Draw a selection rectangle around the Data Matrix code
5. Click "Detect Data Matrix" to decode the selected area

### Automated Processing
1. Switch to the "Automated Processing" tab
2. Click "Load Folder" to select images for processing
3. Click "Select Output Directory" to choose where to save results
4. Adjust the scale factor if needed (for large images)
5. Click "Process Images" to start batch processing
6. Monitor progress and results in the log viewer

## Output Structure

For automated processing, the output is organized as follows:
```
output_directory/
  ├── image1_name/
  │   ├── matrix1_content_timestamp.png
  │   └── matrix2_content_timestamp.png
  └── image2_name/
      ├── matrix1_content_timestamp.png
      └── matrix2_content_timestamp.png
```

## Notes

- The application uses OpenCV for all image operations, providing better image processing capabilities
- Uses pylibdmtx for reliable Data Matrix code detection
- GUI built with PyQt5 for a native look and feel
- Multi-threaded processing for responsive UI during batch operations
