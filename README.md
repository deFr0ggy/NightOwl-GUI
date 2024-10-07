# NightOwl-GUI

NightOwl-GUI is a Python Flask Application, an upgrade of my NightOwl-CLI which i released 2-3 years ago (https://github.com/deFr0ggy/NightOwl) and have been using in personal capacity. The github one is not that updated as i made a lot of changes to it. 

However, i though to give it a little upgrade. So that, we can work with the email files without the worries of clicking or downloading or executing anything from the email itself. 

This is pretty much a boiler plate for the time being, there is a lot to come to the project and will happen over time. I will be keeping this as an open source project with the sole aim to support he community. 

# Usage 

The usage is pretty simple, all you need is to supply a `.EML` or `.MSG` file. The data will be taken out and displayed to you automatically. 

1. From field
2. To field
3. Email Subject
4. Date
5. Email Body
6. IP Addresses (From the body)
7. Emails Addresses (From the body)
8. URLs (From the body)
9. Attachments (Name is displayed)
10. Attachments stored in Passowrd Protected Zip File. 'Password: infected'
11. MD5, SHA512, SHA256 Calculation. 
12. AbuseIPDB Integration for validating IP Addresses.

The attachments will be stored in the `/Uploads` folder as well as the uploaded email files. 

# API KEYS

The API keys are required to be in the environment variables. For now only one is required and you should set it on your local machine. 

```
ABUSEIPDB_API_KEY
```

# In Mission

![](/Snaps/1.png)

![](/Snaps/2.png)

# Updated Mission

![](/Snaps/3.png)

# Upcoming

- [ ] Threat Intelligence (IP/Domains/Emails)
- [X] Password Protected Attachments 
- [X] Hash Calculation of Attachments. 
- [ ] AbuseIPDB data comes in JSON, this has to be parsed and displayed, no redirect. Will take a look into this later.

# Bugs

- [ ] Remove the double message from the attachments section.
- [ ] AbuseIPDB does not works with URLs, so have to integrate. For now, its the same function so thats buggy. 

# Contribute

If you have more ideas or want to make a copy of this, please feel free to do it. You can always create a pull request and share your ideas on the same. 

# Get In Touch

You can reach out to me on the below. 

- Twitter - https://x.com/deFr0ggy
- LinkedIn - https://linkedin.com/in/kamransaifullah786