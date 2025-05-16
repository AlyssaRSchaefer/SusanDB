# SusanDB
Spring 2025 Capstone Project

## Detailed User Documentation & Initialization
- https://mailmissouri-my.sharepoint.com/:w:/g/personal/ajch9f_umsystem_edu/Ee93MYDwI-VGjJh-8eS6ZWUBbvo9pCm_IHOkbm5Nqc6gwg?e=5KPU31

## 1. Initialize your environment
- Run "conda env create -f environment.yml"
- Run "pip install -r requirements.txt"

## 2. Create your .env file
- Contact us for ours

## 3. Test
- To run unit tests, run "pytest"

## 4. Run
- Open a terminal and run "python app.py"

### To create an executable, run the following command and add the .env to the same folder as the .exe
- "pyinstaller --noconfirm --onefile --windowed --icon=app_icon.ico --add-data "templates;templates" --add-data "static;static" app.py"