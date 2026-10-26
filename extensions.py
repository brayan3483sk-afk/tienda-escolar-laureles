from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

# Inicializar Limitador de Tasa (Rate Limiting)
limiter = Limiter(key_func=get_remote_address)
