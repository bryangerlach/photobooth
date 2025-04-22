This will open a fullscreen preview from your webcam. Press the "1" key on your keyboard and it will take 3 images. The images will be put together like a photobooth strip. It will then send it to the printer. You will need a photo printer, photo paper, and a way to cut the photo (it will print two photobooth strips on one photo page, so you will need to cut in half). You can edit the footer.jpg file to create your own footer for the photobooth. You can set up an ftp server to upload the pictures.

create a .env file:
```
FTP_HOST=
FTP_USER=
FTP_PASSWORD=
FTP_INDIVIDUAL_PATH=
FTP_STRIPS_PATH=
LOCAL_PRINTS_PATH=prints
LOCAL_PICS_PATH=pics
```

setup venv:
```python -m venv venv```

activate venv:
```.\venv\Scripts\activate```

install requirements:
```pip install -r requirements.txt```

run photobooth:
```python photoboothMain.py```

font used:
https://www.fontspace.com/minecraft-ten-font-f40317