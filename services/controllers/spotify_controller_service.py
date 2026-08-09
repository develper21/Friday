"""
Spotify Controller Service Implementation
Implements ISpotifyController interface using existing SpotifyController
"""

from typing import Tuple
from core.interfaces.controller_service import ISpotifyController
from assistance.controllers.spotify_controller import SpotifyController


class SpotifyControllerService(ISpotifyController):
    """Spotify controller service implementation"""
    
    def __init__(self):
        self.spotify_controller = SpotifyController()
    
    def play_song(self, song_name: str) -> Tuple[bool, str]:
        """Play song on Spotify"""
        return self.spotify_controller.play_song(song_name)
    
    def add_to_playlist(self, song: str, playlist: str) -> Tuple[bool, str]:
        """Add song to playlist"""
        return self.spotify_controller.add_to_playlist(song, playlist)
    
    def create_playlist(self, playlist_name: str) -> Tuple[bool, str]:
        """Create new playlist"""
        return self.spotify_controller.create_playlist(playlist_name)
    
    def change_track(self, action: str) -> Tuple[bool, str]:
        """Change track (next/previous/pause/resume)"""
        return self.spotify_controller.change_track(action)
