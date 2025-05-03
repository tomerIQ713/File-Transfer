# File Transfer Project

A secure client-server file transfer system built in Python. The project allows encrypted file uploads and downloads between a client and server using RSA encryption for secure transmission.  
This setup demonstrates basic principles of network communication, public-private key cryptography, and secure file handling.

## Installation

- Download the folders.
- Run the install `install_dependencies.bat` file to download the necessary libraries.

**OR run these commands manually:**

```bat
pip install customtkinter
pip install CTkMessagebox
pip install Pillow
pip install cryptography
pip install rsa
```

For this project to work, create these folders:

* Client/downloads/
* Server/data/encryption_keys/
* Server/data/files/

Inside Server/data/encryption_keys, add these files:
* privatekey.pem
* publickey.pem
  
These files are the RSA encryption keys for the server (rsa keys should be generated with 1024 bit length for private key)
