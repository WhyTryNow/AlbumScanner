"""
Album Scanner by Jess Casaus
Scans music folders for incomplete albums and fetches missing track info from Spotify.
"""
import os
import json
from datetime import datetime
from collections import defaultdict
import mutagen
from mutagen import File
import spotipy
from spotipy.oauth2 import SpotifyClientCredentials
import tkinter as tk
from tkinter import filedialog, messagebox
from cryptography.fernet import Fernet

class CredentialManager:
    # Handles secure storage and retrieval of Spotify credentials.
    def __init__(self, key_file="scanner_key.key", cred_file="credentials.enc"):
        self.key_file = key_file
        self.cred_file = cred_file
        self.key = self._get_or_create_key()
        self.cipher = Fernet(self.key)

    def _get_or_create_key(self):
        if os.path.exists(self.key_file):
            with open(self.key_file, 'rb') as f:
                return f.read()
        else:
            key = Fernet.generate_key()
            with open(self.key_file, 'wb') as f:
                f.write(key)
            return key

    def save_credentials(self, client_id, client_secret):
        data = {"client_id": client_id, "client_secret": client_secret}
        json_data = json.dumps(data).encode('utf-8')
        encrypted_data = self.cipher.encrypt(json_data)
        
        with open(self.cred_file, 'wb') as f:
            f.write(encrypted_data)

    def load_credentials(self):
        if not os.path.exists(self.cred_file):
            return "", ""
        try:
            with open(self.cred_file, 'rb') as f:
                encrypted_data = f.read()
            decrypted_data = self.cipher.decrypt(encrypted_data)
            data = json.loads(decrypted_data.decode('utf-8'))
            return data.get("client_id", ""), data.get("client_secret", "")
        except Exception as e:
            print(f"Failed to decrypt credentials: {e}")
            return "", ""

def extract_metadata(filepath):
    # Safely extracts artist, album, track number, and total tracks using Mutagen.
    try:
        f = File(filepath, easy=True)
        if f is None:
            f = File(filepath)
        if f is None:
            return None, None, 0, 0
            
        artist = f.get('artist', ['Unknown Artist'])[0]
        album = f.get('album', ['Unknown Album'])[0]
        
        track_num = 0
        total_tracks = 0
        
        track_field = f.get('tracknumber', f.get('trkn', []))
        
        if track_field:
            if isinstance(track_field[0], tuple): 
                track_num = track_field[0][0]
                total_tracks = track_field[0][1] if len(track_field[0]) > 1 else 0
            else: 
                track_str = str(track_field[0])
                if '/' in track_str:
                    parts = track_str.split('/')
                    track_num = int(parts[0]) if parts[0].isdigit() else 0
                    total_tracks = int(parts[1]) if parts[1].isdigit() else 0
                else:
                    track_num = int(track_str) if track_str.isdigit() else 0
        
        return str(artist), str(album), track_num, total_tracks
    except Exception:
        return None, None, 0, 0

def get_spotify_album_metadata(sp, artist, album, missing_indices):
    # Fetches missing track names from Spotify.
    default_res = ("Could not automatically locate Spotify link", [])
    if not sp:
        return "Spotify Connection Disabled", []
        
    try:
        query = f"artist:{artist} album:{album}"
        results = sp.search(q=query, type='album', limit=1)
        items = results.get('albums', {}).get('items', [])
        
        if not items:
            return default_res
            
        album_data = items[0]
        spotify_url = album_data['external_urls']['spotify']
        album_id = album_data['id']
        
        missing_song_names = []
        found_indices = set()
        
        tracks_response = sp.album_tracks(album_id, limit=50)
        tracks = tracks_response.get('items', [])
        
        for track in tracks:
            track_num = track.get('track_number')
            if track_num in missing_indices:
                track_name = str(track.get('name', f"Track {track_num}"))
                missing_song_names.append(track_name)
                found_indices.add(track_num)
                
        # Fill in generic names for any tracks Spotify missed
        for track_num in missing_indices:
            if track_num not in found_indices:
                missing_song_names.append(f"Track {track_num}")
                
        return spotify_url, missing_song_names
        
    except spotipy.SpotifyException as e:
        print(f"Spotify API error: {e}")
        return default_res
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
        return default_res

def check_album_completeness(music_folder, min_track_threshold=3):
    # Scans local directories and finds albums with missing track numbers.
    album_data = defaultdict(lambda: {'tracks': set(), 'total_meta': 0})

    for root, dirs, files in os.walk(music_folder):
        for f in files:
            if f.lower().endswith(('.flac', '.mp3', '.m4a', '.wav')):
                filepath = os.path.join(root, f)
                artist, album, track_num, total_tracks = extract_metadata(filepath)
                
                if artist and album and track_num > 0:
                    key = (artist, album)
                    album_data[key]['tracks'].add(track_num)
                    if total_tracks > album_data[key]['total_meta']:
                        album_data[key]['total_meta'] = total_tracks

    incomplete_albums = []
    
    for (artist, album), data in album_data.items():
        present_tracks = data['tracks']
        
        # SKIP if we don't meet the minimum track threshold (avoids flagging singles/EPs)
        if len(present_tracks) < min_track_threshold:
            continue
            
        max_present = max(present_tracks)
        expected_total = max(max_present, data['total_meta'])
        
        expected_set = set(range(1, expected_total + 1))
        missing = sorted(list(expected_set - present_tracks))
        
        if missing:
            incomplete_albums.append({
                "artist": artist,
                "album": album,
                "missing_indices": missing,
                "missing_count": len(missing),
                "amount_present": len(present_tracks),
                "total_tracks": expected_total
            })
                
    return incomplete_albums

class AlbumScannerApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Album Scanner")
        self.root.geometry("700x750")
        
        self.cred_manager = CredentialManager()
        saved_id, saved_secret = self.cred_manager.load_credentials()
        
        self.music_folder_path = tk.StringVar()
        self.spotify_id = tk.StringVar(value=saved_id)
        self.spotify_secret = tk.StringVar(value=saved_secret)
        self.min_tracks_var = tk.IntVar(value=3)
        
        self.setup_ui()
    
    def setup_ui(self):
        title_frame = tk.Frame(self.root)
        title_frame.pack(pady=10)
        tk.Label(title_frame, text="🎵 Album Scanner", font=("Helvetica", 18, "bold")).pack()
        tk.Label(title_frame, text="Find incomplete albums in your music collection.").pack()
        
        settings_frame = tk.Frame(self.root)
        settings_frame.pack(pady=10, fill=tk.X, padx=20)
        
        tk.Label(settings_frame, text="Spotify Client ID:").grid(row=0, column=0, sticky=tk.W, pady=2)
        tk.Entry(settings_frame, textvariable=self.spotify_id, width=45, show="*").grid(row=0, column=1, padx=5, pady=2)
        
        tk.Label(settings_frame, text="Spotify Client Secret:").grid(row=1, column=0, sticky=tk.W, pady=2)
        tk.Entry(settings_frame, textvariable=self.spotify_secret, width=45, show="*").grid(row=1, column=1, padx=5, pady=2)
        
        tk.Button(settings_frame, text="💾 Save Credentials", command=self.save_creds_to_file).grid(row=0, column=2, rowspan=2, padx=5, pady=2)
        
        # Added setting for singles threshold
        tk.Label(settings_frame, text="Minimum Tracks (Ignore Singles):").grid(row=2, column=0, sticky=tk.W, pady=15)
        tk.Entry(settings_frame, textvariable=self.min_tracks_var, width=10).grid(row=2, column=1, sticky=tk.W, padx=5, pady=15)
        
        tk.Label(settings_frame, text="Select Music Folder:").grid(row=3, column=0, sticky=tk.W, pady=5)
        tk.Entry(settings_frame, textvariable=self.music_folder_path, width=45).grid(row=3, column=1, padx=5, pady=5)
        tk.Button(settings_frame, text="Browse", command=self.browse_music_folder).grid(row=3, column=2, padx=5, pady=5)
        
        scan_frame = tk.Frame(self.root)
        scan_frame.pack(pady=5)
        tk.Button(scan_frame, text="🔍 Scan Albums", command=self.scan_albums, bg="#4CAF50", fg="white", font=("Helvetica", 10, "bold")).pack()
        
        self.result_text = tk.Text(self.root, height=22, width=82, font=("Consolas", 10))
        self.result_text.pack(pady=10)
        
        self.status_var = tk.StringVar(value="Ready")
        status_bar = tk.Label(self.root, textvariable=self.status_var, bd=1, relief=tk.SUNKEN, anchor=tk.W)
        status_bar.pack(fill=tk.X, side=tk.BOTTOM)
        
    def save_creds_to_file(self):
        c_id = self.spotify_id.get().strip()
        c_secret = self.spotify_secret.get().strip()
        
        if c_id and c_secret:
            self.cred_manager.save_credentials(c_id, c_secret)
            messagebox.showinfo("Success", "Credentials encrypted and saved locally.")
            self.status_var.set("✅ Credentials saved securely.")
        else:
            messagebox.showwarning("Warning", "Please enter both a Client ID and Client Secret to save.")
            
    def browse_music_folder(self):
        folder_path = filedialog.askdirectory()
        if folder_path:
            self.music_folder_path.set(folder_path)
            self.status_var.set(f"✅ Folder set to: {folder_path}")
    
    def scan_albums(self):
        music_folder = self.music_folder_path.get()
        if not music_folder:
            messagebox.showerror("Error", "Please select a Music folder.")
            return

        try:
            min_thresh = self.min_tracks_var.get()
        except ValueError:
            min_thresh = 3

        sp = None
        client_id = self.spotify_id.get().strip()
        client_secret = self.spotify_secret.get().strip()
        
        if client_id and client_secret:
            try:
                auth_manager = SpotifyClientCredentials(client_id=client_id, client_secret=client_secret)
                sp = spotipy.Spotify(auth_manager=auth_manager, requests_timeout=10, retries=3)
                sp.search(q="test", limit=1)
                self.status_var.set("✅ Spotify Connected. Scanning albums...")
            except Exception as e:
                messagebox.showwarning("Spotify Error", f"Failed to connect to Spotify. Continuing with local data only.\nError: {e}")
                self.status_var.set("⚠️ Spotify Failed. Scanning local albums...")
                sp = None
        else:
            self.status_var.set("🔄 Scanning local albums (Spotify disabled)...")
            
        self.root.update()

        try:
            incomplete_albums = check_album_completeness(music_folder, min_track_threshold=min_thresh)
            
            if not incomplete_albums:
                results_text = "✅ All albums are complete (or fall below the singles threshold)!\n\n"
                results_text += "=" * 50 + "\n\n"
                results_text += f"No missing tracks found in {music_folder}\n"
                results_text += f"Your collection is perfectly organized! 🎉\n"
            else:
                results_text = "📊 Album Scan Results\n"
                results_text += "=" * 50 + "\n\n"
                
                sorted_albums = sorted(incomplete_albums, key=lambda x: (x['artist'], x['album']))
                total_albums = len(sorted_albums)
                
                for index, album in enumerate(sorted_albums):
                    self.status_var.set(f"🔍 Fetching Spotify Data ({index + 1}/{total_albums}): {album['artist']}")
                    self.root.update()
                    
                    spotify_url, missing_names = get_spotify_album_metadata(
                        sp, 
                        album['artist'], 
                        album['album'], 
                        album['missing_indices']
                    )
                    
                    if len(missing_names) != album['missing_count'] and album.get('missing_count', 0) < len(missing_names):
                        missing_names = missing_names[:album.get('missing_count', len(missing_names))]
                        
                    names_str = ", ".join(str(n) for n in missing_names) if missing_names else \
                               ", ".join([f"Track {x}" for x in album['missing_indices']])
                               
                    results_text += f"🎤 {album['artist']}\n"
                    results_text += "-" * len(album['artist']) + "--------\n\n"
                    results_text += f"   💿 Album: {album['album']}\n"
                    results_text += f"   📀 Total Tracks: {album['total_tracks']}\n"
                    results_text += f"   ✅ Present: {album['amount_present']} | ❌ Missing: {album['missing_count']}\n"
                    results_text += f"   🚫 Missing Tracks: {names_str}\n"
                    
                    if spotify_url != "Spotify Connection Disabled":
                        results_text += f"   🔗 Spotify URL: {spotify_url}\n\n"
                    else:
                        results_text += "\n"
                        
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                output_file = f"scan_results_{timestamp}.txt"
                with open(output_file, "w", encoding="utf-8") as out:
                    out.write(results_text)
                    
                self.status_var.set(f"✅ Scan complete! Results saved to {output_file}")
                
            self.result_text.delete(1.0, tk.END)
            self.result_text.insert(tk.END, results_text)
            
        except Exception as e:
            messagebox.showerror("Error", f"Scan failed:\n{str(e)}")
            self.status_var.set(f"❌ Error: {e}")

if __name__ == "__main__":
    root = tk.Tk()
    app = AlbumScannerApp(root)
    root.mainloop()