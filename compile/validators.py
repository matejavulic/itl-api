from . import serializers as ser

def validate_api(request):
    response = {}
    response["success"] = True
    response["errors"] = None
    response["details"] = None
    validation = ser.DataSerializer(data = request)
    
    if not validation.is_valid():
        response["success"] = False
        response["errors"] = validation.errors
        response["details"] = "Invalid request body"
    
    return response  