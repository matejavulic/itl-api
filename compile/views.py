from django.shortcuts import render
from django.http import HttpResponse, JsonResponse
from rest_framework import status
from django.views.generic import TemplateView

from .dsl.language import *
from lark import exceptions as lexc

# library for stdout redirecting
from contextlib import redirect_stdout
from io import StringIO

# library to measure compile time
import time as tim

# libraries for plt conversion to base64 png
from io import BytesIO
import base64

# libraries to validate request 
from . import validators as val
import json

def index(request):
    return HttpResponse("Compile-OK!")

class Compile(TemplateView):

    def get(self, request, *args, **kwargs):
        return HttpResponse('This is GET request')

    def post(self, request, *args, **kwargs):
            
           #TODO Check using of the load balance solutions (Celery, Redis,...)
           
        resCodeSucc = {
                'status': None, 
                'state': 'Success',
                'message': "Code successufully executed.",
                'result': None,
                'time': None,
                'graphs': None
                }

        resCodeFail = {
                'status': None,
                'state': 'Error',
                'type': None,
                'message': None
            }
        
        resBadReq = {
            'status': None,
            'state': 'Error',
            'type': None,
            'message': None
        }
        
        statusCode = status.HTTP_200_OK
        
        # try to execute code and if successful return results
        try:
            # check if request has proper format in JSON (deserializing)
            req = json.loads(request.body.decode("utf-8"))
        except Exception as e: 
            statusCode = status.HTTP_400_BAD_REQUEST
            resBadReq['status'] = statusCode  
            resBadReq['type'] = 'InvalidRequest'
            resBadReq['message'] = {
            'details': 'Invalid request body, should be in JSON format',
            }
           
            return JsonResponse(resBadReq, status=statusCode)
        
        validation = val.validate_api(req)
        if not validation['success']:
            statusCode = status.HTTP_400_BAD_REQUEST
            resBadReq['status'] = statusCode  
            resBadReq['type'] = 'InvalidRequest'
            resBadReq['message'] = {
            'details': validation['details'],
            'errors': validation['errors']
            }
           
            return JsonResponse(resBadReq, status=statusCode)
        try:    
            # if it has a proper body continue to process the request
            codeToExec = req['code']
            graph = None
            figDataImg = None
            f = StringIO()
            with redirect_stdout(f):
                start = tim.time()
                graph = runn(codeToExec)
                end = tim.time()
                compTime = round((end - start)*1000)
                
                try:   
                    if (graph != None and req['pictureOpt']['generate']=='True'):
                        figDataImg = self.convertToB64(graph, req['pictureOpt']['extension'])
                        resCodeSucc['graphs'] = figDataImg
                except KeyError:
                     pass
            
            resCodeSucc['status'] = statusCode
            resCodeSucc['result'] = f.getvalue()
            resCodeSucc['time'] = compTime
            
            return JsonResponse(resCodeSucc, status = statusCode)
       
        # handler for UnexpectedCharacters error 
        except lexc.UnexpectedCharacters as errUC:
            statusCode = status.HTTP_422_UNPROCESSABLE_ENTITY
            resCodeFail['status'] = statusCode
            resCodeFail['type'] = 'UnexpectedCharacters'
            trace = 'Hidden'
            try:
                if (req['maskTrace'] == 'False'):
                    trace = str(errUC)
            except KeyError: 
                pass
            resCodeFail['message'] = {
                    'line': errUC.line,
                    'column': errUC.column,
                    'body': 'Instruction error on the line ' + str(errUC.line) + '. at the position ' + str(errUC.column) + '.',
                    'trace': trace
                }
            return JsonResponse(resCodeFail, status = statusCode)
                                
        # handler for KeyError error 
        except KeyError as errKE:
            statusCode = status.HTTP_422_UNPROCESSABLE_ENTITY
            resCodeFail['status'] = statusCode
            resCodeFail['type'] = 'KeyError'
            trace = "Hidden"
            try:
                if (req['maskTrace'] == 'False'):
                    trace = str(errKE)
            except KeyError: 
                pass
            resCodeFail['message'] = {
                    'variable': errKE.args[0],
                    'body': 'Unknown variable:' + errKE.args[0],
                    'trace': trace
                }
            return JsonResponse(resCodeFail, status = statusCode)
                                                
        # handler for UnexpectedEOF error
        except lexc.UnexpectedEOF as errUE:
            statusCode = status.HTTP_422_UNPROCESSABLE_ENTITY
            resCodeFail['status'] = statusCode
            resCodeFail['type'] = 'UnexpectedEOF'
            trace = "Hidden"
            try:
                if (req['maskTrace'] == 'False'):
                    trace = str(errUE)
            except KeyError: 
                pass
            resCodeFail['message'] = {
                    'body': 'Unexpected end of the file. Did you close all brackets?',
                    'trace': trace
                }
            return JsonResponse(resCodeFail, status = statusCode)
            
        # handler for SyntaxError error
        except SyntaxError as errSE:
            statusCode = status.HTTP_422_UNPROCESSABLE_ENTITY
            resCodeFail['status'] = statusCode
            resCodeFail['type'] = 'SyntaxError'
            trace = "Hidden"
            try:
                if (req['maskTrace'] == 'False'):
                    trace = str(errSE)
            except KeyError: 
                pass
            resCodeFail['message'] = {
                    'body': 'Unsupported function type for drawing.',
                    'trace': trace
                }
            return JsonResponse(resCodeFail, status = statusCode) # use reason to set reason phrase
                           
        # handler for general error
        except Exception as errGX:
            statusCode = status.HTTP_500_INTERNAL_SERVER_ERROR
            resCodeFail['status'] = statusCode
            resCodeFail['type'] = 'GeneralErr'
            trace = "Hidden"
            try:
                if (req['maskTrace'] == 'False'):
                    trace = str(errGX)
            except KeyError: 
                pass
            resCodeFail['message'] = {
                    'body': 'An error occured. Please try later.',
                    'trace': trace
                }
            return JsonResponse(resCodeFail, status = statusCode)
            
    def convertToB64(self, graph, extension):
        #https://stackoverflow.com/questions/31492525/converting-matplotlib-png-to-base64-for-viewing-in-html-template
        try:
            figfile = BytesIO()
            graph.savefig(figfile, format=extension)
            figfile.seek(0)  # rewind to the beginning of file
            #figdataPng = base64.b64encode(figfile.read())
            return str(base64.b64encode(figfile.getvalue()))
        except:
            raise Exception("Error while generating img object from plt.") 
    
   