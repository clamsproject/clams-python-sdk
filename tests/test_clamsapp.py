import json
import os
import tempfile
import unittest
from typing import Union

import jsonschema
from mmif import Mmif, Document, DocumentTypes, AnnotationTypes

import clams.app
import clams.restify
from clams.appmetadata import AppMetadata, Input, Output

AT_TYPE = AnnotationTypes.TimeFrame


class ExampleInputMMIF(object):
    EXAMPLE_TEXT = 'this is a temp file.'

    @staticmethod
    def get_rawmmif() -> Mmif:
        mmif = Mmif(validate=False, frozen=False)

        vdoc = Document({'@type': DocumentTypes.VideoDocument.value,
                         'properties':
                             {'id': 'v1', 'location': "/dummy/dir/dummy.file.mp4"}})
        mmif.add_document(vdoc)

        idoc: Document = Document({'@type': DocumentTypes.ImageDocument})
        idoc.id = 'i1'
        idoc.location = os.path.join(os.path.dirname(__file__), 'pillow-logo.png')
        mmif.add_document(idoc)

        t = tempfile.NamedTemporaryFile(delete=False)
        with open(t.name, 'w') as t_f:
            t_f.write(ExampleInputMMIF.EXAMPLE_TEXT)
        tdoc: Document = Document({'@type': DocumentTypes.TextDocument})
        tdoc.location = t.name
        tdoc.id = 't1'
        mmif.add_document(tdoc)

        return mmif

    @staticmethod
    def get_mmif() -> str:
        return ExampleInputMMIF.get_rawmmif().serialize()


class TestSerialization(unittest.TestCase):

    def setUp(self):
        self.mmif = Mmif(ExampleInputMMIF.get_mmif())

    def test_view_is_empty(self):
        self.assertEqual(len(self.mmif.views), 0)


class ExampleClamsApp(clams.app.ClamsApp):

    def _appmetadata(self) -> Union[dict, AppMetadata]:
        pass
    
    def _input_spec(self):
        return []
        
    def _output_spec(self):
        return [Output(at_type=AT_TYPE.value)]

    def _annotate(self, mmif):
        if type(mmif) is not Mmif:
            mmif = Mmif(mmif, validate=False)
        new_view = mmif.new_view()
        new_view.new_contain(AT_TYPE, {"producer": "dummy-producer"})
        ann = new_view.new_annotation('a1', AT_TYPE)
        ann.add_property("f1", "hello_world")
        return mmif


class TestClamsApp(unittest.TestCase):
    
    def setUp(self):
        self.exampleappversion = '0.0.1'
        self.exampleappmetadata = AppMetadata(
            name="Example CLAMS App for testing",
            description="This app doesn't do anything",
            app_version=self.exampleappversion,
            license="MIT",
            url=f"https://apps.clams.ai/example/{self.exampleappversion}",
            input=[],
            output=[]
        )
        self.appmetadataschema = json.loads(AppMetadata.schema_json())
        self.app = ExampleClamsApp()
        self.in_mmif = ExampleInputMMIF.get_mmif()

    def test_jsonschema_export(self):
        # TODO (krim @ 4/20/21): there may be a better test for this...
        self.assertIsNotNone(self.appmetadataschema)

    def test_appmetadata(self):
        # from AppMetadata class
        self.app.metadata = self.exampleappmetadata
        metadata = json.loads(self.app.appmetadata(pretty=True))
        jsonschema.validate(metadata, self.appmetadataschema)
        print(self.app.appmetadata(pretty=True))
        
    def test_annotate(self):
        out_mmif = self.app.annotate(self.in_mmif)
        # TODO (krim @ 9/3/19): more robust test cases
        self.assertIsNotNone(out_mmif)

    def test_open_document_location(self):
        mmif = ExampleInputMMIF.get_rawmmif()
        with self.app.open_document_location(mmif.documents['t1']) as f:
            self.assertEqual(f.read(), ExampleInputMMIF.EXAMPLE_TEXT)

    def test_open_document_location_custom_opener(self):
        from PIL import Image
        mmif = ExampleInputMMIF.get_rawmmif()
        with self.app.open_document_location(mmif.documents['i1'], Image.open) as f:
            self.assertEqual(f.size, (200, 71))


class TestRestifier(unittest.TestCase):

    def setUp(self):
        self.app = clams.Restifier(ExampleClamsApp()).test_client()

    def test_can_get(self):
        gotten = self.app.get('/')
        print(gotten.get_data(as_text=True))
        self.assertIsNotNone(gotten)
        gotten = self.app.get('/', query_string={'pretty': 'true'})
        print(gotten.get_data(as_text=True))
        self.assertIsNotNone(gotten)

    def test_can_post(self):
        posted = self.app.post('/', data=ExampleInputMMIF.get_mmif())
        print(posted.get_data(as_text=True))
        self.assertIsNotNone(posted)

    def test_can_put(self):
        put = self.app.put('/', data=ExampleInputMMIF.get_mmif())
        print(put.get_data(as_text=True))
        self.assertIsNotNone(put)

    def test_can_put_as_json(self):
        put = self.app.put('/', data=ExampleInputMMIF.get_mmif(), headers={"Content-Type": "Application/json"})
        self.assertIsNotNone(put)
        self.assertEqual(put.status_code, 200)
        self.assertIsNotNone(Mmif(put.get_data(as_text=True)))

    def test_can_pass_params(self):
        mmif = ExampleInputMMIF.get_mmif()
        headers = {"Content-Type": "Application/json"}
        query_string = {'pretty': True}
        pretty_res = self.app.put('/', data=mmif, headers=headers, query_string=query_string)
        self.assertEqual(pretty_res.status_code, 200, pretty_res.get_data(as_text=True))
        self.assertIsNotNone(Mmif(pretty_res.get_data(as_text=True)))
        pretty_to_mmif = Mmif(pretty_res.get_data(as_text=True))
        unpretty_res = self.app.put('/', data=mmif, headers=headers)
        unpretty_to_mmif = Mmif(unpretty_res.get_data(as_text=True))
        self.assertIsNotNone(pretty_to_mmif)
        self.assertIsNotNone(unpretty_to_mmif)
        # TODO (krim @ 12/17/20): __eq__() is not working as expected, possibly realted to https://github.com/clamsproject/mmif/issues/131
        # self.assertEqual(pretty_to_mmif, unpretty_to_mmif)

        # this should raise TypeError because the ExampleClamsApp._annotate() doesn't take kwargs at all
        query_string = {'pretty': True, 'random': 'random'}
        res = self.app.put('/', data=mmif, headers=headers, query_string=query_string)
        self.assertEqual(res.status_code, 415, res.get_data(as_text=True))


if __name__ == '__main__':
    unittest.main()
