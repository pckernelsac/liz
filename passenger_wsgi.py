#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Punto de entrada ASGI para Passenger / despliegue WSGI-ASGI.
Requiere Passenger con soporte ASGI o un adaptador ASGI→HTTP del hosting.
"""
import os
import sys

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

if '__main__' not in sys.modules:
    sys.modules['__main__'] = type(sys)('__main__')

# aplicación ASGI (FastAPI)
from app import app as application
