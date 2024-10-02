import unittest
from app import app

class TestApp(unittest.TestCase):
    def setUp(self):
        self.app = app.test_client()

    def test_login(self):
        response = self.app.post('/users/login', json={'email': 'test@example.com'})
        self.assertEqual(response.status_code, 200)

if __name__ == '__main__':
    unittest.main()
