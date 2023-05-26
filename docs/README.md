# Setting Up:

### Installation
#### Windows and Linux: 
The short version of things you will need to install:
- A command line interface (such as Windows Terminal, which can be installed from the Microsoft Store)
- WSL & Ubuntu
- Python (+ packages)
    - pandas
    - xlrd
- Internet Archive's command line tool

For Windows, you'll have to install Ubuntu or some other unix-like terminal to interact with the IA's command line tool. You can do this in the default command line interface with `wsl --install`. Reboot the machine and open it in your preferred command line interface. You may need to enable virtualization in order for Ubuntu to properly install-- the steps for this will depend on your machine.

Now that Ubuntu is set up, install the **packages** needed to run the program. First, run `sudo apt update` to update the existing packages. Then run `sudo apt install pythonpy python3-pip internetarchive` this includes Python (which is required to run the program), pip (which is used to install other dependencies), and the Internet Archive command line tool itself. Then run `pip3 install pandas xlrd`. `Pandas` and `xlrd` are used for reading the metadata Excel spreadsheets.

#### Mac:
Since Mac already has a unix-like terminal, you only need to install:
- pip and Python 
- pandas (Python package)
- xlrd (Python package)
- Internet Archive's command line tool

You might have Python3 already installed on your machine. Take note that pip3 goes with Python3, and pip goes with older versions of Python, make sure to be consistent with using them together when troubleshooting errors in the installation. ```which pip``` or ```which python``` could be helpful commands at determining what is recognized by your system. If, according to these commands, you have python3 + pip3 installed, and pip and python are not, and you are struggling to install them, you could make pip point to pip3. In these cases, a helpful command for installing pandas and internet archive command line tool would be ```python3 -m pip install internetarchive, pandas```. 

### IA Configuration
Next, set up the **IA credentials** with `ia configure`. See the [IA Quickstart guide](https://archive.org/services/docs/api/internetarchive/quickstart.html) for more information.

Once you have this, you should be good to start! 

## Mounting Google Drive
Since the Dime Novel files are so large in size, dowloading them locally to your computer would be very time-consuming and memory inefficient. To avoid this, you will need to mount the Google Drive on your file system, which basically provides access to all of the files in your drive through the terminal as though they are in your local directory. If you don't have rclone installed in your system already (you can check through ```rclone --version``` command), follow the [installation instructions] (https://rclone.org/install/) for your respective operating system. 

You will then need to configure rclone through ```rclone config```. Make sure to go through more detailed instructions on configuration in [rclone docs] (https://rclone.org/docs/). There are multiple steps to it, and it takes quite a bit of time to understand!

After your rclone is set up, you can check to see if it works by running ```rclone lsd remote:[GOOGLE_DRIVE_FOLDER_PATH]``` which should output the contents of the Google Drive folder you are trying to work with. 

Finally to mount the GDrive in the Batch folder you're trying to upload to the Internet Archive, run ```rclone mount remote:[GOOGLE_DRIVE_FOLDER_PATH] [LOCAL_FILESYSTEM_PATH] --vv --allow-other```. ```-vv``` flag is helpful for debugging and ```--allow-other``` is necessary if your DimeNovels folder is the root. 

# Uploading `texts` items

For items with media type `texts`, the archive displays a pager on the item's webpage that allows the visitor to read through the text.
In order for this to work, the system has to be able to tell what files are the page scans, and which corresponds to which page.

The program combines the scan image files into a ZIP file to be uploaded. If the IA identifier for an item to be uploaded is `xyz`, then it's acceptable for the ZIP file to contain a single folder called `xyz` containing image files whose names are `xyz` followed by a number specifying the order of pages. For example, the first scan could be `xyz-01.jpg`, and the second `xyz-02.jpg`.

The IA is a little fussy about their page labeling: labels should be double-checked. If there are **multiple files that have the number `00`**, such as `xyz-00` or `xyz-00a`, the IA will put `xyz-00` before `xyz-00a`. Make sure not to use `xyz-00 [cover]`, it might not work for the ordering that you would like. Your `xyz-00` should always be your cover. 

Essentially, if there are **multiple `xyz-00`s**, rename them to `xyz-00a` `xyz-00b` `xyz-00c`, etc. 

It also has some trouble when accidentally trying to include metadata keys with leading whitespace. It's probably best to strip whitespace from keys to be safe (the program does this).

# Testing

You can use the Internet Archive `test_collection` collection to upload temporary (test) items.
Items uploaded to the test collection only stay around for about a month.
The collection to upload to is specified using the `collection` metadata key.

You can also add `test` to the end of the command line call to make it upload one test item.

# The program, and running it

Make sure your files are downloaded, and double check the naming conventions. The **folder of scans** and the **Excel spreadsheet** should be in the path specified in the `base_dir` variable. You should also specify it in line 167- `os.chdir("path")`.

I created two `.sh` files, `upload.sh` and `testupload.sh`, in my `home` directory to make the uploading process a little faster.

The folder I have `process.py` in is `/mnt/c/Users/'Tech Assistant'/documents/dimenovels/code/`, so mine look like this:

```bash
# upload.sh
python3 /mnt/c/Users/'Tech Assistant'/documents/dimenovels/code/process.py
```

```bash
# testupload.sh
python3 /mnt/c/Users/'Tech Assistant'/documents/dimenovels/code/process.py test
```

Then run `upload.sh` or `testupload.sh`, as appropriate.
If you get the "Permission denied" error, run `chmod +x` followed by the name of your .sh. 


## Troubleshooting

If you encounter the error `AttributeError: 'ValueError' object has no attribute 'request'`, make sure the Excel spreadsheet contains only cells filled with data. If there are borders around cells that don't have metadata inside, the program will attempt to upload those empty cells on the Internet Archive.

## Otherwise
If the storage is mounted a different way (e.g. using the system file browser), you should change `base_dir` to that location.

# Resources

- [Documentation](https://archive.org/services/docs/api/internetarchive/index.html) for the Internet Archive Python library
- [Documentation](https://archive.org/services/docs/api/metadata-schema/index.html) for IA item metadata
