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

import sqlite3
import time
import behaviour_digital_twin_configuration
import os
from datetime import datetime

def get_status():
    result = {}
    try:
        result["Databases"] = []
        con = sqlite3.connect("./data/Hestia_BehaviourDigitalTwin_data.db")
        cur = con.cursor()
        for row in cur.execute("SELECT name FROM sqlite_master"):
            result["Databases"].append(row[0])
    except:
        None
    try:
        result["Parameters"] = []
        for row in cur.execute("SELECT timestamp, key, value FROM parameters"):
            result["Parameters"].append({"timestamp": row[0],
                                         "key":row[1],
                                         "value":row[2]})
    except:
        None
    try:
        result["Actions"] = []
        for row in cur.execute("SELECT timestamp, participantId, actionId, actionCompleted FROM actions"):
            result["Actions"].append({"timestamp": row[0],
                                      "participantId":row[1],
                                      "actionId":row[2],
                                      "actionCompleted":row[3]})
    except:
        None
    try:
        result["Replies"] = []
        for row in cur.execute("SELECT timestamp, participantId, questionnaireId, questionId, answerId FROM replies"):
            result["Replies"].append({"timestamp":row[0],
                                      "participantId":row[1],
                                      "questionnaireId":row[2],
                                      "questionId":row[3],
                                      "answerId":row[4]})
    except:
        None
    try:
        f = open("./data/log.txt", "r")
        result["Log"] = f.read()
        f.close()
    except:
        None
    return result


def log_entry(s):
    timestamp = datetime.now()
    f = open("./data/log.txt", "a")
    f.write("[" + str(timestamp) + "] " + s)
    f.close()
    return


def report_action(participantId, actionId, actionCompleted):
    con = sqlite3.connect("./data/Hestia_BehaviourDigitalTwin_data.db")
    cur = con.cursor()
    res = cur.execute("SELECT name FROM sqlite_master WHERE name=\"actions\"")
    if res.fetchone() is None:
        cur.execute("CREATE TABLE actions(timestamp INTEGER, participantId TEXT, actionId TEXT, actionCompleted INTEGER)")
    timestamp = int(time.time())
    cur.execute("INSERT INTO actions(timestamp, participantId, actionId, actionCompleted) VALUES (%d,\"%s\",\"%s\",%d)" % (timestamp, participantId, actionId, int(actionCompleted)))
    con.commit()
    return


def report_reply(participantId, questionnaireId, questionId, answerId):
    con = sqlite3.connect("./data/Hestia_BehaviourDigitalTwin_data.db")
    cur = con.cursor()
    res = cur.execute("SELECT name FROM sqlite_master WHERE name=\"replies\"")
    if res.fetchone() is None:
        cur.execute("CREATE TABLE replies(timestamp INTEGER, participantId TEXT, questionnaireId TEXT, questionId TEXT, answerId TEXT)")
    timestamp = int(time.time())
    cur.execute("INSERT INTO replies(timestamp, participantId, questionnaireId, questionId, answerId) VALUES (%d,\"%s\",\"%s\",\"%s\",\"%s\")" % (timestamp, participantId, questionnaireId, questionId, answerId))
    con.commit()
    return


def set_parameters(key_value_pairs, replace=True):
    con = sqlite3.connect("./data/Hestia_BehaviourDigitalTwin_data.db")
    cur = con.cursor()
    res = cur.execute("SELECT name FROM sqlite_master WHERE name=\"parameters\"")
    if res.fetchone() is None:
        cur.execute("CREATE TABLE parameters(timestamp INTEGER, key TEXT, value REAL)")
    timestamp = int(time.time())
    for key in key_value_pairs:
        if replace:
            cur.execute("DELETE FROM parameters WHERE key=\"%s\""%key)
        cur.execute("INSERT INTO parameters(timestamp, key, value) VALUES (%d,\"%s\",%f)" % (timestamp, key, key_value_pairs[key]))
    con.commit()
    return


def get_parameters(keys):
    key_value_pairs = {}
    con = sqlite3.connect("./data/Hestia_BehaviourDigitalTwin_data.db")
    cur = con.cursor()
    for key in keys:
        res = cur.execute("SELECT timestamp, key, value FROM parameters WHERE (key=\"%s\") ORDER BY timestamp DESC"%(key))
        first = res.fetchone()
        if first is not None:
            value = float(first[2])
            key_value_pairs[key] = value
    return key_value_pairs


def get_latest_replies(model, topicId, participantId):
    questionnaireIdsForTopic = behaviour_digital_twin_configuration.get_questionnaireIds_for_topic(model, topicId)
    con = sqlite3.connect("./data/Hestia_BehaviourDigitalTwin_data.db")
    cur = con.cursor()
    questionnaireIdsForTopicAndParticipant = set()
    for questionnaireId in cur.execute("SELECT DISTINCT questionnaireId FROM replies WHERE participantId=\"%s\""%(participantId)):
        if questionnaireId[0] in questionnaireIdsForTopic:
            questionnaireIdsForTopicAndParticipant.add(questionnaireId[0])
    latest_overall_timestamp = 0
    result = None
    for questionnaireId in questionnaireIdsForTopicAndParticipant:
        question_answer_pairs = {}
        latest_timestamp = 0
        for row in cur.execute("SELECT timestamp, questionId, answerId FROM replies WHERE (participantId=\"%s\") AND (questionnaireId=\"%s\") ORDER BY timestamp DESC"%(participantId,questionnaireId)):
            timestamp = int(row[0])
            questionId = row[1]
            answerId = row[2]
            if not questionId in question_answer_pairs:
                if timestamp > latest_timestamp:
                    latest_timestamp = timestamp
                question_answer_pairs[questionId] = answerId
        model_set = behaviour_digital_twin_configuration.extract_complete_set(model,questionnaireId,question_answer_pairs)
        if model_set is not None:
            if latest_timestamp > latest_overall_timestamp:
                latest_overall_timestamp = latest_timestamp
                result = model_set
    return result


def delete_all_data():
    os.remove("./data/Hestia_BehaviourDigitalTwin_data.db")
    return


def get_all_action_response_rates():
    N = {}
    n = {}
    con = sqlite3.connect("./data/Hestia_BehaviourDigitalTwin_data.db")
    cur = con.cursor()
    for row in cur.execute("SELECT participantId, actionId, actionCompleted FROM actions"):
        participantId = row[0]
        actionId = row[1]
        completed = bool(row[2])
        if actionId not in N:
            N[actionId] = {}
            n[actionId] = {}
        if participantId not in N[actionId]:
            N[actionId][participantId] = 0
            n[actionId][participantId] = 0
        N[actionId][participantId] += 1
        if completed:
            n[actionId][participantId] += 1
    return N,n


def get_action_response_rate(participantId, actionId):
    con = sqlite3.connect("./data/Hestia_BehaviourDigitalTwin_data.db")
    cur = con.cursor()
    n = 0
    N = 0
    for row in cur.execute("SELECT actionCompleted FROM actions WHERE (participantId=\"%s\") AND (actionId=\"%s\")"%(participantId,actionId)):
        completed = bool(row[0])
        N += 1
        if completed:
            n+=1
    if (N>0):
        return float(n)/float(N)
    else:
        return None

