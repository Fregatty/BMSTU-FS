from django.test import TestCase
from django.contrib.auth.models import User
from BMSTUFS.models import Folder, Profile


class URLTests(TestCase):

    def setUp(self):
        test_user = User.objects.create_user(username='testuser1', first_name='Viktor', password='plsletmein',
                                             email='rz5555@yandex.ru')
        test_user.save()
        profile = Profile.objects.create(user=test_user, department=None)
        profile.save()
        folder = Folder.objects.create(id=5, name='New_folder', owner=test_user)
        folder.save()

    def test_homepage(self):
        response = self.client.get('/')
        self.assertEqual(response.status_code, 200)

    def test_folder(self):
        login = self.client.login(username='testuser1', password='plsletmein')
        response = self.client.get('/storage/5')
        self.assertEqual(response.status_code, 301)

    def test_registration(self):
        login = self.client.login(username='testuser1', password='plsletmein')
        response = self.client.get('/register')
        self.assertEqual(response.status_code, 301)

    def test_edit(self):
        login = self.client.login(username='testuser1', password='plsletmein')
        response = self.client.get('/edit')
        self.assertEqual(response.status_code, 301)

    def test_storage(self):
        login = self.client.login(username='testuser1', password='plsletmein')
        response = self.client.get('/storage')
        self.assertEqual(response.status_code, 200)

    def test_email(self):
        login = self.client.login(username='testuser1', password='plsletmein')
        response = self.client.get('/email')
        self.assertEqual(response.status_code, 200)

    def test_history(self):
        login = self.client.login(username='testuser1', password='plsletmein')
        response = self.client.get('/history')
        self.assertEqual(response.status_code, 200)
