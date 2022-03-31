from string import digits
import tkinter
from tkinter import messagebox
from tkinter import filedialog
import constants_final
import json
import pysftp
import csv
import os
import webbrowser

# Binary Search Method. Faster Look-up - O(log(n))
# Source: https://realpython.com/binary-search-python/ 
def find_index(elements, value):
    left, right = 0, len(elements) - 1
    
    while left <= right:
        middle = (left + right) // 2

        if elements[middle] == value:
            return middle

        if elements[middle] < value:
            left = middle + 1
        elif elements[middle] > value:
            right = middle - 1

# Json Decode Method.
def GetJSON(path):
    try:
        f = open(path, encoding='UTF8')
        fstr = f.read()[1:]
        f.close()
        try:
            data = json.loads(fstr)
        except json.decoder.JSONDecodeError:
            messagebox.showerror("File not found", "Please file with the .json extension")
    except FileNotFoundError:
        messagebox.showerror("File not found", "Check whether the 'Choose Json File' field points to the actual file")
    return data

# Returns the list of all funders from Decoded Json.
# data - decoded .json file
def getAndFilterFunders(classif, g_det):
    inter_res = []
    for row in g_det:
        if row['charity_registration_status'] == 'Registered':
            if isinstance(row['latest_expenditure'], float) :
                if row['latest_expenditure'] >= 100000:
                    inter_res.append(row['registered_charity_number'])
            

    res = []
    res.append(0) # to prevent bug with binary search, when resolve first element in the array.
    for row in classif:
        if row['classification_type'] == 'How' and row['classification_code'] == 302 and find_index(inter_res, row['registered_charity_number']):
            res.append(row['registered_charity_number'])
    return res

# Returns a dictionary where 
### key = id of the funder, e.g. 200002
### value = concatinated string of its "What" classification, eg. value = "102;105;112" 
# data - decoded .json data.
# funders - list of funders id.
def getClassifications(data, funders):
    res = {}
    for row in data:
        if row['classification_type'] == 'What':
            if find_index(funders, row['registered_charity_number']):
                if not row['registered_charity_number'] in res:
                    res[row['registered_charity_number']] = str(row['classification_code'])
                else:
                    res[row['registered_charity_number']] += ";" + str(row['classification_code'])
    return res

# Encapsulates the first stage of the script, which is resposible for extracting the classification of all the funders into the dictionary data-structure
# path - relative path to the .json file to be processed.
def getInputToDB(path_class, path_det):
    classif_data = GetJSON(path_class)
    details_data = GetJSON(path_det)
    funders = getAndFilterFunders(classif_data, details_data)
    inputToDb = getClassifications(classif_data, funders)
    return inputToDb

# Method that writes a dictionary to the 'SQL.csv' file
# inputToCSV - dictionary data structure.
def writeFileCSV(inputToCSV):
    with open(constants_final.FILENAME_CSV+constants_final.EXTENSION_CSV, 'w', newline='') as csvfile:
        spamWrite = csv.writer(csvfile)
        for key in inputToCSV:
            spamWrite.writerow([key, inputToCSV[key]])

# Method that sends a CSV file to the IONOS server via SFTP protocol
# FTPfolders - array of folders located on the server, that represent an absolute path of the directory, where .CSV file need to be sent to.
# file - .csv file to write (Relative path)
def FTPto(folders, file):
    cnopts = pysftp.CnOpts()
    cnopts.hostkeys = None
    try:
        sftp = pysftp.Connection(constants_final.FTP_HOST, username=constants_final.FTP_USERNAME, password=constants_final.FTP_PASSWORD, private_key=".ppk", cnopts=cnopts)
    except pysftp.ConnectionException:
        messagebox.showerror("Connection Error", "Check host input field")
    except pysftp.AuthenticationException:
        messagebox.showerror("Authentification Error", "Check username and password input fields")

    for folder in folders:   
        sftp.cwd(folder)
    sftp.put(file)

# Encapsulation method that contains all 3 stages of the script:
# 1. Decoding and processing JSON file into Dictionary
# 2. Writing the information to the SQL.csv file
# 3. FTP .CSV file to the IONOS hosting server
# jsonFile - .json file to decode (Relative path)
# csvFILE - .csv file to write (Relative path)
# FTPfolders - array of folders located on the server, that represent an absolute path of the directory, where .CSV file need to be sent to.
def encapsulation(jsonFile_class, jsonFile_det, csvFILE, FTPfolders, destURL):
    writeFileCSV(getInputToDB(jsonFile_class, jsonFile_det))
    FTPto(FTPfolders, csvFILE)    
    
    # Delete local SQL.csv file if exists
    if os.path.exists(constants_final.FILENAME_CSV+constants_final.EXTENSION_CSV):
        os.remove(constants_final.FILENAME_CSV+constants_final.EXTENSION_CSV)
    
    # Feedback to the user
    messagebox.showinfo("Done", "You can now visit http://bcausam.co.uk/charities-tables-update/ and wait until page is loaded to update your database ")
    webbrowser.open(destURL)

# classPath = 'C:/Users/glebs/Downloads/publicextract.charity/publicextract.charity.json'
# print(GetJSON(classPath)[0])


# encapsulation(constants_final.FILENAME_JSON+constants_final.EXTENSION_JSON,
#               constants_final.FILENAME_CSV+constants_final.EXTENSION_CSV,
#               constants_final.FTP_PATH)


# Callback function to resolve path from filedialog and insert it into appropriate entry filed.
def handle_class_path():
    fd = filedialog.askopenfilename()
    classPath.delete(0,"end")
    classPath.insert(0,fd)

# Callback function to resolve path from filedialog and insert it into appropriate entry filed.
def handle_det_path():
    fd = filedialog.askopenfilename()
    detPath.delete(0,"end")
    detPath.insert(0,fd)

# Handle main functionality of the program
def handle_process():
    # Get entries from fields.
    constants_final.FTP_HOST = host.get()
    constants_final.FTP_USERNAME = username.get()
    constants_final.FTP_PASSWORD = password.get()
    constants_final.FTP_PATH = server_path.get().split(sep=",")
    constants_final.FILENAME_CLASS_JSON = classPath.get()
    constants_final.FILENAME_DET_JSON = detPath.get()
    constants_final.WP_URL = dest_url.get()
    encapsulation(
              constants_final.FILENAME_CLASS_JSON,
              constants_final.FILENAME_DET_JSON,
              constants_final.FILENAME_CSV+constants_final.EXTENSION_CSV,
              constants_final.FTP_PATH,
              constants_final.WP_URL
              )

# Create windows
window = tkinter.Tk()

# Labels and their arrangement in the grid
tkinter.Label(window, text="host").grid(row=0)
tkinter.Label(window, text="username").grid(row=1)
tkinter.Label(window, text="password").grid(row=2)
tkinter.Label(window, text="classification json file").grid(row=3)
tkinter.Label(window, text="general details json file").grid(row=4)
tkinter.Label(window, text="path").grid(row=5)
tkinter.Label(window, text="Update script destination").grid(row=6)

# Input fields
host = tkinter.Entry(window)
username = tkinter.Entry(window)
password = tkinter.Entry(window)
classPath = tkinter.Entry(window)
detPath = tkinter.Entry(window)
server_path = tkinter.Entry(window)
dest_url = tkinter.Entry(window)

# Arrange Input fields in the grid.
host.grid(row=0, column=1)
username.grid(row=1, column=1)
password.grid(row=2, column=1)
classPath.grid(row=3, column=1)
detPath.grid(row=4, column=1)
server_path.grid(row=5, column=1)
dest_url.grid(row=6, column=1)

# Initial values
host.insert(0,constants_final.FTP_HOST)
username.insert(0,constants_final.FTP_USERNAME)
server_path.insert(0,constants_final.GUI_FTP_PATH)
dest_url.insert(0,constants_final.WP_URL)

# File Dialog trigger
button1 = tkinter.Button(master=window, text="...", command=lambda:handle_class_path())
button1.grid(row=3, column=2, sticky="nsew" )

# File Dialog trigger
button1 = tkinter.Button(master=window, text="...", command=lambda:handle_det_path())
button1.grid(row=4, column=2, sticky="nsew" )

# Processing .json and other main functionality trigger
button2 = tkinter.Button(master=window, text="Process File", command=lambda:handle_process())
button2.grid(row=7, column=0, sticky="nsew" )

# GUI Application loop
window.mainloop()