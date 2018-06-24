# Uploadfile to google drive with oauth2 #
Without google's library dependencies

There exists a progress and speed indicator during upload.  

# Requirement #
Python 3.4 or above  
Google Account with api, oauth2 enabled  
Linux, windows or Mac  


# Google API #
https://console.developers.google.com/apis/credentials  
Create an API project and add a product name on the OAuth consent screen under Credentials settings page.  
Create credentials by OAuth client ID and click download JSON afterwards  
Enable Google drive API from the console.  
This program demands https://www.googleapis.com/auth/drive.file (Read/Write files that created by this program only) authorization only.  


# Installation #
make the uploadfile.py executable  
```
# Linux or mac
chmod 700 upload.py
```
Make a symbolic link to /usr/local/bin/  
```
ln -s <folder>/uploadfile.py /usr/local/bin/uploadfile
```
For windows user  
Add the checkout path to path env variable

Put your client_secret.json which can be downloaded from google api console  
to ~/.google-credentials/uploadfile/client_secret.json  
During the first time you will be asked for authorization, finish it one time only.  
The account you authorize is the target google drive that you are allowing the file to be uploaded to.  
A folder named uploads will be created on the google drive of that's account.  

# Usage #
```
uploadfile film.mp4
```

### Show stack trace on error ###
```
uploadfile film.mp4 -v
```

### use manual flow ###
suitable for ssh
```
UPLOAD_AUTH_USING=manual uploadfile film.mp4
```


# Env variable #
UPLOAD_CHUNKSIZE : in KB, the size for each chunk. Use a large value to speed up or a low value in a slower network to prevent failure, 4096 by default.  
UPLOAD_AUTH_USING : set it to manual if you are not running from your local computer, such as server under ssh. You are required to paste the authorization code manually. 
Or skip this to use local server mode by default. The port 9004 will be used to listen the response from google. However, there is no need to forward 9004 port outside.
UPLOAD_LOCAL_SERVER_PORT : 9004 by default  

# Revoke access #
https://myaccount.google.com/u/6/permissions  
It may take several seconds to activate.  