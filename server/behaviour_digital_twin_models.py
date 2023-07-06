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

import behaviour_digital_twin_database
import behaviour_digital_twin_configuration
import math

def TPB(topicId, participantId, tpb_parameters=None):
    replies = behaviour_digital_twin_database.get_latest_replies("TPB", topicId, participantId)
    A = replies["BehaviouralBeliefs"]
    SN = replies["ControlBeliefs"]
    PBC = replies["NormativeBeliefs"]

    if tpb_parameters is None:
        try:
            weights = behaviour_digital_twin_database.get_parameters(["wA_" + topicId, "wSN_" + topicId, "wPBC_" + topicId])
            wA = weights["wA_"+topicId]
            wSN = weights["wSN_"+topicId]
            wPBC = weights["wPBC_"+topicId]
        except:
            wA = 1.0
            wSN = 1.0
            wPBC = 1.0
    else:
        wA = tpb_parameters[0]
        wSN = tpb_parameters[1]
        wPBC = tpb_parameters[2]

    BI = (wA * A + wSN * SN + wPBC * PBC) / 3.0
    return BI, A, SN, PBC


def SDT(topicId, participantId, sdt_parameters=None):
    replies = behaviour_digital_twin_database.get_latest_replies("SDT", topicId, participantId)

    Rint = replies["Intrinsic"]
    Rid = replies["Identified"]
    Rintro = replies["Introjected"]
    Rext = replies["External"]

    if sdt_parameters is None:
        try:
            weights = behaviour_digital_twin_database.get_parameters(["wInt_" + topicId, "wId_" + topicId, "wIntro_" + topicId, "wExt_" + topicId])
            wInt = weights["wInt_"+topicId]
            wId = weights["wId_"+topicId]
            wIntro = weights["wIntro_"+topicId]
            wExt = weights["wExt_"+topicId]
        except:
            wInt = 1.0
            wId = 1.0
            wIntro = 1.0
            wExt = 1.0
    else:
        wInt = sdt_parameters[0]
        wId = sdt_parameters[1]
        wIntro = sdt_parameters[2]
        wExt = sdt_parameters[3]

    RAI = (2 * wInt * Rint + wId * Rid - wIntro * Rintro - 2 * wExt * Rext) / 6.0
    return RAI, Rint, Rid, Rintro, Rext


def likelihoodOfBehaviour(actionId, participantId, topic=None, tpb_parameters=None, sdt_parameters=None, IAG=None):
    if topic is None:
        topic = behaviour_digital_twin_configuration.get_topic_for_action(actionId)

    if IAG is None:
        try:
            IAG = behaviour_digital_twin_database.get_parameters(["IAG_" + actionId])["IAG_" + actionId]
        except:
            IAG = 0.0

    BI, A, SN, PBC = TPB(topic, participantId, tpb_parameters)
    RAI, Rint, Rid, Rintro, Rext = SDT(topic, participantId, sdt_parameters)


    lambda_BI = behaviour_digital_twin_configuration.get_parameter("ImportanceFactorBI")
    lambda_RAI = behaviour_digital_twin_configuration.get_parameter("ImportanceFactorRAI")

    beta = lambda_BI*BI + lambda_RAI*RAI - IAG

    gamma = behaviour_digital_twin_configuration.get_parameter("ActivationFunctionGamma")
    P = 1.0 / (1 + math.exp(-beta/gamma))
    dP = P * (1.0 - P) / gamma

    return P, dP, BI, RAI, A, SN, PBC, Rint, Rid, Rintro, Rext

