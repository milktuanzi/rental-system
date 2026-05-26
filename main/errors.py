"""
自定义异常类和全局错误处理
"""
from flask import render_template, jsonify


class APIException(Exception):
    """API异常基类"""
    def __init__(self, message, code=400, status_code=400):
        self.message = message
        self.code = code
        self.status_code = status_code
        super().__init__(self.message)


class ValidationError(APIException):
    """数据验证异常"""
    def __init__(self, message):
        super().__init__(message, code=4001, status_code=400)


class AuthenticationError(APIException):
    """认证异常"""
    def __init__(self, message='请先登录'):
        super().__init__(message, code=4011, status_code=401)


class AuthorizationError(APIException):
    """授权异常"""
    def __init__(self, message='权限不足'):
        super().__init__(message, code=4031, status_code=403)


class NotFoundError(APIException):
    """资源不存在异常"""
    def __init__(self, message='资源不存在'):
        super().__init__(message, code=4041, status_code=404)


class BusinessException(APIException):
    """业务异常"""
    def __init__(self, message):
        super().__init__(message, code=5001, status_code=400)


def register_error_handlers(app):
    """
    注册全局错误处理器
    """

    @app.errorhandler(APIException)
    def handle_api_exception(error):
        """处理API异常"""
        response = {
            'code': error.code,
            'message': error.message,
            'status': 'error'
        }
        return jsonify(response), error.status_code

    @app.errorhandler(404)
    def handle_404(error):
        """处理404错误"""
        return render_template('errors/404.html'), 404

    @app.errorhandler(500)
    def handle_500(error):
        """处理500错误"""
        return render_template('errors/500.html'), 500

    @app.errorhandler(403)
    def handle_403(error):
        """处理403错误"""
        return render_template('errors/403.html'), 403

