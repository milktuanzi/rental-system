"""
智能房屋租赁系统 - Flask应用入口
"""
import os
import sys

# 将项目根目录加入 Python 模块搜索路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from main import create_app

# 创建应用实例
config_name = os.environ.get('FLASK_ENV', 'development')
app = create_app(config_name)


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=1145, debug=True)
