# -*- coding: utf-8 -*-
import os
import sys
cur_dir = os.path.abspath(os.path.join( os.path.dirname(__file__) ) )
ext_path = os.path.join(cur_dir, 'wechatapi')
sys.path.append(ext_path)

from . import controllers
from . import models
