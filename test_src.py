# -*- coding: utf-8 -*-
import unittest

from src import app, db
from src.models import Movie, User
from src.commands import forge, initdb


class WatchlistTestCase(unittest.TestCase):

    def setUp(self):
        app.config.update(
            TESTING=True,
            SQLALCHEMY_DATABASE_URI='sqlite:///:memory:'
        )
        db.create_all()

        user = User(name='Test', username='test')
        user.set_password('123')
        movie = Movie(title='Test Title', year='2020')
        db.session.add_all([user, movie])
        db.session.commit()

        self.client = app.test_client()
        self.runner = app.test_cli_runner()

    def tearDown(self):
        db.session.remove()
        db.drop_all()

    def login(self):
        self.client.post('/login', data=dict(
            username='test',
            password='123'
        ), follow_redirects=True)

    def test_app_exist(self):
        self.assertIsNotNone(app)

    def test_app_is_testing(self):
        self.assertTrue(app.config['TESTING'])

    def test_404_page(self):
        response = self.client.get('/nothing')
        data = response.get_data(as_text=True)
        self.assertIn('Page Not Found - 404', data)
        self.assertIn('Go Back', data)
        self.assertEqual(response.status_code, 404)

    def test_index_page(self):
        response = self.client.get('/')
        data = response.get_data(as_text=True)
        self.assertIn('Test\'s Watch-List', data)
        self.assertIn('Test Title', data)
        self.assertEqual(response.status_code, 200)

    def test_login_protect(self):
        response = self.client.get('/')
        data = response.get_data(as_text=True)
        self.assertNotIn('Logout', data)
        self.assertNotIn('Settings', data)
        self.assertNotIn('<form method="post">', data)
        self.assertNotIn('Delete', data)
        self.assertNotIn('Edit', data)

    def test_login(self):
        response = self.client.post('/login', data=dict(
            username='test',
            password='123'
        ), follow_redirects=True)
        data = response.get_data(as_text=True)
        self.assertIn('Login Success', data)
        self.assertIn('Logout', data)
        self.assertIn('Settings', data)
        self.assertIn('Delete', data)
        self.assertIn('Edit', data)
        self.assertIn('<form method="post">', data)

        response = self.client.post('/login', data=dict(
            username='test',
            password='456'
        ), follow_redirects=True)
        data = response.get_data(as_text=True)
        self.assertNotIn('Login Success', data)
        self.assertIn('Invalid username or password', data)

        response = self.client.post('/login', data=dict(
            username='wrong',
            password='123'
        ), follow_redirects=True)
        data = response.get_data(as_text=True)
        self.assertNotIn('Login Success', data)
        self.assertIn('Invalid username or password', data)

        response = self.client.post('/login', data=dict(
            username='',
            password='123'
        ), follow_redirects=True)
        data = response.get_data(as_text=True)
        self.assertNotIn('Login success', data)
        self.assertIn('Invalid input', data)

        response = self.client.post('/login', data=dict(
            username='test',
            password=''
        ), follow_redirects=True)
        data = response.get_data(as_text=True)
        self.assertNotIn('Login Success', data)
        self.assertIn('Invalid input', data)

    def test_logout(self):
        self.login()

        response = self.client.get('/logout', follow_redirects=True)
        data = response.get_data(as_text=True)
        self.assertIn('Bye', data)
        self.assertNotIn('Logout', data)
        self.assertNotIn('Settings', data)
        self.assertNotIn('Delete', data)
        self.assertNotIn('Edit', data)
        self.assertNotIn('<form method="post">', data)

    def test_settings(self):
        self.login()

        response = self.client.get('/settings')
        data = response.get_data(as_text=True)
        self.assertIn('Setting', data)
        self.assertIn('Name', data)

        response = self.client.post('/settings', data=dict(
            name='',
        ), follow_redirects=True)
        data = response.get_data(as_text=True)
        self.assertNotIn('Setting', data)
        self.assertIn('Invalid Name', data)

        response = self.client.post('/settings', data=dict(
            name='Grey Li',
        ), follow_redirects=True)
        data = response.get_data(as_text=True)
        self.assertIn('Setting', data)
        self.assertIn('Grey Li', data)

    def test_create_item(self):
        self.login()

        response = self.client.post('/', data=dict(
            title='New Movie',
            year='2019'
        ), follow_redirects=True)
        data = response.get_data(as_text=True)
        self.assertIn('New Item Added', data)
        self.assertIn('New Movie', data)

        response = self.client.post('/', data=dict(
            title='',
            year='2019'
        ), follow_redirects=True)
        data = response.get_data(as_text=True)
        self.assertNotIn('New Item Added', data)
        self.assertIn('Invalid input', data)

        response = self.client.post('/', data=dict(
            title='bacde',
            year=''
        ), follow_redirects=True)
        data = response.get_data(as_text=True)
        self.assertNotIn('New Item Added', data)
        self.assertIn('Invalid input', data)

    def test_update_item(self):
        self.login()

        response = self.client.get('/movie/edit/1')
        data = response.get_data(as_text=True)
        self.assertIn('Edit item', data)
        self.assertIn('New Movie', data)
        self.assertIn('2019', data)

        response = self.client.post('/movie/edit/1', data=dict(
            title='New Movie Edit',
            year='2020'
        ), follow_redirects=True)
        data = response.get_data(as_text=True)
        # self.assertIn('Item updated.', data)
        self.assertIn('New Movie Edit', data)

        response = self.client.post('/movie/edit/1', data=dict(
            title='',
            year='2020'
        ), follow_redirects=True)
        data = response.get_data(as_text=True)
        # self.assertNotIn('Item updated.', data)
        self.assertIn('Invalid input.', data)

        response = self.client.post('/movie/edit/1', data=dict(
            title='abcdefggggg',
            year=''
        ), follow_redirects=True)
        data = response.get_data(as_text=True)
        # self.assertNotIn('Item updated.', data)
        # self.assertNotIn('New Movie Edited Again', data)
        self.assertIn('Invalid input.', data)

    def test_delete_item(self):
        self.login()

        response = self.client.post('/movie/delete/1', follow_redirects=True)
        data = response.get_data(as_text=True)
        self.assertIn('Delete Item', data)
        self.assertNotIn('Test Title', data)

    def test_forge_command(self):
        result = self.runner.invoke(forge)
        self.assertIn('Insert Done!', result.output)
        self.assertNotEqual(Movie.query.count(), 0)

    def test_initdb_command(self):
        result = self.runner.invoke(initdb)
        self.assertIn('Initialized database.', result.output)

    def test_admin_command(self):
        db.drop_all()
        db.create_all()
        result = self.runner.invoke(args=['admin', '--username', 'bzh', '--password', '123456'])
        self.assertIn('Creating user ...', result.output)
        self.assertIn('Done!', result.output)
        self.assertEqual(User.query.count(), 1)
        self.assertEqual(User.query.first().username, 'bzh')
        self.assertTrue(User.query.first().validate_password('123456'))

    def test_admin_command_update(self):
        result = self.runner.invoke(args=['admin', '--username', 'ty', '--password', '9999'])
        self.assertIn('Renaming user ...', result.output)
        self.assertIn('Done!', result.output)
        self.assertEqual(User.query.count(), 1)
        self.assertEqual(User.query.first().username, 'ty')
        self.assertTrue(User.query.first().validate_password('9999'))


if __name__ == '__main__':
    unittest.main()