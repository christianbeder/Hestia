# Copyright 2023 Munster Technological University, Ireland
#
# Permission is hereby granted, free of charge, to any person obtaining a
# copy of this software and associated documentation files (the “Software”),
# to deal in the Software without restriction, including without limitation
# the rights to use, copy, modify, merge, publish, distribute, sublicense,
# and/or sell copies of the Software, and to permit persons to whom the
# Software is furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED “AS IS”, WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING
# FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER
# DEALINGS IN THE SOFTWARE.

import requests
import json

server = "http://127.0.0.1:5000"

def get_questionnaire(auth_token, topic, language):
    questionnaire = requests.get(url=server + "/Questionnaire/",
                                 params={"auth":auth_token},
                                 data=json.dumps({"Topic": topic, "Language": language})).json()
    return questionnaire


def post_reply(auth_token, participantId, questionnaireId, replies):
    reply = {}
    reply["ParticipantId"] = participantId
    reply["QuestionnaireId"] = questionnaireId
    reply["Replies"] = [
        {
            "QuestionId": questionId,
            "AnswerId": replies[questionId]
        }
        for questionId in replies
    ]
    result = requests.post(url=server + "/Reply/",
                           params={"auth": auth_token},
                           data=json.dumps(reply))
    return result


def post_action(auth_token, participantId, actionId, completed):
    result = requests.post(url=server + "/Action/",
                           params={"auth": auth_token},
                           data=json.dumps(
                               {"ParticipantId": participantId,
                                "ActionId": actionId,
                                "Completed": bool(completed)}))
    return result


def get_profile(auth_token, actionId, participantId):
    profile = requests.get(url=server + "/Profile/",
                           params={"auth": auth_token},
                           data=json.dumps({"ActionId": actionId,
                                            "ParticipantId": participantId}
                                           )).json()
    return profile


def force_calibration(auth_token):
    calibration = requests.post(url=server + "/Calibrate/",
                                params={"auth": auth_token}).json()
    return calibration


def delete_database(auth_token):
    result = requests.post(url=server + "/Delete/", params={"auth": auth_token})
    return result


def database_dump(auth_token):
    status = requests.get(url=server + "/", params={"auth": auth_token})
    return status
