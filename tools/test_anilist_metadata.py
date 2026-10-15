"""Exercise public metadata recovery and the real show-opening failure path."""
import ast
import importlib.util
import json
import pickle
from pathlib import Path
import sys
import tempfile
import types
import unittest
from unittest.mock import Mock, patch
import zipfile

ROOT = Path(__file__).resolve().parents[1]
PREFIX = 'plugin.video.otaku/resources/lib/'


def source(name):
    path = ROOT / '_local/source' / PREFIX / name
    if path.exists():
        return path.read_text()
    with zipfile.ZipFile(ROOT / 'kodi/plugin.video.otaku/plugin.video.otaku-5.3.3+bugz.3.zip') as archive:
        return archive.read(PREFIX + name).decode()


class Response:
    def __init__(self, status=200, payload=None, text=None, headers=None):
        self.status_code = status
        self.payload = payload if payload is not None else {'data': {'Media': {'id': 123, 'idMal': 59597}}}
        self.text = text if text is not None else json.dumps(self.payload)
        self.headers = headers or {'Content-Type': 'application/json'}
    def json(self):
        return json.loads(self.text)


class MetadataTests(unittest.TestCase):
    def setUp(self):
        directory = tempfile.TemporaryDirectory(prefix='otaku-anilist-test-')
        self.addCleanup(directory.cleanup)
        self.waits = []
        self.aborting = False
        self.abort_on_wait = False
        test = self
        class Monitor:
            def abortRequested(self):
                return test.aborting
            def waitForAbort(self, seconds):
                test.waits.append(seconds)
                return test.abort_on_wait
        self.control = types.SimpleNamespace(dataPath=directory.name, ADDON_NAME='Otaku', log=Mock(),
                                            notify=Mock(), draw_items=Mock())
        self.client = types.SimpleNamespace(post=Mock(return_value=Response()))
        modules = {name: types.ModuleType(name) for name in ('resources', 'resources.lib', 'resources.lib.ui')}
        modules['resources.lib.ui'].control = self.control
        modules['resources.lib.ui'].client = self.client
        modules['xbmc'] = types.SimpleNamespace(Monitor=Monitor)
        self.patcher = patch.dict(sys.modules, modules)
        self.patcher.start();self.addCleanup(self.patcher.stop)
        self.api = types.ModuleType('api_under_test')
        exec(compile(source('ui/anilist_metadata.py'), 'anilist_metadata.py', 'exec'), self.api.__dict__)
        self.variables = {'idMal': '59597', 'type': 'ANIME'}

    def fetch(self):
        return self.api.fetch_media('query { Media { idMal } }', self.variables)

    def test_success_is_single_request(self):
        self.assertEqual(self.fetch()['idMal'], 59597)
        self.assertEqual(self.client.post.call_count, 1)
        self.assertEqual(self.waits, [])
        self.assertEqual(self.client.post.call_args.kwargs['headers']['Accept'], 'application/json')

    def test_html_response_retries_and_recovers(self):
        self.client.post.side_effect = [Response(text='<html>temporary outage</html>',headers={'Content-Type':'text/html'}),Response()]
        self.assertEqual(self.fetch()['idMal'], 59597)
        self.assertEqual(self.waits, [1])
        record = json.loads((Path(self.control.dataPath) / 'anilist-metadata.log').read_text().splitlines()[0])
        self.assertEqual(record['status'], 200)
        self.assertEqual(record['content_type'], 'text/html')
        self.assertIn('temporary outage', record['body_prefix'])
        self.assertEqual(record['mal_id'], '59597')

    def test_empty_response_stops_after_three_attempts(self):
        self.client.post.return_value = Response(status=0,text='')
        self.assertIsNone(self.fetch())
        self.assertEqual(self.client.post.call_count, 3)
        self.assertEqual(self.waits, [1,2])

    def test_timeout_can_recover(self):
        self.client.post.side_effect = [TimeoutError(),Response()]
        self.assertEqual(self.fetch()['idMal'], 59597)
        self.assertEqual(self.waits, [1])

    def test_retry_after_short_delay_is_honored(self):
        self.client.post.side_effect = [Response(status=503,headers={'Retry-After':'1.5'}),Response()]
        self.assertEqual(self.fetch()['idMal'],59597)
        self.assertEqual(self.waits,[1.5])

    def test_long_rate_limit_does_not_hammer_server(self):
        self.client.post.return_value = Response(status=429,headers={'Retry-After':'60'})
        self.assertIsNone(self.fetch())
        self.assertEqual(self.client.post.call_count,1)
        self.assertEqual(self.waits,[])

    def test_permanent_http_failure_does_not_retry(self):
        self.client.post.return_value=Response(status=403,text='forbidden')
        self.assertIsNone(self.fetch())
        self.assertEqual(self.client.post.call_count,1)

    def test_invalid_json_shape_is_bounded(self):
        self.client.post.return_value=Response(payload=['not an object'])
        self.assertIsNone(self.fetch())
        self.assertEqual(self.client.post.call_count,3)

    def test_graphql_error_is_not_treated_as_media(self):
        self.client.post.return_value=Response(payload={'errors':[{'message':'Not found','status':404}]})
        self.assertIsNone(self.fetch())
        self.assertEqual(self.client.post.call_count,1)

    def test_missing_media_is_not_success(self):
        self.client.post.return_value=Response(payload={'data':{'Media':None}})
        self.assertIsNone(self.fetch())
        self.assertEqual(self.client.post.call_count,1)

    def test_abort_cancels_retry(self):
        self.client.post.return_value=Response(text='invalid')
        self.abort_on_wait=True
        self.assertIsNone(self.fetch())
        self.assertEqual(self.client.post.call_count,1)

    def test_shutdown_before_request_makes_no_call(self):
        self.aborting=True
        self.assertIsNone(self.fetch())
        self.client.post.assert_not_called()

    def test_failed_log_write_does_not_break_recovery(self):
        file=Path(self.control.dataPath)/'file';file.write_text('test');self.control.dataPath=str(file)
        self.client.post.side_effect=[Response(text='invalid'),Response()]
        self.assertEqual(self.fetch()['idMal'],59597)

    def browser_method(self, method):
        cls=next(n for n in ast.parse(source('AniListBrowser.py')).body if isinstance(n,ast.ClassDef) and n.name=='AniListBrowser')
        return next(n for n in cls.body if isinstance(n,ast.FunctionDef) and n.name==method)

    def test_real_metadata_method_uses_recovery_helper(self):
        namespace={'fetch_media':Mock(return_value={'idMal':59597})}
        node=self.browser_method('get_anilist_res')
        exec(compile(ast.Module(body=[node],type_ignores=[]),'real AniList method','exec'),namespace)
        self.assertEqual(namespace['get_anilist_res'](object(),self.variables),{'idMal':59597})
        namespace['fetch_media'].assert_called_once()

    def test_real_browser_failure_uses_cached_show(self):
        cached={'kodi_meta':b'existing'}
        database=types.SimpleNamespace(get=Mock(return_value=None),get_show=Mock(return_value=cached))
        namespace={'database':database,'control':self.control}
        exec(compile(ast.Module(body=[self.browser_method('get_anime')],type_ignores=[]),'real get_anime','exec'),namespace)
        browser=types.SimpleNamespace(get_anilist_res=Mock(),process_res=Mock())
        self.assertEqual(namespace['get_anime'](browser,'59597'),cached)
        browser.process_res.assert_not_called();self.control.notify.assert_not_called()

    def test_real_browser_failure_without_cache_notifies_once(self):
        database=types.SimpleNamespace(get=Mock(return_value=None),get_show=Mock(return_value=None))
        namespace={'database':database,'control':self.control}
        exec(compile(ast.Module(body=[self.browser_method('get_anime')],type_ignores=[]),'real get_anime','exec'),namespace)
        browser=types.SimpleNamespace(get_anilist_res=Mock(),process_res=Mock())
        self.assertIsNone(namespace['get_anime'](browser,'59597'))
        browser.process_res.assert_not_called();self.control.notify.assert_called_once()

    def test_actual_show_route_does_not_write_progress_on_metadata_failure(self):
        tree=ast.parse(source('WatchlistIntegration.py'))
        route=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='WATCHLIST_TO_EP')
        route.decorator_list=[]
        database=types.SimpleNamespace(get_show=Mock(return_value=None),update_kodi_meta=Mock())
        browser=types.SimpleNamespace(get_anime=Mock(return_value=None))
        namespace={'database':database,'BROWSER':browser,'control':self.control}
        exec(compile(ast.Module(body=[route],type_ignores=[]),'real watchlist route','exec'),namespace)
        namespace['WATCHLIST_TO_EP']('59597/3',{})
        database.update_kodi_meta.assert_not_called()
        self.control.draw_items.assert_called_once_with([],'episodes')

    def test_successful_show_route_preserves_existing_progress_behavior(self):
        tree=ast.parse(source('WatchlistIntegration.py'))
        route=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='WATCHLIST_TO_EP')
        route.decorator_list=[]
        cached={'kodi_meta':pickle.dumps({'name':'Test show','eps_watched':'0'})}
        database=types.SimpleNamespace(get_show=Mock(return_value=cached),update_kodi_meta=Mock())
        browser=types.SimpleNamespace(get_anime=Mock())
        metadata=types.SimpleNamespace(get_anime_init=Mock(return_value=(['episode'],'episodes')))
        namespace={'database':database,'BROWSER':browser,'control':self.control,'pickle':pickle,'MetaBrowser':metadata}
        exec(compile(ast.Module(body=[route],type_ignores=[]),'real watchlist route','exec'),namespace)
        namespace['WATCHLIST_TO_EP']('59597/3',{})
        database.update_kodi_meta.assert_called_once_with('59597',{'name':'Test show','eps_watched':'3'})
        browser.get_anime.assert_not_called()
        self.control.draw_items.assert_called_once_with(['episode'],'episodes')


if __name__=='__main__':
    unittest.main()
