"""
Spotify Controller
Handles Spotify playback, track navigation, searching, adding songs to playlists, and creating playlists.
Supports both Spotify Web API (spotipy) and local desktop (MPRIS/dbus/playerctl/URI) controls.
"""

import os
import json
import subprocess
import urllib.parse
from typing import Tuple, Dict, Any, Optional, List
from pathlib import Path

try:
    import spotipy
    from spotipy.oauth2 import SpotifyOAuth
    SPOTIPY_AVAILABLE = True
except ImportError:
    SPOTIPY_AVAILABLE = False


class SpotifyController:
    def __init__(self):
        """Initialize Spotify Controller"""
        self.sp = None
        self.playlists_file = Path.home() / ".config" / "voice_assistant" / "local_playlists.json"
        self._init_spotify_api()
        self._init_local_playlists()

    def _init_spotify_api(self):
        """Initialize Spotipy client if credentials are present"""
        if not SPOTIPY_AVAILABLE:
            print("ℹ Spotipy library not available. Using desktop MPRIS/URI controls.")
            return

        client_id = os.environ.get("SPOTIPY_CLIENT_ID") or os.environ.get("SPOTIFY_CLIENT_ID")
        client_secret = os.environ.get("SPOTIPY_CLIENT_SECRET") or os.environ.get("SPOTIFY_CLIENT_SECRET")
        redirect_uri = os.environ.get("SPOTIPY_REDIRECT_URI") or os.environ.get("SPOTIFY_REDIRECT_URI") or "http://127.0.0.1:8888/callback"

        if client_id and client_secret:
            try:
                auth_manager = SpotifyOAuth(
                    client_id=client_id,
                    client_secret=client_secret,
                    redirect_uri=redirect_uri,
                    scope="user-modify-playback-state user-read-playback-state playlist-modify-public playlist-modify-private playlist-read-private",
                    open_browser=False
                )
                self.sp = spotipy.Spotify(auth_manager=auth_manager)
                print("✓ Spotify Web API initialized successfully")
            except Exception as e:
                print(f"⚠️ Spotify Web API setup error: {e}. Will fallback to desktop controls.")
                self.sp = None
        else:
            print("ℹ Spotify API credentials not set in environment. Desktop controls active.")

    def _init_local_playlists(self):
        """Initialize local playlist JSON storage for fallback"""
        try:
            self.playlists_file.parent.mkdir(parents=True, exist_ok=True)
            if not self.playlists_file.exists():
                with open(self.playlists_file, 'w') as f:
                    json.dump({"playlists": {}}, f, indent=2)
        except Exception as e:
            print(f"Local playlist init error: {e}")

    def _load_local_playlists(self) -> Dict[str, List[str]]:
        try:
            if self.playlists_file.exists():
                with open(self.playlists_file, 'r') as f:
                    data = json.load(f)
                    return data.get("playlists", {})
        except Exception:
            pass
        return {}

    def _save_local_playlists(self, playlists: Dict[str, List[str]]):
        try:
            with open(self.playlists_file, 'w') as f:
                json.dump({"playlists": playlists}, f, indent=2)
        except Exception as e:
            print(f"Error saving local playlists: {e}")

    def _run_mpris_cmd(self, action: str) -> bool:
        """Run DBus or playerctl command for Spotify playback control"""
        playerctl_actions = {
            "next": "next",
            "previous": "previous",
            "pause": "pause",
            "resume": "play",
            "play_pause": "play-pause"
        }
        if action in playerctl_actions:
            try:
                res = subprocess.run(
                    ["playerctl", "--player=spotify", playerctl_actions[action]],
                    capture_output=True, text=True, timeout=3
                )
                if res.returncode == 0:
                    return True
            except Exception:
                pass

        dbus_methods = {
            "next": "Next",
            "previous": "Previous",
            "pause": "Pause",
            "resume": "Play",
            "play_pause": "PlayPause"
        }
        if action in dbus_methods:
            method = dbus_methods[action]
            try:
                res = subprocess.run([
                    "dbus-send", "--print-reply", "--dest=org.mpris.MediaPlayer2.spotify",
                    "/org/mpris/MediaPlayer2", f"org.mpris.MediaPlayer2.Player.{method}"
                ], capture_output=True, text=True, timeout=3)
                if res.returncode == 0:
                    return True
            except Exception:
                pass
        return False

    def play_song(self, song_name: str) -> Tuple[bool, str]:
        """
        Search and play a song by name.
        """
        if not song_name or not song_name.strip():
            return False, "Please specify a song name to play."

        clean_song = song_name.strip()

        # 1. Try Spotify Web API if initialized
        if self.sp:
            try:
                results = self.sp.search(q=clean_song, limit=1, type='track')
                tracks = results.get('tracks', {}).get('items', [])
                if tracks:
                    track = tracks[0]
                    track_uri = track['uri']
                    title = track['name']
                    artist = track['artists'][0]['name'] if track['artists'] else ""
                    display_name = f"'{title}' by {artist}" if artist else f"'{title}'"

                    try:
                        self.sp.start_playback(uris=[track_uri])
                        return True, f"Playing {display_name} on Spotify"
                    except Exception:
                        pass
                    
                    subprocess.Popen(["xdg-open", track_uri], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                    return True, f"Playing {display_name} on Spotify"
            except Exception as e:
                print(f"Spotify API search failed: {e}")

        # 2. Desktop fallback: open Spotify search URI or desktop URI
        encoded_query = urllib.parse.quote(clean_song)
        spotify_uri = f"spotify:search:{encoded_query}"
        
        try:
            subprocess.Popen(["xdg-open", spotify_uri], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            return True, f"Searching and playing {clean_song} on Spotify"
        except Exception:
            try:
                web_url = f"https://open.spotify.com/search/{encoded_query}"
                subprocess.Popen(["xdg-open", web_url], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                return True, f"Opening {clean_song} on Spotify Web"
            except Exception as e:
                return False, f"Could not play song on Spotify: {e}"

    def change_track(self, action: str) -> Tuple[bool, str]:
        """
        Change track or playback state (next, previous, pause, resume)
        """
        action = action.lower().strip()
        
        if self.sp:
            try:
                if action == "next":
                    self.sp.next_track()
                    return True, "Skipped to next track"
                elif action == "previous":
                    self.sp.previous_track()
                    return True, "Playing previous track"
                elif action == "pause":
                    self.sp.pause_playback()
                    return True, "Paused Spotify"
                elif action == "resume":
                    self.sp.start_playback()
                    return True, "Resumed Spotify playback"
            except Exception as e:
                print(f"Spotify API track control error: {e}")

        mpris_success = self._run_mpris_cmd(action)
        if mpris_success:
            messages = {
                "next": "Skipped to next track",
                "previous": "Playing previous track",
                "pause": "Paused Spotify",
                "resume": "Resumed Spotify playback"
            }
            return True, messages.get(action, f"Executed Spotify {action}")

        action_names = {
            "next": "skip to next track",
            "previous": "play previous track",
            "pause": "pause Spotify",
            "resume": "resume Spotify"
        }
        return False, f"Could not {action_names.get(action, action)}. Is Spotify running?"

    def create_playlist(self, playlist_name: str) -> Tuple[bool, str]:
        """
        Create a new playlist by name
        """
        if not playlist_name or not playlist_name.strip():
            return False, "Please specify a name for the new playlist."

        clean_name = playlist_name.strip().title()

        if self.sp:
            try:
                user_id = self.sp.current_user()['id']
                created = self.sp.user_playlist_create(
                    user=user_id,
                    name=clean_name,
                    public=True,
                    description="Created by Jean Max Voice Assistant"
                )
                return True, f"Successfully created new Spotify playlist '{clean_name}'"
            except Exception as e:
                print(f"Spotify API create playlist failed: {e}")

        playlists = self._load_local_playlists()
        if clean_name in playlists:
            return True, f"Playlist '{clean_name}' already exists."
        
        playlists[clean_name] = []
        self._save_local_playlists(playlists)
        return True, f"Created playlist '{clean_name}'"

    def add_to_playlist(self, song_name: str, playlist_name: str) -> Tuple[bool, str]:
        """
        Add a song to a specific playlist
        """
        if not song_name or not playlist_name:
            return False, "Please specify both the song name and playlist name."

        clean_song = song_name.strip()
        clean_playlist = playlist_name.strip().title()

        if self.sp:
            try:
                results = self.sp.search(q=clean_song, limit=1, type='track')
                tracks = results.get('tracks', {}).get('items', [])
                if not tracks:
                    return False, f"Could not find track '{clean_song}' on Spotify."

                track = tracks[0]
                track_uri = track['uri']
                track_title = track['name']

                user_playlists = self.sp.current_user_playlists()
                target_playlist_id = None

                for item in user_playlists.get('items', []):
                    if item['name'].lower() == clean_playlist.lower():
                        target_playlist_id = item['id']
                        break

                if not target_playlist_id:
                    user_id = self.sp.current_user()['id']
                    new_pl = self.sp.user_playlist_create(
                        user=user_id,
                        name=clean_playlist,
                        public=True,
                        description="Created by Jean Max Voice Assistant"
                    )
                    target_playlist_id = new_pl['id']

                self.sp.playlist_add_items(target_playlist_id, [track_uri])
                return True, f"Added '{track_title}' to playlist '{clean_playlist}' on Spotify"

            except Exception as e:
                print(f"Spotify API add_to_playlist error: {e}")

        playlists = self._load_local_playlists()
        if clean_playlist not in playlists:
            playlists[clean_playlist] = []

        playlists[clean_playlist].append(clean_song)
        self._save_local_playlists(playlists)
        return True, f"Added '{clean_song}' to playlist '{clean_playlist}'"
