import urllib.request as request
from contextlib import closing
import zipfile
import os
import glob
from pathlib import Path

shapefiles = {
    "tropical_wx_outlook": "https://www.nhc.noaa.gov/xgtwo/gtwo_shapefiles.zip"
}

def create_data_directory(folder):
    path = Path('.') / folder
    if not path.exists():
        path.mkdir()

def clear_folder_contents(folder):
    '''Clears all contents of folder specified in the argument'''
    old_pwd = os.getcwd()
    os.chdir(folder)
    files = glob.glob('*')
    
    for f in files:
        try:
            os.remove(f)
        except OSError as e:
            print(e)
    
    os.chdir(old_pwd)


def download_zip_file(file_url, folder):
    '''Downloads a zip file and extracts it in a target directory of choice'''
    file = file_url.split('/')[-1]
    request.urlretrieve(file_url, f'{folder}/{file}')
    
def unzip(folder):
    old_pwd = os.getcwd()
    os.chdir(folder)

    for item in os.listdir():
        if item.endswith('.zip'):
            file_name = os.path.abspath(item)
            zip_ref = zipfile.ZipFile(file_name)
            zip_ref.extractall()
            zip_ref.close()
            os.remove(file_name)
            
    os.chdir(old_pwd)


def get_data():
    create_data_directory('data')  
    clear_folder_contents('data')

    for url in shapefiles:
        download_zip_file(shapefiles[url], 'data')
        
    unzip('data')
    

if __name__ == '__main__':
    get_data()