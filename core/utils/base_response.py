class BaseResponse:
    # @staticmethod
    # def success_response(data=None, message="Request successful"):
    #     return {"success": True, "message": message, "data": data}

    # @staticmethod
    # def error_response(message="An error occurred"):
    #     return {"success": False, "message": message, "data": None}
    @staticmethod
    def success_response(data=None, message="Request successful"):
        return {
            "success": True,
            "message": message,
            "data": data
        }

    @staticmethod
    def error_response(message="An error occurred", data=None):
        return {
            "success": False,
            "message": message,
            "data": data
        }