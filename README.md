# Intro

# History stealer


### Challenge description (given to players)
An election candidate's computer has been hacked with malware, the malware's task is to steal browser history files from Chrome & Internet Explorer and then compress them into a zip and upload them to a C2.

The incident response team have captured the executable binary that was used for data stealing. 

Can you find the C2 server & hijjack it?

The executable binary found on the cadidate's computer is here:
Executable_download_link_here


## Moving parts 
This challenge is going to have several moving parts such as:
- A web app & server for the C2
- An executable binary with a hardcoded but obfuscated C2 URL


### Web App
The web app is going to have all these pages:
- Uploads
    - Showing all uploads & unzipped files with button to open it using a web browser explorer
- file_upload endpoint 


### Stealer program
This is not a real stealer but just a program with an obfuscated C2 value. 
Install dependencies:
```
sudo apt install mono-complete python3-pip
```


Compile with:
```
mcs -sdk:4.5 -target:exe -out:./steal.exe -platform:x64 -r:/usr/lib/mono/4.5/System.Net.Http.dll -r:/usr/lib/mono/4.5/System.IO.Compression.dll -r:/usr/lib/mono/4.5/System.IO.Compression.FileSystem.dll -langversion:7.1 Program.cs
```

Grab C2 URL with:
```
strings -e l Program.exe
```


### Docker container setup 



# Todo
- [ ] Create docker container to run the C2 
- [ ] Give root permissions to your user to run c2 as root 
- [ ] Setup crontab and test it 
- [ ] Test upload against container
- [ ] Make the unzipping functionality vulnerable
- [ ] Test zip slip vulnerability against crontab
- [ ] Get a shell on the system through the web app 



