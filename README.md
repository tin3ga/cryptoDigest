# cryptoDigest
send cryptocurrency price information to email

This repository utilizes GitHub Actions to schedule and execute a Python script as a cron job. The script makes a weekly API call, sends an email, records the event in an "event.log" file, and subsequently automates the process of pushing these changes back to the repository.
