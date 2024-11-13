from itsdangerous.url_safe import URLSafeTimedSerializer as Serializer

s = Serializer('secret')  
token = s.dumps({'user_id': 1})    
s.loads(token, max_age=1)  