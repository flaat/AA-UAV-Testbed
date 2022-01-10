# Here the NTP server is 169.254.1.1, to add a new node it is sufficient to copy-paste a row and change the ip "pi@my_ip"

sshpass -p 'raspberry' ssh -o StrictHostKeyChecking=no pi@169.254.1.7 "sudo service ntp stop; sudo ntpdate 169.254.1.1"
sshpass -p 'raspberry' ssh -o StrictHostKeyChecking=no pi@169.254.1.5 "sudo service ntp stop; sudo ntpdate 169.254.1.1"
sshpass -p 'raspberry' ssh -o StrictHostKeyChecking=no pi@169.254.1.3 "sudo service ntp stop; sudo ntpdate 169.254.1.1"
sshpass -p 'raspberry' ssh -o StrictHostKeyChecking=no pi@169.254.1.2 "sudo service ntp stop; sudo ntpdate 169.254.1.1"
