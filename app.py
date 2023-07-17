#import
from flask import Flask, render_template
import csv
import matplotlib.pyplot as plt
from datetime import datetime, timedelta
from itertools import islice
from typing import Any
from pydantic import BaseModel, ValidationError
import os
import json
from fastapi import APIRouter, HTTPException
import redis
from fastapi import FastAPI
import sys
import requests
from os import listdir
import pydicom
import numpy as np
from PIL import Image
from pydicom.pixel_data_handlers.util import apply_voi_lut
from flask import Flask, render_template, url_for
import pydicom
from pydicom.errors import InvalidDicomError
from pydicom import dcmread
import matplotlib.pyplot as plt
from flask import jsonify

#app
app = Flask(__name__)






###Create a route ('/') that outputs HTML and shows a grid of images as a table with 4 images per row, include annotations of Patient ID, Date, and Age (in human readable format)

@app.route('/')
def patients():
    dicom_list=[]
    #the path
    path = 'static/dicoms'
    dicom_files = listdir('static/dicoms')
    image_dir = 'static/images'  # The place where the image will be upload
    os.makedirs(image_dir, exist_ok=True)  # If the repertory doesn't exist
    for filename in listdir(path):
        #avoid errors
        try:
            with dcmread(f"{path}/{filename}") as f:
                dicom_list.append(f)
        except InvalidDicomError:
            print(f'{filename} is not DICOM image')

    #4 images per row
    rows = len(dicom_list)+3 // 4
    #information we need, id, name, age, date
    patient_id = []
    PatientName = []
    PatientDate = []
    PatientAge= []
    #Complete the information we need
    for dcm in dicom_list:
        patient_id.append(dcm.PatientID)
        PatientName.append(dcm.PatientName)
        PatientDate.append(dcm.StudyDate)
        PatientAge.append(dcm.PatientAge)
        image_path = os.path.join(image_dir, f'image_{dcm.PatientID}.png')  # Individual image path
        #Show the picture
        plt.imshow(dcm.pixel_array)
        plt.axis('off')
        plt.savefig(image_path)
        plt.close()
    #return with the element we need to show in the html page
    return render_template('patients.html', patient_details=patient_details, image_dir=image_dir, num_images=len(dicom_list), patient_id= patient_id, PatientName=PatientName, PatientDate = PatientDate, PatientAge=PatientAge)


###Create a filterable route that outputs HTML and shows all patients images ('/patient/<patient_id>')

@app.route('/patients/<patient_id>')
def patient_details(patient_id):
    patient_id = patient_id

    filtered_id = []

    #part of the same code than patients()
    dicom_list=[]
    path = 'static/dicoms'
    dicom_files = listdir('static/dicoms')
    image_dir = 'static/images'  # The place where the image will be upload
    os.makedirs(image_dir, exist_ok=True)  # If the repertory doesn't exist
    for filename in listdir(path):
        try:
            with dcmread(f"{path}/{filename}") as f:
                dicom_list.append(f)
        except InvalidDicomError:
            print(f'{filename} is not DICOM image')



    #find all patients images
    for dcm in dicom_list:
        if dcm.PatientID == patient_id:
            filtered_id.append(dcm.PatientID)

    return render_template('patient_details.html', patient_id=patient_id, filtered_id=filtered_id)




### Create a Webservice with a first route ('/api') to serve all DICOM metadata as JSON. At least include Patient ID, Date, Age, Link to image on disk. You do not need to make this data interoperable.

@app.route('/api')
def api():
    dicom_metadata = []

    #to have the image dicom same that in patients()
    dicom_list=[]
    path = 'static/dicoms'
    dicom_files = listdir('static/dicoms')
    image_dir = 'static/images'
    os.makedirs(image_dir, exist_ok=True)
    for filename in listdir(path):
        print(filename)

        try:
            with dcmread(f"{path}/{filename}") as f:
                dicom_list.append(f)
        except InvalidDicomError:
            print(f'{filename} is not DICOM image')
    #

    #Creation of metadata
    #with all the information we need: id, date, age, imagelink
    for dcm in dicom_list:
        metadata = {
            'PatientID': dcm.PatientID,
            'Date': dcm.StudyDate,
            'Age': dcm.PatientAge,
            'ImageLink': url_for('static', filename='images/image_' + dcm.PatientID + '.png', _external=True)
        }
        dicom_metadata.append(metadata)

    return jsonify(dicom_metadata)



### Create a route ('/api/patient/<patient_id>') that filters the images based on a patient's id
@app.route('/api/patient/<patient_id>')
def api_patient(patient_id):
    filtered_metadata = []


    #same code than patient()
    dicom_list=[]
    path = 'static/dicoms'
    dicom_files = listdir('static/dicoms')
    image_dir = 'static/images'
    os.makedirs(image_dir, exist_ok=True)
    for filename in listdir(path):
        print(filename)

        try:
            with dcmread(f"{path}/{filename}") as f:
                dicom_list.append(f)
        except InvalidDicomError:
            print(f'{filename} is not DICOM image')
    #



    #search for the metadata of the patient with the same id
    for dcm in dicom_list:
        if dcm.PatientID == patient_id:
            metadata = {
                'PatientID': dcm.PatientID,
                'Date': dcm.StudyDate,
                'Age': dcm.PatientAge,
                'ImageLink': url_for('static', filename='images/image_' + dcm.PatientID + '.png', _external=True)
            }
            filtered_metadata.append(metadata)

    return jsonify(filtered_metadata)

### Which image names do not match their metadata?
@app.route('/errors')
def find_mismatched_cues():
    # Load DICOM images
    dicom_list = []
    path = 'static/dicoms'
    for filename in listdir(path):
        try:
            with dcmread(f"{path}/{filename}") as f:
                dicom_list.append(f)
        except InvalidDicomError:
            print(f'{filename} is not a DICOM image')

    # Extract cues from image names
    image_cues = [image_name.split('_')[1].split('.')[0] for image_name in os.listdir('static/images')]

    # Extract cues from metadata
    metadata_cues = [dcm.PatientID for dcm in dicom_list]

    # Find cues that exist in image names but not in metadata
    missing_metadata_cues = list(set(image_cues) - set(metadata_cues))

    # Find cues that exist in metadata but not in image names
    missing_image_cues = list(set(metadata_cues) - set(image_cues))

    # Return the results as a dictionary
    results = {
        'image_cues': image_cues,
        'metadata_cues': metadata_cues,
        'missing_metadata_cues': missing_metadata_cues,
        'missing_image_cues': missing_image_cues
    }

    return jsonify(results)

###To show : Which image names do not match their metadata?
@app.route('/errors2')
def find_mismatched_cues2():
    # Load DICOM images
    dicom_list = []
    path = 'static/dicoms'
    for filename in listdir(path):
        try:
            with dcmread(f"{path}/{filename}") as f:
                dicom_list.append(f)
        except InvalidDicomError:
            print(f'{filename} is not a DICOM image')

    # Extract cues from image names
    image_cues = [image_name.split('_')[1].split('.')[0] for image_name in os.listdir('static/images')]

    # Extract cues from metadata
    metadata_cues = [dcm.PatientID for dcm in dicom_list]

    # Find cues that exist in image names but not in metadata
    missing_metadata_cues = list(set(image_cues) - set(metadata_cues))

    # Find cues that exist in metadata but not in image names
    missing_image_cues = list(set(metadata_cues) - set(image_cues))

    # Identify image names that do not match their metadata
    mismatched_image_names = [
        image_name for image_name in os.listdir('static/images')
        if image_name.split('_')[1].split('.')[0] not in metadata_cues
    ]

    # Prepare the response with explanations and mismatched image names
    response = {
        'explanation': 'Cues found in both image names and metadata:',
        'cues': {
            'Patient ID': 'Unique identifier for each patient.',
            'Image Dates': 'Dates associated with the images.',
            'Study/Series Descriptions': 'Textual information about the study or series.'
        },
        'results': {
            'image_cues': image_cues,
            'metadata_cues': metadata_cues,
            'missing_metadata_cues': missing_metadata_cues,
            'missing_image_cues': missing_image_cues,
            'mismatched_image_names': mismatched_image_names
        }
    }

    return render_template('errors.html', results=response['results'])

###Please provide code to avoid this problem in the future.
#This function could be call to check if the image names match with their metadata
def validate_image_metadata():

    #load the dicom images
    dicom_list=[]
    path = 'static/dicoms'
    dicom_files = listdir('static/dicoms')
    image_dir = 'static/images'
    os.makedirs(image_dir, exist_ok=True)
    for filename in listdir(path):
        print(filename)

        try:
            with dcmread(f"{path}/{filename}") as f:
                dicom_list.append(f)
        except InvalidDicomError:
            print(f'{filename} is not DICOM image')

    # Create a dictionary to store the image metadata using the image cues as keys
    metadata_dict = {dcm.PatientID: dcm for dcm in dicom_list}

    # List to store mismatched image names
    mismatched_image_names = []

    # Iterate over the image files in the directory
    for image_name in os.listdir(image_dir):
        # Extract the image cue from the image name
        image_cue = image_name.split('_')[1].split('.')[0]

        # Check if the image cue exists in the metadata dictionary
        if image_cue not in metadata_dict:
            mismatched_image_names.append(image_name)

    return mismatched_image_names


###Can you fix the image names, which of them were wrong and what needed to be changed?
def fix_image_names():

    #load the dicom images
    dicom_list=[]
    path = 'static/dicoms'
    dicom_files = listdir('static/dicoms')
    image_dir = 'static/images'
    os.makedirs(image_dir, exist_ok=True)
    for filename in listdir(path):
        print(filename)

        try:
            with dcmread(f"{path}/{filename}") as f:
                dicom_list.append(f)
        except InvalidDicomError:
            print(f'{filename} is not DICOM image')


    metadata_cues = [dcm.PatientID for dcm in dicom_list]
    image_names = os.listdir(image_dir)

    for image_name in image_names:
        image_cue = image_name.split('_')[1].split('.')[0]
        if image_cue not in metadata_cues:
            for dcm in dicom_list:
                if dcm.PatientID not in metadata_cues and dcm.PatientID != image_cue:
                    # Find a DICOM object with a matching Patient ID
                    new_image_name = image_name.replace(image_cue, dcm.PatientID)
                    # Update the image name with the correct Patient ID
                    os.rename(os.path.join(image_dir, image_name), os.path.join(image_dir, new_image_name))
                    # Rename the image file accordingly
                    metadata_cues.append(dcm.PatientID)
                    print(f"Image name '{image_name}' has been fixed to '{new_image_name}'.")


if __name__ == '__main__':
    app.run()







