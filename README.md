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
Compile with:
```
mcs -optimize- Program.cs
```


### Docker container setup 






