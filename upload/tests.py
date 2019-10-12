from django.test import TestCase
from django.test import Client
from users.models import TANFUser

# Create your tests here.


class CheckUI(TestCase):
    anonymousclient = Client()

    @classmethod
    def setUpTestData(cls):
        cls.user = TANFUser.objects.create_user(email='user@gsa.gov')
        cls.superuser = TANFUser.objects.create_superuser(email='superuser@gsa.gov')
        cls.staffuser = TANFUser.objects.create_superuser(email='staff@gsa.gov')

    def test_about(self):
        """about page has proper data"""
        response = self.anonymousclient.get("/about/")
        self.assertIn(b'Welcome to the TANF Data Reporting system', response.content)

    def test_authentication(self):
        """We cannot get into pages if we are not authenticated"""
        pages = {
            '/': b'Current user',
            '/status/': b'Current user',
            '/viewquarter/': b'Current user',
        }
        for k, v in pages.items():
            response = self.anonymousclient.get(k)
            self.assertNotEqual(response.status_code, 200)
            self.assertNotIn(v, response.content, msg='anonymous ' + k)

            self.client.force_login(self.user)
            response = self.client.get(k)
            self.assertEqual(response.status_code, 200)
            self.assertIn(v, response.content, msg='user ' + k)

            self.client.force_login(self.superuser)
            response = self.client.get(k)
            self.assertEqual(response.status_code, 200)
            self.assertIn(v, response.content, msg='superuser ' + k)

    def test_staffuser_authentication(self):
        """We cannot get into admin pages if we are not staff or superuser authenticated"""
        page = '/useradmin'
        response = self.anonymousclient.get(page)
        self.assertNotEqual(response.status_code, 200)

        self.client.force_login(self.user)
        response = self.client.get(page)
        self.assertNotEqual(response.status_code, 200)

        self.client.force_login(self.superuser)
        response = self.client.get(page)
        self.assertRedirects(response, '/admin/users/tanfuser/', status_code=302, target_status_code=200)

        self.client.force_login(self.staffuser)
        response = self.client.get(page)
        self.assertRedirects(response, '/admin/users/tanfuser/', status_code=302, target_status_code=200)

    def test_upload(self):
        """upload page has proper data"""
        self.client.force_login(self.user)
        response = self.client.get("/")
        self.assertIn(b'Upload to the TANF Data Reporting system', response.content)
