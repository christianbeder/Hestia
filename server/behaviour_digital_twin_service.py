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

import json
from flask import Flask, request, jsonify
from threading import Thread, Lock
from time import sleep
from datetime import datetime

import behaviour_digital_twin_database
import behaviour_digital_twin_calibration
import behaviour_digital_twin_configuration
import behaviour_digital_twin_models

mutex = Lock()

verbose = True


def print_log(s):
    print(s)
    try:
        behaviour_digital_twin_database.log_entry(s)
    except BaseException as error:
        print("Exception during logging:" + str(error))
    return


def calibration_worker():
    last = datetime(1,1,1,0,0,0,0)
    while True:
        now = datetime.now()
        if (now.hour>=2) and (now.hour<=5) and ((now-last).hours>12):
            last = now
            mutex.acquire()
            try:
                try:
                    print_log("Launching regular calibration " + str(now))
                    status = behaviour_digital_twin_calibration.calibrate()
                except BaseException as error:
                    print_log("Exception:" + str(error))
                print_log("Regular calibration finished" + str(datetime.now()))
            finally:
                mutex.release()
        sleep(60*15)
Thread(target=calibration_worker, daemon=True).start()


app = Flask(__name__)


def authenticate(request_args, access):
    try:
        token=request_args["auth"]
        if behaviour_digital_twin_configuration.auth_token_valid(token, access):
            return True
    except BaseException as error:
        print_log("Exception:" + str(error))
        False
    return False


@app.route('/')
def index():
    mutex.acquire()
    try:
        if not authenticate(request.args, "admin"):
            return jsonify("Authentication error")
        status = behaviour_digital_twin_database.get_status()
        return jsonify(status)
    finally:
        mutex.release()


@app.route('/Questionnaire/', methods=["GET"])
def get_questionnaire():
    mutex.acquire()
    try:
        if not authenticate(request.args, "read"):
            return jsonify("Authentication error")
        try:
            input_data = request.get_json(force=True)
            if verbose:
                print_log("GET Questionnaire")
                print_log("Input:" + str(input_data))

            topic = input_data["Topic"]
            language = input_data["Language"]

            questionnaire = behaviour_digital_twin_configuration.get_questionnaire(topic, language)
            if questionnaire is None:
                output_data = "Topic or language not supported"
            else:
                output_data = questionnaire
        except BaseException as error:
            print_log("Exception:" + str(error))
            output_data = "Fail"

        if verbose:
            print_log("Output:" + str(output_data))
        return jsonify(output_data)
    finally:
        mutex.release()

@app.route('/Reply/', methods=["POST"])
def post_reply():
    mutex.acquire()
    try:
        if not authenticate(request.args, "write"):
            return jsonify("Authentication error")
        try:
            input_data = request.get_json(force=True)
            if verbose:
                print_log("POST Reply")
                print_log("Input:" + str(input_data))

            participantId = input_data["ParticipantId"]
            questionnaireId = input_data["QuestionnaireId"]
            replies = input_data["Replies"]
            for reply in replies:
                questionId = reply["QuestionId"]
                answerId = reply["AnswerId"]
                behaviour_digital_twin_database.report_reply(participantId, questionnaireId, questionId, answerId)
            output_data = "Success"
        except BaseException as error:
            print_log("Exception:" + str(error))
            output_data = "Fail"
        if verbose:
            print_log("Output:" + str(output_data))
        return jsonify(output_data)
    finally:
        mutex.release()

@app.route('/Action/', methods=["POST"])
def post_action():
    mutex.acquire()
    try:
        if not authenticate(request.args, "write"):
            return jsonify("Authentication error")
        try:
            input_data = request.get_json(force=True)
            if verbose:
                print_log("POST Action")
                print_log("Input:" + str(input_data))

            participantId = input_data["ParticipantId"]
            actionId = input_data["ActionId"]
            actionCompleted = bool(input_data["Completed"])
            behaviour_digital_twin_database.report_action(participantId, actionId, actionCompleted)
            output_data = "Success"
        except BaseException as error:
            print_log("Exception:" + str(error))
            output_data = "Fail"
        if verbose:
            print_log("Output:" + str(output_data))
        return jsonify(output_data)
    finally:
        mutex.release()

@app.route('/Profile/', methods=["GET"])
def get_profile():
    mutex.acquire()
    try:
        if not authenticate(request.args, "read"):
            return jsonify("Authentication error")
        try:
            input_data = request.get_json(force=True)
            if verbose:
                print_log("GET Profile")
                print_log("Input:" + str(input_data))

            participantId = input_data["ParticipantId"]
            actionId = input_data["ActionId"]
            P, dP, BI, RAI, A, SN, PBC, Rint, Rid, Rintro, Rext = behaviour_digital_twin_models.likelihoodOfBehaviour(actionId, participantId)
            output_data = {
                "BehaviouralIntention": BI,
                "RelativeAutonomyIndex": RAI,
                "AttitudeTowardsBehaviour": A,
                "SubjectiveNorms": SN,
                "PerceivedBehaviouralControl": PBC,
                "PredictedBehaviour": P
            }
            B = behaviour_digital_twin_database.get_action_response_rate(participantId,actionId)
            if B is not None:
                output_data["ActualBehaviour"] = B
        except BaseException as error:
            print_log("Exception:" + str(error))
            output_data = "Fail"
        if verbose:
            print_log("Output:" + str(output_data))
        return jsonify(output_data)
    finally:
        mutex.release()

@app.route('/Calibrate/', methods=["POST"])
def post_calibrate():
    mutex.acquire()
    try:
        if not authenticate(request.args, "admin"):
            return jsonify("Authentication error")
        try:
            if verbose:
                print_log("POST Calibrate")
            status = behaviour_digital_twin_calibration.calibrate()
        except BaseException as error:
            print_log("Exception:" + str(error))
            status = "Fail"
        if verbose:
            print_log("Output:" + str(status))
        return jsonify(status)
    finally:
        mutex.release()

@app.route('/Delete/', methods=["POST"])
def post_delete():
    mutex.acquire()
    try:
        if not authenticate(request.args, "admin"):
            return jsonify("Authentication error")
        if verbose:
            print_log("POST Delete")
        behaviour_digital_twin_database.delete_all_data()
        if verbose:
            print_log("Output:" + "Database deleted")
        return jsonify("Database deleted")
    finally:
        mutex.release()
