"""Run the actual resolver monitor/handoff methods with simulated Kodi events."""
import ast
import json
from pathlib import Path
import types
import unittest
import zipfile
from unittest.mock import Mock

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / '_local/source/plugin.video.otaku/resources/lib/windows/resolver.py'
if SOURCE.exists():
    RESOLVER_SOURCE = SOURCE.read_text()
else:
    with zipfile.ZipFile(ROOT / 'kodi/plugin.video.otaku/plugin.video.otaku-5.3.3+bugz.3.zip') as archive:
        RESOLVER_SOURCE = archive.read('plugin.video.otaku/resources/lib/windows/resolver.py').decode()


class StartupDelayTests(unittest.TestCase):
    def setUp(self):
        self.now = 0.0
        self.speed = 1
        self.file = 'https://video.example/master.m3u8'
        self.active = True
        self.abort = False
        self.calls = []
        self.instances = []
        test = self
        class KodiMonitor:
            def __init__(self):
                test.instances.append(self)
            def abortRequested(self):
                return test.abort
            def waitForAbort(self, seconds):
                test.now += seconds
                return test.abort
        class KodiPlayer:
            def getPlayingFile(self):
                return test.file
            def isPlayingVideo(self):
                return test.active
            def play(self, *args):
                test.instances[-1].onNotification('xbmc', 'Player.OnAVStart', json.dumps({'player': {'playerid': 1}}))
        def rpc(request):
            if request['method'] == 'Player.PlayPause':
                test.calls.append((test.now, request['params']['play']))
                test.speed = 1 if request['params']['play'] else 0
            return {'result': {'speed': test.speed}}
        self.control = types.SimpleNamespace(jsonrpc=Mock(side_effect=rpc), log=Mock(), ADDON_ID='plugin.video.otaku', HANDLE=1,
            playList=types.SimpleNamespace(size=lambda: 1, clear=Mock(), add=Mock()), set_videotags=Mock())
        self.xbmc = types.SimpleNamespace(Monitor=KodiMonitor, Player=KodiPlayer, getInfoLabel=lambda key: self.control.ADDON_ID)
        tree = ast.parse(RESOLVER_SOURCE)
        monitor = next(n for n in tree.body if isinstance(n, ast.ClassDef) and n.name == 'Monitor')
        resolver = next(n for n in tree.body if isinstance(n, ast.ClassDef) and n.name == 'Resolver')
        method = next(n for n in resolver.body if isinstance(n, ast.FunctionDef) and n.name == '_handle_playback')
        def resolve_url(handle, success, item):
            if success:
                self.instances[-1].onNotification('xbmc', 'Player.OnAVStart', json.dumps({'player': {'playerid': 1}}))
        self.namespace = dict(xbmc=self.xbmc, json=json, time=types.SimpleNamespace(monotonic=lambda: self.now), control=self.control,
            xbmcplugin=types.SimpleNamespace(setResolvedUrl=Mock(side_effect=resolve_url)),
            xbmcgui=types.SimpleNamespace(ListItem=lambda **kwargs: types.SimpleNamespace(getPath=lambda: kwargs['path'], setArt=Mock())),
            player=types.SimpleNamespace(WatchlistPlayer=lambda: types.SimpleNamespace(handle_player=Mock())), watchlist_update_episode=Mock())
        exec(compile(ast.Module(body=[monitor, method], type_ignores=[]), str(SOURCE), 'exec'), self.namespace)
        self.Monitor = self.namespace['Monitor']

    def started(self):
        monitor = self.Monitor()
        monitor.onNotification('xbmc', 'Player.OnAVStart', json.dumps({'player': {'playerid': 1}}))
        return monitor

    def test_holds_loaded_video_for_three_seconds(self):
        m = self.started()
        self.assertEqual(self.calls, [(0.0, False)])
        self.now = 2.99
        m.advance_startup()
        self.assertEqual(len(self.calls), 1)
        self.now = 3.0
        m.advance_startup()
        self.assertEqual(self.calls, [(0.0, False), (3.0, True)])
        self.assertTrue(m.playing)
        m.advance_startup()
        self.assertEqual(len(self.calls), 2)

    def test_duplicate_av_events_do_not_extend_delay_or_toggle(self):
        m = self.started()
        self.now = 2.0
        m.onNotification('xbmc', 'Player.OnAVStart', json.dumps({'player': {'playerid': 1}}))
        self.now = 3.0
        m.advance_startup()
        self.assertEqual(self.calls, [(0.0, False), (3.0, True)])

    def test_stop_and_shutdown_do_not_resume(self):
        for shutdown in (False, True):
            with self.subTest(shutdown=shutdown):
                self.calls.clear();self.now=0;self.abort=False
                m = self.started()
                if shutdown:self.abort=True
                else:m.onNotification('xbmc', 'Player.OnStop', '{}')
                self.now=3;m.advance_startup()
                self.assertEqual(self.calls, [(0.0, False)])

    def test_replaced_media_is_not_resumed(self):
        m = self.started();self.file = 'another video';self.now=3
        m.advance_startup()
        self.assertEqual(self.calls, [(0.0, False)])
        self.assertTrue(m.playbackerror)

    def test_manual_early_resume_is_respected(self):
        m = self.started();self.now=1;self.speed=1
        m.onNotification('xbmc', 'Player.OnPlay', json.dumps({'player': {'playerid': 1, 'speed': 1}}))
        self.now=3;m.advance_startup()
        self.assertTrue(m.playing)
        self.assertEqual(self.calls, [(0.0, False)])

    def test_audio_notification_is_ignored(self):
        m=self.Monitor();m.onNotification('xbmc', 'Player.OnAVStart', json.dumps({'player': {'playerid': 0}}))
        self.assertEqual(self.calls, [])
        self.assertFalse(m.playing)

    def test_both_actual_handoffs_capture_initial_event_and_wait(self):
        for context in (False, True):
            with self.subTest(context=context):
                self.calls.clear();self.now=0;self.speed=1
                resolver=types.SimpleNamespace(source_select_close=None, return_data={'linkinfo': {'url': self.file},
                    'source': {'type': 'direct', 'provider': 'animepahe'}}, params={}, image={}, context=context,
                    _build_art_dict=lambda **kw: {}, abort=False, close=Mock(), mal_id=1, episode=1, resume=0)
                self.namespace['_handle_playback'](resolver)
                self.assertFalse(resolver.abort)
                self.assertEqual(self.calls[0], (0.0, False))
                self.assertGreaterEqual(self.calls[-1][0], 3.0)
                self.assertLess(self.calls[-1][0], 3.11)
                self.assertTrue(self.calls[-1][1])


if __name__ == '__main__':
    unittest.main()
