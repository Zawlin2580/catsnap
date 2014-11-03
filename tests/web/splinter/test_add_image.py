from __future__ import unicode_literals

from selenium.webdriver.common.keys import Keys
from time import sleep
from tests import with_settings
from tests.image_helper import SOME_GIF
from tests.web.splinter import TestCase, logged_in
from catsnap import Client
from catsnap.table.image import Image
from catsnap.table.album import Album
from catsnap.table.image_tag import ImageTag
from mock import patch, Mock
from nose.tools import eq_, nottest


class UploadTestCase(TestCase):
    @nottest
    @patch('catsnap.web.controllers.image.ImageTruck')
    def upload_one_image(self, ImageTruck):
        ImageTruck.new_from_url.return_value = self.mock_truck()

        self.visit_url('/add')
        self.browser.click_link_by_text('From Url')
        url_field = self.browser.find_by_css('input[name="url"]')
        url_field.fill('http://cdn.mlkshk.com/r/118S7')
        self.browser.find_by_css('input[name="url-submit"]').click()

    @nottest
    def mock_truck(self):
        truck = Mock()
        with open(SOME_GIF, 'r') as fh:
            truck.contents = fh.read()
        truck.url.return_value = 'https://catsnap.cdn/ca7face'
        truck.filename = 'ca7face'
        truck.content_type = 'image/gif'
        return truck


class TestUploadImage(UploadTestCase):
    @logged_in
    @with_settings(bucket='frootypoo')
    def test_try_to_add_a_bad_url(self):
        self.visit_url('/add')
        self.browser.click_link_by_text('From Url')
        url_field = self.browser.find_by_css('input[name="url"]')
        assert url_field, "Didn't find the url input"
        url_field.fill('http://example.com/images/example_image_4.jpg')
        self.browser.find_by_css('input[name="url-submit"]').click()

        assert self.browser.is_text_present('That url is no good'), \
            "Didn't see a user-facing error message!"

    @logged_in
    @with_settings(bucket='frootypoo')
    def test_errors_clear_previous_errors(self):
        self.visit_url('/add')
        self.browser.click_link_by_text('From Url')

        submit_button = self.browser.find_by_css('input[name="url-submit"]')
        submit_button.click()
        assert self.browser.is_text_present(
                'Please submit either a file or a url.'), \
            "Didn't see a user-facing error message!"

        url_field = self.browser.find_by_css('input[name="url"]')
        assert url_field, "Didn't find the url input"
        url_field.fill('SOMETHING INVALID')
        submit_button.click()

        assert self.browser.is_text_present('That url is no good'), \
            "Didn't see a user-facing error message!"
        assert not self.browser.is_text_present('submit either a file'), \
            "The old error wasn't cleared!"

    @logged_in
    @with_settings(bucket='frootypoo')
    @patch('catsnap.web.controllers.image.ImageTruck')
    def test_successes_clear_previous_errors(self, ImageTruck):
        ImageTruck.new_from_url.return_value = self.mock_truck()
        self.visit_url('/add')
        self.browser.click_link_by_text('From Url')

        submit_button = self.browser.find_by_css('input[name="url-submit"]')
        submit_button.click()
        assert self.browser.is_text_present(
                'Please submit either a file or a url.'), \
            "Didn't see a user-facing error message!"

        url_field = self.browser.find_by_css('input[name="url"]')
        assert url_field, "Didn't find the url input"
        url_field.fill('http://cdn.mlkshk.com/r/110WR')
        submit_button.click()

        assert not self.browser.is_text_present('submit either a file'), \
            "The old error wasn't cleared!"

    @logged_in
    @with_settings(bucket='frootypoo')
    @patch('catsnap.web.controllers.image.ImageTruck')
    def test_add_by_url(self, ImageTruck):
        ImageTruck.new_from_url.return_value = self.mock_truck()

        self.visit_url('/add')
        self.browser.click_link_by_text('From Url')

        url_field = self.browser.find_by_css('input[name="url"]')
        assert url_field, "Didn't find the url input"
        assert url_field.first.visible, "The url input isn't visible"
        url_field.fill('http://cdn.mlkshk.com/r/111DS')
        self.browser.find_by_css('input[name="url-submit"]').click()

        img = self.browser.find_by_css('img')[0]
        eq_(img['src'], 'http://localhost:65432/public/img/large-throbber.gif')

        url_field = self.browser.find_by_css('input[name="url"]')
        assert url_field, "The page didn't create a new url input"
        assert url_field.first.visible, "The new url input isn't visible"

    @logged_in
    @with_settings(bucket='frootypoo')
    def test_add_by_file(self):
        self.visit_url('/add')

        file_field = self.browser.find_by_css('input[name="file"]').first
        file_label = self.browser.find_by_css('label[for="file"]').first
        assert file_field, "Didn't find the file input"
        assert not file_field.visible, "The file input is visible"
        assert file_label, "Didn't find a label for the file input"
        assert file_label.visible, "The file label isn't visible"
        self.browser.execute_script('''
            $('input[type="file"]').css({'opacity': 100});
        ''') # selenium won't interact with invisible objects. Ridiculous!
        assert file_field.visible, "The file input didn't become visible!"

        self.browser.attach_file('file', SOME_GIF)
        self.browser.find_by_css('input[name="file-submit"]').click()

        img = self.browser.find_by_css('img')[0]
        eq_(img['src'], 'http://localhost:65432/public/img/large-throbber.gif')

        file_field = self.browser.find_by_css('input[name="file"]')
        file_label = self.browser.find_by_css('label[for="file"]')
        assert file_field, "The page didn't create a new upload form"

    @logged_in
    @with_settings(bucket='frootypoo')
    def test_file_labels_track_the_input_value(self):
        self.visit_url('/add')

        file_field = self.browser.find_by_css('input[name="file"]').first
        file_label = self.browser.find_by_css('label[for="file"]').first
        assert file_field, "Didn't find the file input"
        assert file_label, "Didn't find a label for the file input"
        self.browser.execute_script('''
            $('input[type="file"]').css({'opacity': 100});
        ''') # selenium won't interact with invisible objects. Ridiculous!
        assert file_field.visible, "The file input didn't become visible!"

        self.browser.attach_file('file', '/path/to/image.jpg')

        eq_(file_label.text, 'image.jpg')

class TestAlbumFunctions(UploadTestCase):
    @logged_in
    @with_settings(bucket='frootypoo')
    @patch('catsnap.web.controllers.image.ImageTruck')
    def test_upload_to_an_album(self, ImageTruck):
        ImageTruck.new_from_url.return_value = self.mock_truck()
        session = Client().session()
        album = Album(name='fotoz')
        session.add(album)
        session.flush()

        self.visit_url('/add')
        album_select = self.browser.find_by_name('album')
        album_select.select(str(album.album_id))

        self.browser.click_link_by_text('From Url')
        url_field = self.browser.find_by_css('input[name="url"]')
        url_field.fill('http://cdn.mlkshk.com/r/111V1')
        self.browser.find_by_css('input[name="url-submit"]').click()

        # force a wait for the upload response
        self.browser.find_by_css('textarea')

        image = session.query(Image).one()
        eq_(image.album_id, album.album_id)


class TestAddTagsAfterUpload(UploadTestCase):
    @logged_in
    @with_settings(bucket='frootypoo')
    def test_tab_from_tag_input_focuses_descr_and_saves(self):
        self.upload_one_image()
        self.browser.click_link_by_text('Add tag')
        self.browser.find_by_name('tag').first.fill('cute\t')
        # there is no .is_focused or anything, so we'll do it inside-out:
        # look for a focused textarea and assert that it's the right one.
        description = self.browser.find_by_css('textarea:focus').first
        eq_(description['name'], "description", "wrong textarea was focused")

        session = Client().session()
        image = session.query(Image).one()
        eq_(list(image.get_tags()), ["cute"])

        assert self.browser.find_link_by_text('Add tag').first, \
            "A new add-tag link wasn't appended!"

    @logged_in
    @with_settings(bucket='frootypoo')
    def test_enter_from_tag_input_focuses_next_tag_input_and_saves(self):
        self.upload_one_image()
        self.browser.click_link_by_text('Add tag')
        self.browser.find_by_name('tag').first.fill('chipmunk\n')
        # wait for the submit event to happen. Normally Selenium handles the
        # wait for us when we seek a focused input, but since the in-progress
        # input has focus until the new one is ready, that doesn't work.
        sleep(0.25)
        # there is no .is_focused or anything, so we'll do it inside-out:
        # look for a focused input and assert that it's the right one.
        next_tag = self.browser.find_by_css('input:focus').first
        eq_(next_tag['name'], "tag", "wrong input was focused")

        session = Client().session()
        image = session.query(Image).one()
        eq_(list(image.get_tags()), ["chipmunk"])

    @logged_in
    @with_settings(bucket='frootypoo')
    def test_escape_from_tag_input_cancels_tag_editing(self):
        self.upload_one_image()
        self.browser.click_link_by_text('Add tag')
        tag_input = self.browser.find_by_name('tag').first
        tag_input.fill('flerp')
        tag_input.fill(Keys.ESCAPE)

        assert self.browser.is_element_not_present_by_name('tag'), \
            "the tag-name input wasn't cleared!"
        assert self.browser.find_link_by_text('Add tag').first, \
            "The add-tag link wasn't put back in!"

        tags = Client().session().query(ImageTag).all()
        eq_(tags, [])

    @logged_in
    @with_settings(bucket='frootypoo')
    def test_empty_tags_are_not_saved(self):
        self.upload_one_image()
        self.browser.click_link_by_text('Add tag')
        tag_input = self.browser.find_by_name('tag').first
        tag_input.fill(' \n')
        sleep(0.25)

        assert self.browser.is_element_not_present_by_name('tag'), \
            "the tag-name input wasn't cleared!"
        assert self.browser.find_link_by_text('Add tag').first, \
            "The add-tag link wasn't put back in!"

        tags = Client().session().query(ImageTag).all()
        eq_(tags, [])

class TestEditAttributes(UploadTestCase):
    @logged_in
    @with_settings(bucket='frootypoo')
    def test_submit_title(self):
        self.upload_one_image()
        title_input = self.browser.find_by_name('title').first
        title_input.fill('Tiny chipmunk dancing\n')

        image = Client().session().query(Image).one()
        eq_(image.title, "Tiny chipmunk dancing")

    @logged_in
    @with_settings(bucket='frootypoo')
    def test_submit_description(self):
        self.upload_one_image()
        description_input = self.browser.find_by_name('description').first
        description_input.fill('A chipmunk dances.\nIt dances its heart out')
        self.browser.find_by_name('save').click()

        image = Client().session().query(Image).one()
        eq_(image.description, "A chipmunk dances.\nIt dances its heart out")

    @logged_in
    @with_settings(bucket='frootypoo')
    def test_blurring_inputs_submits_changes(self):
        self.upload_one_image()
        description_input = self.browser.find_by_name('description').first
        description_input.fill('A chipmunk dances.\nIt dances its heart out')
        title_input = self.browser.find_by_name('title').first
        title_input.fill('Tiny chipmunk dancing')

        self.browser.click_link_by_text('From File')

        image = Client().session().query(Image).one()
        eq_(image.title, "Tiny chipmunk dancing")
        eq_(image.description, "A chipmunk dances.\nIt dances its heart out")
