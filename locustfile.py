import csv
import random
from locust import HttpUser, task, between

USERS = []
try:
    with open('usuarios_demo.csv', encoding='utf-8-sig') as f:
        r = csv.DictReader(f)
        for row in r:
            USERS.append({'email': row['EMAIL'].strip(), 'pass': 'Demo1234!'})
except Exception:
    pass

class AuthUser(HttpUser):
    wait_time = between(2, 3)
    @task(1)
    def login(self):
        if not USERS: return
        u = USERS[random.randint(0, len(USERS)-1)]
        self.client.post('/v1/auth/login', json={'email': u['email'], 'password': u['pass']}, name='login')
