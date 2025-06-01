# Intro

# History stealer


### Challenge description (given to players)
An election candidate's computer has been hacked with malware, the malware's task is to steal browser history files from Chrome & Internet Explorer and then compress them into a zip and upload them to a C2.

The incident response team have captured the executable binary that was used for data stealing. 

Can you find the C2 server & hijjack it?

We need to hack the hackers server. 

Executable_download_link_here


## Moving parts 
This challenge is going to have several moving parts such as:
- A web app & server for the C2
- A MySQL database that holds passwords belonging to admins
- An executable binary with a hardcoded but obfuscated C2 URL


### Web App
The web app is going to have all these pages:
- Uploads
    - Showing all uploads & unzipped files with button to open it using a web browser explorer
- Builder page
    - A page where you can interact with the builder through web
- file_upload endpoint 


### Stealer program
A simple stealer with capabilities to either steal chrome history, explorer history or both and how often to steal them.
There is a one-off attack and then there is once every nth days or 7 days.


### Docker container setup 






