import math
import os
import requests
import urllib3


class Device:

    def __init__(self, ip, uname, pwd, timeout=5):
        self.ip = ip
        self.uname = uname
        self.pwd = pwd
        self.timeout = timeout
        self.online = False
        self.uptime = math.inf
        self.uptime_old = -math.inf
        self.attempts = 0
        self.model = "unknown"
        self.name = "unknown"
        self.fw_version = "unknown"
        self.build_type = "unknown"

    def login(self):
        urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
        self.session = requests.Session()
        command = self.session.post(
            (
                "https://"
                + self.ip
                + "/ajax?sid="
            ),
            verify=False,
            json=[
                {
                    "command": "system.login",
                    "user": self.uname,
                    "password": self.pwd
                }
            ],
            timeout=self.timeout
        )
        print(command.text)

        self.sid = command.json()[0]["sid"]
        self.online = True
        return True

    def logout(self):
        try:
            command = self.session.post(
                (
                    "https://"
                    + self.ip
                    + "/ajax?sid="
                ),
                verify=False,
                json=[
                    {
                        "command": "system.logout",
                        "user": self.uname,
                        "password": self.pwd
                    }
                ],
                timeout=self.timeout
            )

            self.online = True
            self.session.close()
            return True
        except:
            self.online = False

    def status(self):
        try:
            command = self.session.get(
                (
                    "https://"
                    + self.ip
                    + "/api/system/status?sid="
                    + self.sid
                ),
                timeout=self.timeout,
                verify=False
            )

            self.online = True
            self.uptime = int(command.json()["result"]["upTime"])
            return True
        except:
            self.online = False
            self.uptime = math.inf
            return False

    def info(self):
        try:
            command = self.session.get(
                (
                    "https://"
                    + self.ip
                    + "/api/system/info?sid="
                    + self.sid
                ),
                timeout=self.timeout,
                verify=False
            )
            self.online = True
            self.model = command.json()["result"]["variant"]
            self.name = command.json()["result"]["deviceName"]
            self.fw_version = command.json()["result"]["swVersion"]
            self.build_type = command.json()["result"]["buildType"]
        except:
            self.online = False
            return False

    def get_param(self, param):
        try:
            payload = [
                {
                    "command": "db.get",
                    "path": param
                }
            ]
            command = self.session.post(
                (
                    "https://"
                    + self.ip
                    + "/ajax?sid="
                    + self.sid
                ),
                timeout=self.timeout,
                verify=False,
                json=payload
            )

            return command.json()[0]["value"]

        except:
            return False

    def call_dial(self, destination):
        command = self.session.get(
            (
                "https://"
                + self.ip
                + "/api/call/dial?number="
                + destination
                + "&sid="
                + self.sid
            ),
            timeout=self.timeout,
            verify=False
        )

    def call_pickup(self):
        command = self.session.get(
            (
                "https://"
                + self.ip
                + "/api/call/status?sid="
                + self.sid
            ),
            timeout=self.timeout,
            verify=False
        )

        call_session = command.json()["result"]["sessions"][0]["session"]

        command = self.session.get(
            (
                "https://"
                + self.ip
                + "/api/call/answer?session="
                + str(call_session)
                + "&sid="
                + self.sid
            ),
            timeout=self.timeout,
            verify=False
        )
        return True

    def restart(self):
        try:
            command = self.session.get(
                (
                    "https://"
                    + self.ip
                    + "/api/system/restart?sid="
                    + self.sid
                ),
                timeout=self.timeout,
                verify=False
            )

            return True
        except:
            return False

    def upload_image(self, image):
        try:
            command = self.session.put(
                (
                    "http://"
                    + self.ip
                    + "/api/display/image?sid="
                    + self.sid
                ),
                timeout=0.1,
                verify=False,
                files={"blob-image": ("blob-image", image, "image/jpeg")}
            )
            return command.text
        except:
            pass

    def delete_image(self):
        try:
            command = self.session.delete(
                (
                    "http://"
                    + self.ip
                    + "/api/display/image?sid="
                    + self.sid
                ),
                timeout=0.1,
                verify=False
            )
            return command.text
        except:
            pass

    def delete_image(self):
        command = self.session.delete(
            (
                "https://"
                + self.ip
                + "/api/display/image?sid="
                + self.sid
            ),
            timeout=self.timeout,
            verify=False
        )

        return command.text

    def subscribe_log(self, filter, duration):
        command = self.session.get(
            (
                "http://"
                + self.ip
                + "/api/log/subscribe?filter="
                + filter
                + "&duration="
                + duration
                + "&sid="
                + self.sid
            ),
            timeout=self.timeout,
            verify=False
        )

        return command.json()["result"]["id"]

    def pull_log(self, id, to):
        rto = to + 10
        if to == 0:
            rto = 0.1
        try:
            command = self.session.get(
                (
                    "http://"
                    + self.ip
                    + "/api/log/pull?id="
                    + id
                    + "&timeout="
                    + str(to) + "&sid="
                    + self.sid
                ),
                timeout=rto,
                verify=False
            )

            return command.json()["result"]["events"]
        except:
            return []

    def upgrade_firmware(self, file):
        command = self.session.put(
            (
                "http://"
                + self.ip
                + "/api/firmware?sid="
                + self.sid
            ),
            timeout=120,
            verify=False,
            files={"blob-fw": file}
        )

        print(command.text)
        return command.json()

    def confirm_firmware(self, fwid):
        payload = [{
            "command": "system.applynewfirmware",
            "fileId": fwid
        }]
        command = self.session.post(
            (
                "https://"
                + self.ip
                + "/ajax?sid="
                + self.sid
            ),
            json=payload,
            timeout=self.timeout,
            verify=False
        )

        return (command, command.text)

    def play_sound(self, sound_id):
        command = self.session.get(
            (
                "http://"
                + self.ip
                + "/api/automation/trigger?triggerId="
                + sound_id
                + "&sid="
                + self.sid
            ),
            timeout=120,
            verify=False
        )

        return(command, command.text)

    def get_snapshot(self, width, height, quality, source):
        command = self.session.get(
            (
                "http://"
                + self.ip
                + "/api/camera/snapshot?width="
                + str(width)
                + "&height="
                + str(height)
                + "&quality="
                + str(quality)
                + "&source="
                + str(source)
                + "&sid="
                + self.sid
            ),
            timeout=120,
            verify=False
        )

        return command.content

    def enter_card(self, card_bytes):
        command = self.session.get(
            (
                "http://"
                + self.ip
                + "/api/sim/cardswipe?cardType=EM41XX&bytes="
                + str(card_bytes)
                + "&bitLength=32&device=0"
                + "&sid="
                + self.sid
            ),
            timeout=self.timeout,
            verify=False
        )

        return command.text

    def activate_bluetooth(self):
        command = self.session.get(
            (
                "http://"
                + self.ip
                + "/api/sim/touch?device=0"
                + "&sid="
                + self.sid
            ),
            timeout=self.timeout,
            verify=False
        )

        return command.text

    def get_last_restart(self):
        try:
            payload = [
                {
                    "command": "db.get",
                    "path": "Debug.Restarts.Count"
                }
            ]

            command = self.session.post(
                (
                    "https://"
                    + self.ip
                    + "/ajax?sid="
                    + self.sid
                ),
                timeout=self.timeout,
                verify=False,
                json=payload
            )

            output = "NO_RESTART_RECORD"

            if int(command.json()[0]["value"]) > 0:

                payload = [
                    {
                        "command": "db.get",
                        "path": "Debug.Restarts.Row[0].Details"
                    },
                    {
                        "command": "db.get",
                        "path": "Debug.Restarts.Row[0].LocalTime"
                    },
                    {
                        "command": "db.get",
                        "path": "Debug.Restarts.Row[0].Reason"
                    },
                    {
                        "command": "db.get",
                        "path": "Debug.Restarts.Row[0].UpTime"
                    },
                    {
                        "command": "db.get",
                        "path": "Debug.Restarts.Row[0].Version"
                    }
                ]

                command = self.session.post(
                    (
                        "https://"
                        + self.ip
                        + "/ajax?sid="
                        + self.sid
                    ),
                    timeout=self.timeout,
                    verify=False,
                    json=payload
                )

                output = ""
                for e in command.json():
                    output += e["value"] + "  "
            return output

        except:
            return "READING_FAILED"
