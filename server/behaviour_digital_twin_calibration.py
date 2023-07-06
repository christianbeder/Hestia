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
import behaviour_digital_twin_models

def calibrate():
    N,n = behaviour_digital_twin_database.get_all_action_response_rates()
    topics = {}
    for actionId in N:
        topic = behaviour_digital_twin_configuration.get_topic_for_action(actionId)
        if topic not in topics:
            topics[topic] = [actionId]
        else:
            topics[topic].append(actionId)

    lambda_BI = behaviour_digital_twin_configuration.get_parameter("ImportanceFactorBI")
    lambda_RAI = behaviour_digital_twin_configuration.get_parameter("ImportanceFactorRAI")
    sigma = behaviour_digital_twin_configuration.get_parameter("ParameterPriorVariance")
    eta = behaviour_digital_twin_configuration.get_parameter("CalibrationLearningRate")
    iterations = behaviour_digital_twin_configuration.get_parameter("CalibrationIterations")
    result = {}
    for topic in topics:
        tpb_parameters = [1.0]*3
        sdt_parameters = [1.0]*4
        IAG = {}
        for action in topics[topic]:
            IAG[action] = 0.0

        for iteration in range(iterations):
            dTPB = [0.0]*len(tpb_parameters)
            for i in range(len(dTPB)):
                dTPB[i] = 2 * (tpb_parameters[i] - 1.0) / sigma
            dSDT = [0.0]*len(sdt_parameters)
            for i in range(len(dSDT)):
                dSDT[i] = 2 * (sdt_parameters[i] - 1.0) / sigma
            for action in topics[topic]:
                dIAG = 0
                for participant in N[action]:
                    NN = float(N[action][participant])
                    nn = float(n[action][participant])
                    if (NN>1) and (nn>0) and (nn<NN):
                        variance = (nn/NN)*(1.0 - (nn/NN))

                        P, dP, BI, RAI, A, SN, PBC, Rint, Rid, Rintro, Rext = behaviour_digital_twin_models.likelihoodOfBehaviour(action, participant, topic, tpb_parameters, sdt_parameters, IAG[action])
                        omega = 2*((nn/NN) - P)*dP/variance
                        dIAG += omega
                        dTPB[0] -= lambda_BI*omega*A
                        dTPB[1] -= lambda_BI*omega*SN
                        dTPB[2] -= lambda_BI*omega*PBC
                        dSDT[0] -= lambda_RAI*2*omega*Rint
                        dSDT[1] -= lambda_RAI*omega*Rid
                        dSDT[2] -= -lambda_RAI*omega*Rintro
                        dSDT[3] -= -lambda_RAI*2*omega*Rext

                IAG[action] -= eta * dIAG
            for i in range(3):
                tpb_parameters[i] -= eta * dTPB[i]
            for i in range(4):
                sdt_parameters[i] -= eta * dSDT[i]

        result[topic] = {"TPB":tpb_parameters, "SDT":sdt_parameters, "IAG":IAG}
        behaviour_digital_twin_database.set_parameters({"wA_%s"%topic:tpb_parameters[0], "wSN_%s"%topic:tpb_parameters[1], "wPBC_%s"%topic:tpb_parameters[2]})
        behaviour_digital_twin_database.set_parameters({"wInt_%s"%topic:sdt_parameters[0], "wId_%s"%topic:sdt_parameters[1], "wIntro_%s"%topic:sdt_parameters[2], "wExt_Flexibility":sdt_parameters[3] })
        behaviour_digital_twin_database.set_parameters({"IAG_%s"%action:IAG[action] for action in topics[topic] })

    return result
