#!/usr/local/bin/python3

from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from netmiko import ConnectHandler
from netmiko.ssh_exception import NetMikoTimeoutException, NetMikoAuthenticationException
from pathlib import Path
import smtplib
import sys
import time

# network_devices contains the devices to connect to
from network_devices import all_devices

# connects to device via ssh, writes config to tftp server, returns error for timeouts, auth failures, write config failures
def ssh_connection(device):
    identifier = "{ip}".format(**device)
    time_now = time.strftime("%Y%m%d-%H%M")
    tftp_server = ("tftp://1.1.1.1/configs/")
    file_path = ("/ftp/tftp/configs/")
    file_name = (identifier + "-" + time_now)
    file_check = Path(file_path + file_name)
    return_data = []
    except_error = ""

    try:
        net_connect = ConnectHandler(**device)
        copy_command = net_connect.send_command_timing("copy running-config " + tftp_server + file_name)
        # the following handles the terminal prompt confirmations
        if True:
            net_connect.send_command_timing("")
            net_connect.send_command_timing("")
    except (NetMikoTimeoutException, NetMikoAuthenticationException) as error:
        except_error = str(error)
    finally:
        if return_data == [] and file_check.is_file():
            return return_data
        elif "timed" in except_error:
             return_data.append("Connection timed-out - failed to backup device " +  identifier)
        elif "Authentication" in except_error:
             return_data.append("Authentication failure - failed to backup device " + identifier)
        else:
            return_data.append("Write failure - failed to backup device " + identifier)

    return return_data

# removes unwanted characters
def text_format(output):
    failed_devices = "\n\n".join(output)

    for chars in failed_devices:
        email_text = failed_devices.replace("['", "").replace("']", "").replace("[]", "")

    return email_text

# sends email if backup fails for any device
def send_email(failed_devices):
    msg = MIMEMultipart()
    msg["From"] = "from@mail.com"
    msg["To"] = "to@mail.com"
    msg["Subject"] = "Network device backup failure"

    text = failed_devices
    part1 = MIMEText(text, "plain")
    msg.attach(part1)

    mailrelay = smtplib.SMTP("smtp.mail.com", 25)
    mailrelay.sendmail("from@mail.com", "to@mail.com", msg.as_string())
    mailrelay.close()

def main():
    output = []

    for device in all_devices:
        output.append("%s" % ssh_connection(device))

    email_text = text_format(output)

    if "failed" in email_text:
        send_email(email_text)

if __name__ == "__main__":
    main()
