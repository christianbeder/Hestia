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
import math


f = open("configuration/parameters.json")
parameters_file = json.load(f)
f.close()
def get_parameter(key):
    value = parameters_file[key]
    return value


def auth_token_valid(token, access):
    auth_tokens = get_parameter("AuthenticationTokens")
    for auth in auth_tokens:
        if auth["Token"] == token:
            user = auth["User"]
            if access in auth["Access"]:
                print("Request authenticated for user ", user)
                return True
    return False


def get_questionnaire(topic, language):
    f = open("configuration/topics.json")
    topics_file = json.load(f)
    f.close()
    filename = None
    for t in topics_file:
        if t["Topic"] == topic:
            for q in t["Questionnaires"]:
                if q["Language"] == language:
                    filename = q["File"]
                    break
            break
    if filename is None:
        questionnaire = None
    else:
        f = open("questionnaires/" + filename)
        questionnaire = json.load(f)
        f.close()
    return questionnaire


def get_questionnaireIds_for_topic(model, topicId):
    questionnairesForModel = set()
    f = open("configuration/models.json")
    models_file = json.load(f)
    f.close()
    for m in models_file:
        if m["Model"]==model:
            questionnairesForModel.add(m["QuestionnaireId"])
    questionnaireIds = set()
    f = open("configuration/topics.json")
    topics_file = json.load(f)
    f.close()
    for t in topics_file:
        if t["Topic"] == topicId:
            for q in t["Questionnaires"]:
                filename = q["File"]
                f = open("questionnaires/" + filename)
                questionnaire = json.load(f)
                f.close()
                if questionnaire["QuestionnaireId"] in questionnairesForModel:
                    questionnaireIds.add(questionnaire["QuestionnaireId"])
    return questionnaireIds


def get_scales():
    f = open("configuration/scales.json")
    scales_file = json.load(f)
    f.close()
    scales = {}
    for scale in scales_file:
        scaleId = scale["ScaleId"]
        scales[scaleId] = {}
        for code in scale["Coding"]:
            scales[scaleId][code["AnswerId"]] = code["Value"]
    return scales


def extract_complete_set(model, questionnaire, question_answer_pairs):
    scales = get_scales()
    f = open("configuration/models.json")
    models_file = json.load(f)
    f.close()
    for m in models_file:
        if (m["Model"]==model) and (m["QuestionnaireId"]==questionnaire):
            sections = {}
            model_valid = True
            for section in m["Sections"]:
                sections[section] = 0
                total_weight = 0
                for question in m["Sections"][section]:
                    if question["QuestionId"] in question_answer_pairs:
                        id = question["QuestionId"]
                        answer = question_answer_pairs[id]
                        scale = question["Scale"]
                        weight = question["Weight"]
                        total_weight += abs(weight)
                        sections[section] += weight * scales[scale][answer]
                    else:
                        model_valid = False
                        break
                if total_weight==0:
                    model_valid = False
                else:
                    sections[section] /= total_weight
                if not model_valid:
                    break
            if model_valid:
                return sections
    return None


def get_topic_for_action(action):
    f = open("configuration/topics.json")
    topics_file = json.load(f)
    f.close()
    for topic in topics_file:
        if action in topic["Actions"]:
            return topic["Topic"]
        if topic["DefaultTopic"]:
            default = topic["Topic"]
    return default
