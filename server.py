#!/usr/bin/python
from http.server import BaseHTTPRequestHandler,HTTPServer
from os import curdir, sep
import sys, cgi, os, json
import numpy as np
import pandas as pd
import pickle as pkl

class dummyHandler(BaseHTTPRequestHandler):

    #def __init__(self, request, client_address, server):
    #    super(dummyHandler, self).__init__(request, client_address, server)
    #    sys.path.append('lib')
    #    fmodel = 'lib/model-Melb.pkl'  # path of the trained model file
    #    self.model = pkl.load(open(fmodel, 'rb'))['MODEL']  # trained model
    #    print('trained model loaded')

    def preprocess(self, recommendations): 
        # scale scores and convert arrays to lists
        score_max = recommendations[0]['TotalScore']
        score_min = recommendations[-1]['TotalScore']
        assert(abs(score_max) > 1e-9)
        assert(abs(score_min) > 1e-9)
        assert(score_max > score_min)

        # linear scaling
        # a * score_max + b = 100
        # a * score_min + b = 10
        a = np.exp(np.log(90) - np.log(score_max - score_min))
        b = 100 - a * score_max
        print(a, b)

        for j in range(len(recommendations)):
            rec = recommendations[j]
            score0 = rec['TotalScore']
            score1 = 0
            if j == 0:
                score1 = 100
            elif j == len(recommendations) - 1:
                score1 = 10
            else:
                score1 = a * rec['TotalScore'] + b

            assert(score1 > 9)
            assert(score1 < 101)
            recommendations[j]['TotalScore'] = score1

            # distribute score to POIs and Transitions
            assert(abs(score0) > 1e-9)
            ratio = np.exp(np.log(score1) - np.log(score0))
            recommendations[j]['POIScore'] = (rec['POIScore'] * ratio).tolist()
            recommendations[j]['TransitionScore'] = (rec['TransitionScore'] * ratio).tolist()
            recommendations[j]['POIFeatureScore'] = (rec['POIFeatureScore'] * ratio).tolist()
            recommendations[j]['TransitionFeatureScore'] = (rec['TransitionFeatureScore'] * ratio).tolist()
            recommendations[j]['Trajectory'] = (rec['Trajectory']).tolist()
            if 'POIFeatureWeight' in rec:
                recommendations[j]['POIFeatureWeight'] = rec['POIFeatureWeight'].tolist()
                recommendations[j]['TransitionFeatureWeight'] = rec['TransitionFeatureWeight'].tolist()

        return recommendations


    def recommend(self, start, length):
        print('in recommend()')
        #startPOI = 9  # the start POI-ID for the desired trajectory, can be any POI-ID in flickr-photo/data/poi-Melb-all.csv
        #length = 8    # the length of desired trajectory: the number of POIs in trajectory (including start POI)
                       # if length > 8, the inference could be slow
        assert(start > 0)
        assert(2 <= length <= 10)

        if not hasattr(self, 'model'):
            sys.path.append('lib')
            fmodel = 'lib/model-Melb.pkl'  # path of the trained model file
            self.model = pkl.load(open(fmodel, 'rb'))['MODEL']  # trained model
            print('trained model loaded')

        recommendations = self.model.predict(start, length) # recommendations is list of 10 trajectories
        for i in range(len(recommendations)):
            print('Top %d recommendation: %s' % (i+1, str(list(recommendations[i]['Trajectory']))))
        for i in range(len(recommendations)):
            print('%s' % recommendations[i]['TotalScore'])

        # encode the top-2 into a string: p0,p1,...,pn;p0,p1,...,pn
        #return ','.join([str(p) for p in recommendations[0]]) + ';' + ','.join([str(p) for p in recommendations[1]])

        # return recommended trajectories as well as a number of scores
        return json.dumps(self.preprocess(recommendations), sort_keys=True)


    # GET requests handler
    def do_GET(self):
        print('in do_GET()')
        if self.path=="/":
            self.path="/index.html"

        try:
            #Check the file extension required and
            #set the right mime type

            sendReply = False
            if self.path.endswith(".html"):
                mimetype='text/html'
                sendReply = True
            if self.path.endswith(".jpg"):
                mimetype='image/jpg'
                sendReply = True
            if self.path.endswith(".gif"):
                mimetype='image/gif'
                sendReply = True
            if self.path.endswith(".js"):
                mimetype='application/javascript'
                sendReply = True
            if self.path.endswith(".css"):
                mimetype='text/css'
                sendReply = True

            if sendReply == True:
                #Open the static file requested and send it
                fname = curdir + sep + self.path
                f = open(curdir + sep + self.path, 'rb') 
                #with open(fname, 'r') as f1:
                #    for line in f1: print(line)
                self.send_response(200)
                self.send_header('Content-type',mimetype)
                self.end_headers()
                self.wfile.write(f.read())
                f.close()
            return

        except IOError:
            self.send_error(404,'File Not Found: %s' % self.path)


    # POST requests handler
    def do_POST(self):
        print('in do_POST()')
        if self.path=="/recommend":
            formData = cgi.FieldStorage(
                fp=self.rfile, 
                headers=self.headers,
                environ={'REQUEST_METHOD':'POST',
                         'CONTENT_TYPE':self.headers['Content-Type'],
            })
            start = int(formData["START"].value)
            length = int(formData["LENGTH"].value)
            print("Start point: %d, length: %d" % (start, length))
            output = self.recommend(start, length)
            self.send_response(200)
            self.end_headers()
            #output = "<p>Thanks! start=%d, length=%d</p>" % (start, length)
            self.wfile.write(output.encode('utf-8'))
            return          
            
def check_system():
    if sys.platform == "darwin":
        if not os.path.exists("./lib/inference_lv_linux.so"):
            os.rename("./lib/inference_lv.so", "./lib/inference_lv_linux.so")
            os.rename("./lib/inference_lv_mac.so", "./lib/inference_lv.so")
    elif sys.platform == "win32":
        raise OSError("does not support Windows systems")   

if __name__ == '__main__':
    check_system()
    try:
        # Create a web server and define the handler
        PORT = 8080
        server = HTTPServer(('', PORT), dummyHandler)
        print('Started local httpserver on port %d' % PORT)
    
        # Waiting for incoming http requests
        server.serve_forever()

    except KeyboardInterrupt:
        print(' Shutting down the web server')
        server.socket.close()
 
